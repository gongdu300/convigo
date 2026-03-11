from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple, Dict
import os
import re
import numpy as np

from sentence_transformers import SentenceTransformer, CrossEncoder
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database import Item, SessionLocal

# ─────────────────────────────────────────────────────────────
# Elasticsearch 설정 (환경변수로 오버라이드 가능)
try:
    from elasticsearch import Elasticsearch
except Exception:
    Elasticsearch = None  # 패키지 미설치 시 안전 폴백

ES_HOST = os.getenv("ES_HOST", "http://localhost:9200")
ES_INDEX = os.getenv("ES_INDEX", "items")
BM25_SIZE_DEFAULT = int(os.getenv("ES_BM25_SIZE", "200"))

# ─────────────────────────────────────────────────────────────
# 모델/가중치/파라미터
EMB_MODEL = "intfloat/multilingual-e5-base"            # 문장 임베딩(E5·한글 OK)
RERANK_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"  # 크로스-인코더(가볍고 빠름)

W_EMB = 0.65        # 하이브리드 가중치 (임베딩)
W_TFIDF = 0.35      # 하이브리드 가중치 (TF-IDF)
CAND_MULTIPLIER = 5 # 최종 top_k의 N배를 1차 후보로
ENFORCE_KEYWORD = True  # 이름에 질의 키워드가 실제 포함되도록 강제(AND)
# ─────────────────────────────────────────────────────────────

# 간단 동의어/정규화(필요시 확장)
SYN = {
    "초코": ["초코", "초콜릿", "choco", "초코칩"],
    "1+1": ["1+1", "원플원", "1 플 1", "1플1"],
    "2+1": ["2+1", "투플원", "2플1", "2 플 1", "2플 원"],
    "증정": ["증정", "덤", "사은품"],
}

def _norm_text(s: str) -> str:
    s = (s or "").strip().lower()
    s = re.sub(r"[^\w\s\+\-/%]", " ", s)   # 한/영/숫자와 기본 기호만
    s = re.sub(r"\s+", " ", s)
    return s.strip()

def expand_terms(q: str) -> List[str]:
    qn = _norm_text(q)
    terms = [t for t in re.split(r"\s+", qn) if t]
    expanded: List[str] = []
    for t in terms:
        expanded.extend(SYN.get(t, [t]))
    # 중복 제거 + 순서 유지
    return list(dict.fromkeys(expanded))

def _infer_filters(q: str) -> Dict[str, Optional[str]]:
    qq = q.lower()
    store = None
    if "gs25" in qq or re.search(r"\bgs\b", qq): store = "GS25"
    if re.search(r"\bcu\b", qq): store = "CU"
    if "세븐" in qq or "7-eleven" in qq or "7eleven" in qq: store = "SEVEN"
    promo = None
    if "1+1" in qq or "원플원" in qq: promo = "1+1"
    elif "2+1" in qq or "투플원" in qq or "투플" in qq or "2플1" in qq: promo = "2+1"
    elif "증정" in qq or "사은품" in qq or "덤" in qq: promo = "증정"
    return {"store": store, "promotion_type": promo}

@dataclass
class ItemRow:
    id: int
    store: str
    name: str
    price: int
    image_url: Optional[str]
    promotion_type: Optional[str]

# ─────────────────────────────────────────────────────────────
# ES 유틸
_es_client: Optional["Elasticsearch"] = None

def get_es() -> Optional["Elasticsearch"]:
    global _es_client
    if Elasticsearch is None:
        return None
    if _es_client is None:
        try:
            _es_client = Elasticsearch(ES_HOST)
        except Exception:
            _es_client = None
    return _es_client

def bm25_candidates(query: str,
                    store: Optional[str],
                    promo: Optional[str],
                    size: int = BM25_SIZE_DEFAULT) -> Optional[set[int]]:
    """
    ES BM25로 후보 문서 id 세트를 가져온다.
    - Nori 분석기가 인덱스 매핑에 설정되어 있다고 가정.
    - 실패 시 None 반환(→ 파이프라인은 폴백).
    """
    es = get_es()
    if es is None:
        return None
    must = [{
    "multi_match": {
        "query": query,
        "fields": ["name^3", "promotion_type", "store"],
        "fuzziness": "AUTO"
    }
}]

    flt = []
    if store: flt.append({"term": {"store": store}})
    if promo: flt.append({"term": {"promotion_type": promo}})
    body = {
        "size": size,
        "_source": False,
        "query": {"bool": {"must": must, "filter": flt}} if flt else {"bool": {"must": must}},
    }
    try:
        res = es.search(index=ES_INDEX, body=body)
        hits = res.get("hits", {}).get("hits", [])
        # _id는 문자열일 수 있으므로 int 변환 시도
        out = set()
        for h in hits:
            try:
                out.add(int(h["_id"]))
            except Exception:
                # 혹시 _source에 id가 있으면 사용
                src = h.get("_source") or {}
                vid = src.get("id")
                if isinstance(vid, int):
                    out.add(vid)
        return out
    except Exception:
        return None

# ─────────────────────────────────────────────────────────────
class VectorIndex:
    """임베딩(E5) + TF-IDF 하이브리드 → (옵션)BM25 후보 → 크로스-인코더 재정렬"""
    def __init__(self):
        self.emb_model = SentenceTransformer(EMB_MODEL)
        self.rerank = CrossEncoder(RERANK_MODEL)
        self.ids: List[int] = []
        self.meta: List[ItemRow] = []
        self.emb: Optional[np.ndarray] = None
        self.tfidf = None
        self.tfidf_mat: Optional[np.ndarray] = None

    def _to_passages(self, rows: Sequence[ItemRow]) -> List[str]:
        out = []
        for r in rows:
            aux = []
            if r.promotion_type: aux.append(r.promotion_type)
            if r.store: aux.append(r.store)
            out.append(_norm_text(" ".join([r.name] + aux)))
        return out

    def build(self, rows: Sequence[ItemRow]):
        texts = self._to_passages(rows)
        if not texts:
            self.ids, self.meta, self.emb, self.tfidf, self.tfidf_mat = [], [], None, None, None
            return

        # 문서 임베딩(E5): "passage: {text}"
        passages = [f"passage: {t}" for t in texts]
        vecs = self.emb_model.encode(passages, convert_to_numpy=True, normalize_embeddings=True)

        # TF-IDF(1~2gram)
        tf = TfidfVectorizer(min_df=1, max_df=0.95, ngram_range=(1, 2))
        tf_mat = tf.fit_transform(texts)

        self.ids = [r.id for r in rows]
        self.meta = list(rows)
        self.emb = vecs
        self.tfidf = tf
        self.tfidf_mat = tf_mat

    def _hybrid_score(self, q: str) -> np.ndarray:
        if self.emb is None or self.tfidf_mat is None:
            return np.zeros((0,), dtype=np.float32)

        qn = _norm_text(q)
        # 질의 임베딩(E5): "query: {text}"
        q_emb = self.emb_model.encode([f"query: {qn}"], convert_to_numpy=True, normalize_embeddings=True)
        emb_scores = cosine_similarity(q_emb, self.emb)[0]

        q_tfidf = self.tfidf.transform([qn])
        tfidf_scores = cosine_similarity(q_tfidf, self.tfidf_mat)[0]

        return W_EMB * emb_scores + W_TFIDF * tfidf_scores

    def search(self, q: str, top_k: int = 20,
               store: Optional[str] = None,
               promo: Optional[str] = None) -> List[Tuple[ItemRow, float]]:
        if self.emb is None:
            return []

        # ── (옵션) 0단계: BM25 후보 뽑기 ─────────────────────────────
        bm25_ids = bm25_candidates(q, store, promo, size=max(BM25_SIZE_DEFAULT, top_k * CAND_MULTIPLIER))
        use_bm25 = bm25_ids is not None and len(bm25_ids) > 0

        # 1) 하이브리드 스코어로 넓게 후보 추출
        scores = self._hybrid_score(q)

        if use_bm25:
            # BM25 id 세트에 포함된 것만 대상으로 정렬/후보 선정
            cand_idx_all = [i for i in np.argsort(-scores) if self.meta[i].id in bm25_ids]
        else:
            #ES 실패/후보 없음 → 기존 방식
            cand_idx_all = list(np.argsort(-scores))

        cand_k = min(len(cand_idx_all), max(top_k * CAND_MULTIPLIER, top_k))
        idxs = cand_idx_all[:cand_k]

        # 키워드 하드필터: 이름에 핵심 용어 포함하도록 (AND)
        terms = expand_terms(q) if ENFORCE_KEYWORD else []

        candidates: List[Tuple[ItemRow, float]] = []
        for i in idxs:
            r = self.meta[i]
            if store and r.store != store: continue
            if promo and (r.promotion_type or "") != promo: continue
            if ENFORCE_KEYWORD and terms:
                nm = _norm_text(r.name)
                need = terms[:2] if len(terms) >= 2 else terms
                # OR 조건: 하나라도 매칭되면 통과
                ok = any(any(tt in nm for tt in SYN.get(t, [t])) for t in need)
                if not ok:
                    continue

            candidates.append((r, float(scores[i])))

        if not candidates:
            return []

        # 2) 크로스-인코더 재정렬(질의-문서 쌍)
        qn = _norm_text(q)
        pairs = [(f"query: {qn}", f"passage: {_norm_text(r.name)}") for (r, _) in candidates]
        rerank_scores = self.rerank.predict(pairs)  # ndarray (len(candidates),)

        order = np.argsort(-np.array(rerank_scores))
        out: List[Tuple[ItemRow, float]] = []
        for j in order[:top_k]:
            r, _ = candidates[j]
            out.append((r, float(rerank_scores[j])))
        return out

# ─────────────────────────────────────────────────────────────
# [수정됨] 싱글톤/유틸 수정
# ─────────────────────────────────────────────────────────────

def _fetch_all_items(db: Session,
                     store: Optional[str]=None,
                     promo: Optional[str]=None) -> List[ItemRow]:
    stmt = select(Item)
    if store: stmt = stmt.where(Item.store == store)
    if promo: stmt = stmt.where(Item.promotion_type == promo)
    rows = db.execute(stmt).scalars().all()
    return [ItemRow(
        id=r.id, store=r.store, name=r.name, price=r.price,
        image_url=r.image_url, promotion_type=r.promotion_type
    ) for r in rows]

# [수정됨] B. 서버 시작 시점(모듈 임포트 시점)에 인덱스를 즉시 생성하고 데이터를 로드합니다.
#    이 코드는 Python이 이 파일을 임포트할 때 '단 한 번' 실행됩니다.
#    (FastAPI 워커 스레드가 아닌, 메인 스레드에서 실행됩니다)
print("Initializing VectorIndex (Eager Loading)...")
_index: VectorIndex = VectorIndex() # 1. 모델 로드 (SentenceTransformer, CrossEncoder)
try:
    db = SessionLocal()
    items = _fetch_all_items(db)
    _index.build(items) # 2. 데이터 빌드
    print(f"VectorIndex initialized with {len(items)} items.")
except Exception as e:
    print(f"CRITICAL: Failed to initialize VectorIndex on startup: {e}")
    # _index가 비어있을 수 있지만, 최소한 _index 객체는 존재함
finally:
    db.close()


def get_index() -> VectorIndex:
    global _index
    # [수정됨] C. _index is None 체크를 제거합니다.
    #    _index는 모듈 로드 시점에 이미 생성되었어야 합니다.
    if _index is None:
         # 이 오류가 발생하면, 위 로직에 심각한 문제가 있는 것임
         raise RuntimeError("VectorIndex was not initialized at module load time.")
    return _index


def refresh_index() -> int:
    db = SessionLocal()
    try:
        items = _fetch_all_items(db)
        # [수정됨] D. get_index() 대신 _index.build()를 직접 호출합니다.
        #    순환 호출을 방지하고, 이미 생성된 _index를 사용합니다.
        _index.build(items)
        print(f"VectorIndex refreshed with {len(items)} items.")
        return len(items)
    finally:
        db.close()

def _keyword_fallback(db: Session, q: str,
                      store: Optional[str],
                      promo: Optional[str],
                      limit: int) -> List[ItemRow]:
    # 필요시 사용할 수 있도록 남겨둠(현재는 재정렬이 있어서 사용 X)
    terms = [t for t in re.split(r"\s+", _norm_text(q)) if t]
    stmt = select(Item)
    if store: stmt = stmt.where(Item.store == store)
    if promo: stmt = stmt.where(Item.promotion_type == promo)
    for t in terms:
        stmt = stmt.where(Item.name.ilike(f"%{t}%"))
    stmt = stmt.limit(limit)
    rows = db.execute(stmt).scalars().all()
    return [ItemRow(
        id=r.id, store=r.store, name=r.name, price=r.price,
        image_url=r.image_url, promotion_type=r.promotion_type
    ) for r in rows]

def smart_query(q: str, top_k: int = 20) -> Dict:
    hints = _infer_filters(q)
    hits = get_index().search(q, top_k=top_k,
                              store=hints["store"],
                              promo=hints["promotion_type"])
    items = [{
        "id": r.id, "store": r.store, "name": r.name, "price": r.price,
        "image_url": r.image_url, "promotion_type": r.promotion_type, "score": sc
    } for r, sc in hits]
    return {"q": q, "hints": hints, "count": len(items), "items": items}

def similar_items(item_id: int, top_k: int = 12):
    idx = get_index()
    target = next((r for r in idx.meta if r.id == item_id), None)
    if not target:
        return []
    res = idx.search(target.name, top_k=top_k+1, store=target.store, promo=target.promotion_type)
    out = []
    for r, sc in res:
        if r.id == item_id: continue
        out.append({
            "id": r.id, "store": r.store, "name": r.name, "price": r.price,
            "image_url": r.image_url, "promotion_type": r.promotion_type, "score": sc
        })
        if len(out) >= top_k: break
    return out
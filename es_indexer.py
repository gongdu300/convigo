# es_indexer.py
# DB(Item) -> Elasticsearch(index=items) 동기화 스크립트
# 사용 예:
#   python es_indexer.py --recreate        # 인덱스 재생성(+매핑) 후 전체 색인
#   python es_indexer.py                   # 인덱스 유지한 채 전체 upsert
#   python es_indexer.py --batch 2000      # 배치 크기 조절
#   python es_indexer.py --es http://127.0.0.1:9200 --index items

from __future__ import annotations
import argparse
from typing import Iterable, Dict, Any, Generator

from elasticsearch import Elasticsearch, helpers

# 프로젝트의 DB 모델 가져옴 (이미 존재)
from backend.database import SessionLocal, Item

# ──────────────────────────────────────────────────────────────────────────
# 매핑 & 세팅 (Nori 형태소 분석기)
MAPPING_BODY: Dict[str, Any] = {
    "settings": {
        "analysis": {
            "analyzer": {
                "nori_analyzer": {
                    "type": "custom",
                    "tokenizer": "nori_tokenizer"
                }
            }
        }
    },
    "mappings": {
        "properties": {
            "id": {"type": "integer"},
            "store": {"type": "keyword"},
            "promotion_type": {"type": "keyword"},
            "name": {"type": "text", "analyzer": "nori_analyzer"},
            "price": {"type": "integer"},
            "image_url": {"type": "keyword"}
        }
    }
}

def ensure_index(es: Elasticsearch, index: str, recreate: bool = False):
    """인덱스 재생성(옵션) 또는 존재 확인 후 생성."""
    if recreate and es.indices.exists(index=index):
        es.indices.delete(index=index, ignore=[404])
    es.indices.create(index=index, body=MAPPING_BODY, ignore=400)

# ──────────────────────────────────────────────────────────────────────────
def iter_rows(batch: int) -> Generator[list[Item], None, None]:
    """DB에서 items를 배치 단위로 yield."""
    db = SessionLocal()
    try:
        last_id = 0
        while True:
            rows = (
                db.query(Item)
                .filter(Item.id > last_id)
                .order_by(Item.id.asc())
                .limit(batch)
                .all()
            )
            if not rows:
                break
            yield rows
            last_id = rows[-1].id
    finally:
        db.close()

def to_doc(it: Item) -> Dict[str, Any]:
    """ES 문서 스키마로 변환 (매핑 필드만 보냄)."""
    return {
        "id": it.id,
        "store": it.store,
        "promotion_type": it.promotion_type,
        "name": it.name,
        "price": int(it.price) if it.price is not None else 0,
        "image_url": it.image_url or "",
    }

def bulk_index(es: Elasticsearch, index: str, batch: int = 1000):
    """helpers.bulk 로 upsert."""
    total = 0
    for rows in iter_rows(batch):
        actions = []
        for it in rows:
            doc = to_doc(it)
            actions.append({
                "_op_type": "index",  # upsert 목적이면 'index'가 간단/빠름
                "_index": index,
                "_id": it.id,
                "_source": doc,
            })
        helpers.bulk(es, actions, request_timeout=60)
        total += len(rows)
        print(f"  + indexed {total} docs ...")
    print(f"✅ Done. total indexed: {total}")

# ──────────────────────────────────────────────────────────────────────────
def main():
    p = argparse.ArgumentParser(description="Sync DB items -> Elasticsearch")
    p.add_argument("--es", default="http://localhost:9200", help="Elasticsearch URL")
    p.add_argument("--index", default="items", help="Elasticsearch index name")
    p.add_argument("--batch", type=int, default=1000, help="Batch size")
    p.add_argument("--recreate", action="store_true",
                   help="Drop & create index with mapping before indexing")
    args = p.parse_args()

    es = Elasticsearch(args.es)
    # 인덱스 준비
    ensure_index(es, args.index, recreate=args.recreate)
    # 색인
    bulk_index(es, args.index, batch=args.batch)

if __name__ == "__main__":
    main()

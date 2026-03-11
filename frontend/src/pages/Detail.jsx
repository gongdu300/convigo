import { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams, useLocation } from "react-router-dom";
import { ChevronLeft, Bookmark, ExternalLink } from "lucide-react";
import { productAPI, bookmarkAPI, aiAPI } from "../services/api";

const IMG_FALLBACK = "/images/placeholder.jpg";

/* ===== 파싱/계산 유틸 (이전과 동일) ===== */
const parseWeight = (name = "") => {
  const s = String(name).toLowerCase();
  let m = s.match(/(\d{2,5})\s*ml/);
  if (m) return { value: Number(m[1]), unit: "ml" };
  m = s.match(/(\d{2,5})\s*g/);
  if (m) return { value: Number(m[1]), unit: "g" };
  return null;
};

const extractTags = (name = "") => {
  const s = String(name).toLowerCase();
  const dict = [
    ["닭가슴살", /(닭가슴살|치킨브레스트)/],
    ["스테이크", /(스테이크|스택)/],
    ["오리지널", /(오리지널|오리진|original)/],
    ["매운맛", /(매운|핫|고추|스파이시)/],
    ["저당", /(저당|무가당|당줄임)/],
    ["고단백", /(단백|프로틴|protein)/],
    ["저칼로리", /(저칼로리|라이트|light)/],
    ["샐러드", /(샐러드|salad)/],
  ];
  const tags = [];
  for (const [label, rx] of dict) if (rx.test(s)) tags.push(label);
  const w = parseWeight(name);
  if (w) tags.push(`${w.value}${w.unit}`);
  return Array.from(new Set(tags));
};

const unitPrice = (price, weight) => {
  const p = Number(price);
  if (!Number.isFinite(p) || !weight) return null;
  const base = weight.unit === "ml" ? 100 : 100;
  return Math.round((p / weight.value) * base);
};

const brandKo = (store) => {
  const s = (store || "").toUpperCase();
  if (s === "GS25") return "GS25";
  if (s === "CU") return "CU";
  if (s.includes("SEVEN") || s === "7" || s === "7-ELEVEN") return "세븐일레븐";
  return store || "-";
};


export default function Detail() {
  const { id } = useParams();
  const location = useLocation();
  const nav = useNavigate();

  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState(null);
  const [product, setProduct] = useState(null);

  const [bookmarked, setBookmarked] = useState(false);
  const [similar, setSimilar] = useState([]);

  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        setLoading(true);
        setErr(null);

        const detail = await productAPI.getProductDetail(id);
        if (!mounted) return;
        setProduct(detail || null);

        try {
          const bm = await bookmarkAPI.checkBookmark(id);
          if (mounted) setBookmarked(!!bm?.bookmarked);
        } catch {}

        try {
          const sim = await aiAPI.similar(id, {
            top_k: 8,
            fallbackName: detail?.name,
            store: detail?.store,
            promotionType: detail?.promotionType,
          });
          const items = Array.isArray(sim?.items) ? sim.items : [];
          if (mounted) setSimilar(items.slice(0, 8));
        } catch {}
      } catch (e) {
        setErr(e?.message || "상세 정보를 불러오지 못했어요.");
      } finally {
        if (mounted) setLoading(false);
      }
    })();
    return () => {
      mounted = false;
    };
  }, [id, location.key]);

  const imgSrc = product?.image_url || product?.item_img_src || product?.img || IMG_FALLBACK;
  const weight = useMemo(() => parseWeight(product?.name ?? ""), [product]);
  const uPrice = useMemo(() => unitPrice(product?.price, weight), [product, weight]);
  const tags = useMemo(() => extractTags(product?.name ?? ""), [product]);

  const priceText = useMemo(() => {
    const n = Number(product?.price);
    return Number.isFinite(n) ? `${n.toLocaleString()}원` : "-";
  }, [product]);

  const promoText = useMemo(() => product?.promotionType || "-", [product]);

  const toggleBookmark = async () => {
    try {
      const next = !bookmarked;
      setBookmarked(next);
      await bookmarkAPI.toggleBookmark?.(id, next);
      if (!bookmarkAPI.toggleBookmark) {
        if (next) await bookmarkAPI.addBookmark(id);
        else await bookmarkAPI.removeBookmarkByProduct(id);
      }
    } catch {
      setBookmarked((v) => !v);
    }
  };

  if (loading) {
    // ... 로딩 UI
    return (
      <div className="max-w-4xl mx-auto px-4 py-12">
         <div className="h-8 w-32 bg-gray-200 animate-pulse rounded mb-8" />
         <div className="bg-white border border-gray-200 rounded-lg p-8">
            <div className="grid sm:grid-cols-2 gap-8">
              <div className="w-full h-72 bg-gray-200 animate-pulse rounded-lg"/>
              <div className="space-y-4">
                <div className="h-6 w-1/4 bg-gray-200 animate-pulse rounded" />
                <div className="h-8 w-3/4 bg-gray-200 animate-pulse rounded" />
                <div className="h-12 w-1/2 bg-gray-200 animate-pulse rounded" />
              </div>
            </div>
         </div>
      </div>
    )
  }

  if (err || !product) {
    // ... 에러 UI
    return (
      <div className="max-w-3xl mx-auto px-4 py-12">
        <button onClick={() => nav(-1)} className="inline-flex items-center gap-2 px-3 py-2 border rounded-md hover:bg-gray-50">
          <ChevronLeft className="w-4 h-4" /> 뒤로
        </button>
        <p className="mt-6 text-rose-600">{err || "상품을 찾을 수 없어요."}</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 py-8 sm:py-12">
        {/* 뒤로가기 */}
        <button 
          onClick={() => nav(-1)} 
          className="inline-flex items-center gap-1 text-sm text-gray-600 hover:text-gray-900 mb-6"
        >
          <ChevronLeft className="w-4 h-4" />
          뒤로가기
        </button>

        {/* 메인 컨텐츠 카드 */}
        <div className="bg-white border border-gray-200 rounded-xl shadow-sm overflow-hidden">
          <div className="grid grid-cols-1 sm:grid-cols-2">
            {/* 왼쪽: 이미지 */}
            <div className="p-8 bg-gray-50 flex items-center justify-center">
              <img
                src={imgSrc}
                alt={product.name}
                className="w-full max-w-[280px] aspect-square object-contain"
              />
            </div>

            {/* 오른쪽: 핵심 정보 */}
            <div className="p-8 flex flex-col space-y-5">
              <div className="text-sm font-medium text-gray-500">
                {brandKo(product.store)}
              </div>
              <div className="flex items-start justify-between gap-4">
                <h1 className="text-2xl font-bold text-gray-900 leading-snug">
                  {product.name}
                </h1>
                <button
                  onClick={toggleBookmark}
                  className="flex-shrink-0 p-2 hover:bg-gray-100 rounded-full transition-colors"
                >
                  <Bookmark 
                    className={`w-6 h-6 ${bookmarked ? 'fill-blue-600 text-blue-600' : 'text-gray-400'}`}
                  />
                </button>
              </div>
              <div className="!mt-auto pt-4">
                {promoText !== '-' &&
                  <div className="mb-3">
                    <span className="inline-flex items-center px-3 py-1.5 bg-red-100 text-red-700 text-sm font-bold rounded-full">
                      {promoText}
                    </span>
                  </div>
                }
                <div className="flex items-baseline gap-3">
                  <span className="text-3xl font-bold text-gray-900">
                    {priceText}
                  </span>
                </div>
                {uPrice && (
                  <p className="text-sm text-gray-500 mt-1">
                    100{weight?.unit}당 {uPrice.toLocaleString()}원
                  </p>
                )}
              </div>
            </div>
          </div>
          
          {/* 하단: 태그, 설명, 구매 버튼 */}
          <div className="p-8 border-t border-gray-200 space-y-8">
            {tags.length > 0 && (
              <div>
                <div className="flex flex-wrap gap-2">
                  {tags.map((t) => (
                    <span 
                      key={t} 
                      className="px-3 py-1 bg-gray-100 text-gray-800 text-sm rounded-md"
                    >
                      # {t}
                    </span>
                  ))}
                </div>
              </div>
            )}
            
            {product.summary && (
              <div>
                <h3 className="text-base font-bold text-gray-900 mb-3">상품정보</h3>
                <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-line">
                  {product.summary}
                </p>
              </div>
            )}
            
            {product.source_url && (
              <div>
                <a
                  href={product.source_url}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center justify-center gap-2 w-full px-6 py-4 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-lg transition-colors"
                >
                  구매하러 가기
                  <ExternalLink className="w-5 h-5" />
                </a>
              </div>
            )}
          </div>
        </div>

        {/* 추천 상품 */}
        {similar.length > 0 && (
          <div className="pt-16">
            <h2 className="text-xl font-bold text-gray-900 mb-6">이런 상품은 어떠세요?</h2>
            <div className="relative">
              {/* 가로 스크롤 컨테이너 */}
              <div className="flex space-x-4 overflow-x-auto pb-4 -mb-4 snap-x snap-mandatory">
                {similar.map((item, index) => (
                  <div
                    key={item.id}
                    className={`flex-shrink-0 w-40 sm:w-48 snap-start ${index === 0 ? 'pl-1' : ''}`}
                  >
                    <button
                      onClick={() => nav(`/detail/${item.id}`)}
                      className="group text-left w-full"
                    >
                      <div className="aspect-square bg-white border border-gray-200 rounded-lg overflow-hidden mb-3 transition-shadow group-hover:shadow-lg">
                        <img
                          src={item.image_url || item.img || IMG_FALLBACK}
                          alt={item.name}
                          className="w-full h-full object-contain p-3 transition-transform duration-300 group-hover:scale-105"
                        />
                      </div>
                      <div className="px-1">
                        {/* 상품 이름 (2줄, 고정 높이) */}
                        <p className="text-sm text-gray-700 line-clamp-2 mb-1 h-10 leading-snug">
                          {item.name}
                        </p>
                        {/* 가격 */}
                        <p className="text-base font-bold text-gray-900">
                          {Number(item.price).toLocaleString()}원
                        </p>
                      </div>
                    </button>
                  </div>
                ))}
                {/* 스크롤 영역 확보를 위한 빈 공간 */}
                <div className="flex-shrink-0 w-1 snap-start"></div>
              </div>
              {/* 오른쪽 그라데이션 (스크롤 가능 힌트) */}
              <div className="absolute top-0 right-0 bottom-4 w-20 bg-gradient-to-l from-gray-50 pointer-events-none"></div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
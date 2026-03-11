// src/pages/Home.jsx
import React, { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Search, User, RefreshCw, LogIn, LogOut } from "lucide-react";
import { useAuth } from "../contexts/AuthContext";
import { productAPI } from "../services/api";
import ProductCard from "../components/ProductCard";
import Chatbot from "../pages/Chatbot";
import SimilarDrawer from "../components/SimilarDrawer";

/* ===== 스토어 라벨/정규화 ===== */
const STORE_LABELS = [
  { key: "", label: "전체" },
  { key: "CU", label: "CU" },
  { key: "GS25", label: "GS25" },
  { key: "SEVEN", label: "세븐일레븐" },
];

const normalizeStoreCode = (s = "") => {
  const u = String(s).toUpperCase();
  if (u === "7-ELEVEN" || u === "7ELEVEN") return "SEVEN";
  return u;
};

const equalsStore = (itemStore, selectedKey) => {
  if (!selectedKey) return true; // "전체"
  return normalizeStoreCode(itemStore) === normalizeStoreCode(selectedKey);
};

/* ===== 필터 바 ===== */
function FilterBar({ value, onChange }) {
  const [local, setLocal] = useState(value);

  useEffect(() => {
    setLocal(value);
  }, [value]);

  const setVal = (k, v) => {
    const next = { ...local, [k]: v };
    setLocal(next);
    onChange?.(next);
  };

  const clearPromo = () => {
    const next = { ...local, promotion_type: "", promo: "" };
    setLocal(next);
    onChange?.(next);
  };

  const chip = (label, isActive, onClick) => (
    <button
      type="button"
      onClick={onClick}
      className={`px-3 py-1.5 rounded-full border text-sm ${
        isActive ? "bg-red-500 text-white border-red-500" : "bg-white hover:bg-gray-50"
      }`}
    >
      {label}
    </button>
  );

  return (
    <div className="w-full bg-white border rounded-xl px-3 py-3 shadow-sm">
      <div className="flex flex-wrap items-center gap-3">
        <div className="flex items-center gap-2">
          {chip("전체", !local.promotion_type && !local.promo, clearPromo)}
          {chip("1+1", local.promotion_type === "1+1" || local.promo === "1+1", () =>
            setVal("promotion_type", "1+1")
          )}
          {chip("2+1", local.promotion_type === "2+1" || local.promo === "2+1", () =>
            setVal("promotion_type", "2+1")
          )}
          {chip("증정", local.promotion_type === "증정" || local.promo === "증정", () =>
            setVal("promotion_type", "증정")
          )}
          {chip("할인", local.promotion_type === "할인" || local.promo === "할인", () =>
            setVal("promotion_type", "할인")
          )}
        </div>

        <div className="w-px h-6 bg-gray-200 mx-1" />

        <label className="inline-flex items-center gap-2 text-sm cursor-pointer select-none">
          <input
            type="checkbox"
            checked={!!local.is_new}
            onChange={(e) => setVal("is_new", e.target.checked)}
          />
          신상품만
        </label>

        <div className="w-px h-6 bg-gray-200 mx-1" />

        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-600">가격</span>
          <input
            type="number"
            min="0"
            placeholder="최소"
            value={local.min_price ?? ""}
            onChange={(e) =>
              setVal("min_price", e.target.value === "" ? "" : Number(e.target.value))
            }
            className="w-24 px-2 py-1.5 border rounded-md text-sm"
          />
          <span className="text-gray-400">~</span>
          <input
            type="number"
            min="0"
            placeholder="최대"
            value={local.max_price ?? ""}
            onChange={(e) =>
              setVal("max_price", e.target.value === "" ? "" : Number(e.target.value))
            }
            className="w-24 px-2 py-1.5 border rounded-md text-sm"
          />
        </div>

        <div className="w-px h-6 bg-gray-200 mx-1" />

        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-600">정렬</span>
          <select
            value={local.sort || ""}
            onChange={(e) => setVal("sort", e.target.value)}
            className="px-2 py-1.5 border rounded-md text-sm"
          >
            <option value="">기본</option>
            <option value="newest">최신순</option>
            <option value="price_asc">가격↑</option>
            <option value="price_desc">가격↓</option>
          </select>
        </div>
      </div>
    </div>
  );
}

/* ===== 메인 Home ===== */
export default function Home() {
  const navigate = useNavigate();
  const { user, isAuthenticated, logout } = useAuth();

  const [activeStore, setActiveStore] = useState("");
  const [keyword, setKeyword] = useState("");
  const [page, setPage] = useState(1);
  const pageSize = 20;

  const [filters, setFilters] = useState({
    promo: "",
    promotion_type: "",
    is_new: false,
    min_price: "",
    max_price: "",
    sort: "newest",
  });

  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState(null);
  const [serverTotal, setServerTotal] = useState(undefined);
  const [totalPages, setTotalPages] = useState(1);

  const [drawerOpen, setDrawerOpen] = useState(false);
  const [drawerItemId, setDrawerItemId] = useState(null);

  // 서버 쿼리 파라미터
  const queryParams = useMemo(() => {
    const p = {
      store: activeStore || undefined,
      q: keyword?.trim() ? keyword.trim() : undefined,
      page,
      page_size: pageSize,
    };
    if (filters.promo) p.promo = filters.promo;
    if (filters.promotion_type) {
      p.promotion_type = filters.promotion_type;
      if (!p.promo) p.promo = filters.promotion_type;
    }
    if (filters.is_new) p.is_new = true;
    if (filters.min_price !== "" && filters.min_price != null) p.min_price = filters.min_price;
    if (filters.max_price !== "" && filters.max_price != null) p.max_price = filters.max_price;
    if (filters.sort) p.sort = filters.sort;
    return p;
  }, [activeStore, keyword, page, pageSize, filters]);

  const normalizeItem = (it, idx = 0) => {
    const image = it.image_url ?? it.item_img_src ?? it.img ?? "";
    return {
      id: it.id ?? it.item_id ?? it._id ?? idx,
      name: it.name ?? it.item_name ?? "",
      price: it.price ?? it.item_price ?? "",
      image_url: image,
      item_img_src: image,
      img: image,
      store: it.store ?? it.store_name ?? "",
      promotionType: it.promotion_type ?? it.promo ?? "",
      isNew: Boolean(it.is_new ?? it.isNew ?? false),
    };
  };

  const applyLocalFilters = (list) => {
    let next = Array.isArray(list) ? list : [];

    if (keyword?.trim()) {
      const tokens = keyword
        .trim()
        .split(/\s+/)
        .filter(Boolean)
        .map((s) => s.toLowerCase());
      next = next.filter((it) =>
        tokens.every((t) => String(it.name ?? "").toLowerCase().includes(t))
      );
    }

    if (activeStore) {
      next = next.filter((it) => equalsStore(it.store, activeStore));
    }

    if (filters.promo) {
      const kw = String(filters.promo).toLowerCase();
      next = next.filter((it) => String(it.promotionType ?? "").toLowerCase().includes(kw));
    }
    if (filters.promotion_type) {
      const want = String(filters.promotion_type).toLowerCase();
      next = next.filter((it) => {
        const v = String(it.promotionType ?? "").toLowerCase();
        if (want === "증정") return v.includes("증") || v.includes("덤");
        return v === want;
      });
    }
    if (filters.is_new) next = next.filter((it) => it.isNew);

    if (filters.min_price !== "" && Number.isFinite(Number(filters.min_price))) {
      next = next.filter((it) => Number(it.price) >= Number(filters.min_price));
    }
    if (filters.max_price !== "" && Number.isFinite(Number(filters.max_price))) {
      next = next.filter((it) => Number(it.price) <= Number(filters.max_price));
    }

    if (filters.sort === "price_asc") {
      next = [...next].sort((a, b) => Number(a.price) - Number(b.price));
    } else if (filters.sort === "price_desc") {
      next = [...next].sort((a, b) => Number(b.price) - Number(a.price));
    }

    return next;
  };

  const fetchList = async () => {
    setLoading(true);
    setErr(null);
    try {
      const inSearch = !!keyword?.trim();

      if (inSearch) {
        const data = await productAPI.searchProducts(keyword, { top_k: 100 });
        let arr = [];
        if (Array.isArray(data?.items)) arr = data.items;
        else if (Array.isArray(data?.results)) arr = data.results;
        else if (Array.isArray(data)) arr = data;

        let next = arr.map((it, idx) => normalizeItem(it, idx));
        next = applyLocalFilters(next);

        const baseTotal = next.length;
        const pages = Math.max(1, Math.ceil(baseTotal / pageSize));
        const start = (page - 1) * pageSize;
        const end = start + pageSize;

        setItems(next.slice(start, end));
        setServerTotal(baseTotal);
        setTotal(baseTotal);
        setTotalPages(pages);
        return;
      }

      // 일반 모드: 서버 페이지네이션 사용
      const { items: serverItems, total: t } = await productAPI.getProducts(queryParams);
      let next = Array.isArray(serverItems) ? serverItems : [];

      next = applyLocalFilters(next);

      const totalFromServer = Number.isFinite(t) ? Number(t) : undefined;
      setServerTotal(totalFromServer);

      const baseTotal = totalFromServer ?? next.length;
      const pages = Math.max(1, Math.ceil(baseTotal / pageSize));

      setItems(next);
      setTotal(baseTotal);
      setTotalPages(pages);
    } catch (e) {
      console.error("[Home] getProducts/search error:", e);
      setErr(e);
      setItems([]);
      setTotal(0);
      setTotalPages(1);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchList();
  }, [queryParams]);

  const onRefresh = () => fetchList();

  /* ===== 헤더(로그인/로그아웃/새로고침/검색 UI) ===== */
  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="flex items-center justify-between mb-4">
            <h1 className="text-3xl font-bold text-gray-900">🏪 편의점 행사상품</h1>

            <div className="flex items-center gap-3">
              <button
                onClick={onRefresh}
                disabled={loading}
                className="flex items-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg
                           hover:bg-gray-200 transition-colors disabled:opacity-50"
              >
                <RefreshCw className={`w-5 h-5 ${loading ? "animate-spin" : ""}`} />
                <span className="font-medium">새로고침</span>
              </button>

              {typeof isAuthenticated === "function" && isAuthenticated() ? (
                <>
                  <button
                    onClick={() => navigate("/mypage")}
                    className="flex items-center gap-2 px-4 py-2 bg-primary text-white rounded-lg
                               hover:bg-red-600 transition-colors"
                  >
                    <User className="w-5 h-5" />
                    <span className="font-medium">{user?.username || "마이페이지"}</span>
                  </button>

                  <button
                    onClick={() => {
                      logout();
                      alert("로그아웃되었습니다.");
                    }}
                    className="flex items-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg
                               hover:bg-gray-200 transition-colors"
                  >
                    <LogOut className="w-5 h-5" />
                    <span className="font-medium">로그아웃</span>
                  </button>
                </>
              ) : (
                <button
                  onClick={() => navigate("/login")}
                  className="flex items-center gap-2 px-4 py-2 bg-primary text-white rounded-lg
                             hover:bg-red-600 transition-colors"
                >
                  <LogIn className="w-5 h-5" />
                  <span className="font-medium">로그인</span>
                </button>
              )}
            </div>
          </div>

          {/* 검색창 */}
          <div className="relative mb-4">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              placeholder="상품명 검색..."
              value={keyword}
              onChange={(e) => {
                setKeyword(e.target.value);
                setPage(1);
              }}
              className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg 
                         focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>

          {/* 스토어 탭 + 필터바 */}
          <div className="flex gap-2 items-center overflow-x-auto pb-2">
            <div className="flex gap-2">
              {STORE_LABELS.map((s) => (
                <button
                  key={s.key}
                  onClick={() => {
                    setActiveStore(s.key);
                    setPage(1);
                  }}
                  className={`px-4 py-2 rounded-lg font-medium whitespace-nowrap transition-colors
                    ${activeStore === s.key ? "bg-primary text-white" : "bg-gray-100 text-gray-700 hover:bg-gray-200"}
                  `}
                >
                  {s.label}
                </button>
              ))}
            </div>

            <FilterBar
              value={filters}
              onChange={(next) => {
                setFilters(next);
                setPage(1);
              }}
            />
          </div>
        </div>
      </header>

      {/* 본문 */}
      <main className="max-w-7xl mx-auto px-4 py-8">
        {loading ? (
          <div className="text-center py-20">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
            <p className="mt-4 text-gray-600">상품을 불러오는 중...</p>
          </div>
        ) : items.length === 0 ? (
          <div className="text-center py-20">
            <p className="text-xl text-gray-600">
              조건에 맞는 상품이 없습니다 <span role="img" aria-label="sad">😢</span>
            </p>
            <p className="text-sm text-gray-400 mt-2">필터를 조정하거나 검색어를 변경해보세요!</p>
          </div>
        ) : (
          <>
            <div className="mb-4 text-gray-600">
              총 <span className="font-bold text-primary">{total}</span>개 상품
            </div>

            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-3">
              {items.map((p) => (
                <ProductCard
                  key={p.id ?? `${p.store}-${p.name}`}
                  product={p}
                  onSimilar={() => {
                    const id = p.id ?? p.item_id;
                    if (!id) return;
                    setDrawerItemId(String(id));
                    setDrawerOpen(true);
                  }}
                />
              ))}
            </div>

            {totalPages > 1 && (
              <div className="flex flex-col items-center gap-2 mt-6">
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    className="px-3 py-2 rounded-md border"
                    onClick={() => setPage((v) => Math.max(1, v - 1))}
                    disabled={page <= 1}
                  >
                    이전
                  </button>
                  <span className="text-sm">
                    {page} / {totalPages}
                  </span>
                  <button
                    type="button"
                    className="px-3 py-2 rounded-md border"
                    onClick={() => setPage((v) => Math.min(totalPages, v + 1))}
                    disabled={page >= totalPages}
                  >
                    다음
                  </button>
                </div>
                <div className="text-xs text-gray-500">
                  총 {serverTotal ?? items.length}개 / 페이지당 {pageSize}개
                </div>
              </div>
            )}
          </>
        )}

        {err && (
          <div className="mt-4 text-center text-sm text-red-500">
            데이터를 불러오지 못했습니다.
          </div>
        )}
      </main>

      <Chatbot />

      <SimilarDrawer
        open={drawerOpen}
        itemId={drawerItemId}
        onClose={() => setDrawerOpen(false)}
      />
    </div>
  );
}
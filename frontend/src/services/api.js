// frontend/src/services/api.js
import axios from "axios";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000/";
const USER_API_BASE_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000/api/v1";

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: { "Content-Type": "application/json" },
});

const userApiClient = axios.create({
  baseURL: USER_API_BASE_URL,
  timeout: 30000,
  headers: { "Content-Type": "application/json" },
});

apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("token");
    if (token) config.headers.Authorization = `Bearer ${token}`;
    return config;
  },
  (e) => Promise.reject(e)
);

userApiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("token");
    if (token) config.headers.Authorization = `Bearer ${token}`;
    return config;
  },
  (e) => Promise.reject(e)
);

apiClient.interceptors.response.use(
  (res) => res,
  (err) => {
    const s = err?.response?.status;
    // 401 Unauthorized - 토큰 만료 또는 인증 실패
    if (err.response?.status === 401) {
      const reqUrl = (err.config?.url || '').toString();
      const isAuthCall = reqUrl.includes('/login') || reqUrl.includes('/register');
      const onLoginPage = window.location.hash.startsWith('#/login');

      // 로그인/회원가입 요청에서의 401은 컴포넌트가 직접 처리하도록 그대로 throw
      if (isAuthCall || onLoginPage) {
        return Promise.reject(err);
      }

      // 그 외(보호된 API에서 401)만 세션 만료로 처리 → 리다이렉트
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.assign('/login?reason=expired');
      return; // 이후 Promise는 굳이 반환하지 않아도 됨
    }
    console.error("API Error:", s, err?.response?.data || err.message);
    return Promise.reject(err);
  }
);

userApiClient.interceptors.response.use(
  (res) => res,
  (err) => {
    const s = err?.response?.status;
    // 401 Unauthorized - 토큰 만료 또는 인증 실패
    if (err.response?.status === 401) {
      const reqUrl = (err.config?.url || '').toString();
      const isAuthCall = reqUrl.includes('/login') || reqUrl.includes('/register');
      const onLoginPage = window.location.hash.startsWith('#/login');

      // 로그인/회원가입 요청에서의 401은 컴포넌트가 직접 처리하도록 그대로 throw
      if (isAuthCall || onLoginPage) {
        return Promise.reject(err);
      }

      // 그 외(보호된 API에서 401)만 세션 만료로 처리 → 리다이렉트
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.assign('/login?reason=expired');
      return; // 이후 Promise는 굳이 반환하지 않아도 됨
    }
    console.error("API Error:", s, err?.response?.data || err.message);
    return Promise.reject(err);
  }
);

// ---- Chatbot ----
export const chatAPI = {
  askRaw: async (message, opts = {}) => {
    const { data } = await apiClient.post(
      "/ai/ask",
      { query: message, ...opts },
      { timeout: 8000 }
    );
    return data;
  },
  ask: async (query, opts = {}) => {
    const { data } = await apiClient.get("/ai/search", {
      params: { q: query, top_k: opts.top_k ?? 8 },
    });
    const items = data?.items ?? [];
    const answer = `상위 ${Math.min(items.length, opts.top_k ?? 8)}개를 보여드릴게요.`;
    return { answer, items, hints: data?.hints };
  },
  // ✅ 새로 추가: OpenAI 스트리밍 챗봇
  askGPT: async (message, onChunk) => {
    // ⭐ API_BASE_URL이 '/'로 끝나므로 앞에 / 안 붙임
    const url = `${API_BASE_URL}ai/chat`;
    console.log('🔍 [askGPT] Requesting:', url); // 디버깅용
    
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token') || ''}`
      },
      body: JSON.stringify({
        message,
        stream: true
      })
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || ''; // 마지막 불완전한 줄은 버퍼에 보관

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6).trim();
          
          if (data === '[DONE]') {
            return;
          }

          try {
            const parsed = JSON.parse(data);
            if (onChunk) {
              onChunk(parsed); // { type: 'text' | 'products' | 'error', content/products }
            }
          } catch (e) {
            console.warn('Failed to parse SSE data:', data);
          }
        }
      }
    }
  }
  
};

// ---- Health ----
export const healthAPI = {
  check: async () => {
    const { data } = await apiClient.get("/health");
    return data;
  },
};

// ---- Products ----
export const productAPI = {
  getProducts: async (params = {}) => {
    const adaptParams = (p) => {
      const out = {};

      // ✅ store 매핑 (7-ELEVEN → SEVEN으로 통일)
      if (p.store != null && p.store !== "") {
        const key = String(p.store).toUpperCase();
        const storeMap = {
          "7-ELEVEN": "SEVEN",
          "7ELEVEN": "SEVEN",
        };
        out.store = storeMap[key] ?? key;
      }

      if (p.brand != null && p.brand !== "") out.brand = p.brand;

      if (p.q) out.q = p.q;
      if (p.query) out.q = p.query;
      if (p.keyword) out.q = p.keyword;

      // ✅ promo / promotion_type 통일
      if (p.promo != null && p.promo !== "") {
        out.promotion_type = p.promo;
      } else if (p.promotion_type != null && p.promotion_type !== "") {
        out.promotion_type = p.promotion_type;
      }

      if (p.is_new !== undefined) out.is_new = p.is_new;
      if (p.min_price != null) out.min_price = p.min_price;
      if (p.max_price != null) out.max_price = p.max_price;
      if (p.sort) out.sort = p.sort;

      if (p.page != null) out.page = p.page;
      if (p.page_size != null) out.page_size = p.page_size;
      if (p.limit != null && out.page_size == null) out.page_size = Number(p.limit);
      if (p.skip != null) {
        const size = Number(out.page_size ?? 20);
        out.page = Math.floor(Number(p.skip) / size) + 1;
      }
      return out;
    };

    const serverParams = adaptParams(params);
    const { data } = await apiClient.get("/items", { params: serverParams });
    console.log("🔍 [getProducts] adapted params ->", serverParams);
    console.log("🔍 [getProducts] raw data:", data);

    const normalize = (it) => {
      const image = it.image_url ?? it.item_img_src ?? it.img ?? "";
      return {
        id: it.id ?? it.item_id,
        name: it.name ?? it.item_name,
        price: it.price ?? it.item_price,
        img: image,
        image_url: image,
        item_img_src: image,
        store: it.store ?? it.store_name ?? "",
        isPromo: Boolean(it.is_promo ?? it.isPromo ?? false),
        isNew: Boolean(it.is_new ?? it.isNew ?? false),
        promotionType: it.promotion_type ?? null,
      };
    };

    let rawItems = [];
    let total, page, pageSize;

    if (Array.isArray(data?.items)) {
      rawItems = data.items;
      total = data.total ?? data.count ?? data.items.length;
      page = data.page ?? undefined;
      pageSize = data.page_size ?? data.pageSize ?? undefined;
    } else if (Array.isArray(data)) {
      rawItems = data;
      total = data.length;
    } else if (data && typeof data === "object" && Array.isArray(data.results)) {
      rawItems = data.results;
      total = data.total ?? data.count ?? data.results.length;
    }

    const items = rawItems.map(normalize);
    console.log("🔍 [getProducts] normalized:", items, { total, page, pageSize });

    return { items, total, page, pageSize };
  },

  getProductDetail: async (id) => {
  const normalizeOne = (it) => {
    const image = it.image_url ?? it.item_img_src ?? it.img ?? "";
    return {
      id: it.id ?? it.item_id,
      name: it.name ?? it.item_name,
      price: it.price ?? it.item_price,
      img: image,
      image_url: image,
      item_img_src: image,
      store: it.store ?? it.store_name ?? "",
      isPromo: Boolean(it.is_promo ?? it.isPromo ?? false),
      isNew: Boolean(it.is_new ?? it.isNew ?? false),
      promotionType: it.promotion_type ?? null,
      category: it.category ?? it.item_category,
      summary: it.summary ?? it.description ?? "",
      scores: it.scores ?? undefined,
      calorie: it.calorie ?? undefined,
      protein: it.protein ?? undefined,
      sugar: it.sugar ?? undefined,
      source_url: it.source_url ?? it.link ?? "",
    };
  };

  const tryFind = (arr) => {
    const numId = Number(id);
    return arr?.find?.((x) =>
      String(x?.id) === String(id) ||
      String(x?.item_id) === String(id) ||
      (Number.isFinite(numId) && (Number(x?.id) === numId || Number(x?.item_id) === numId))
    );
  };

  const fetchByPath = async () => {
    const { data } = await apiClient.get(`/items/${encodeURIComponent(id)}`);
    if (!data) return null;
    const image = data.image_url ?? data.item_img_src ?? data.img ?? "";
    return {
      id: data.id ?? data.item_id,
      name: data.name ?? data.item_name,
      price: data.price ?? data.item_price,
      img: image,
      image_url: image,
      item_img_src: image,
      store: data.store ?? data.store_name ?? "",
      isPromo: Boolean(data.is_promo ?? data.isPromo ?? false),
      isNew: Boolean(data.is_new ?? data.isNew ?? false),
      promotionType: data.promotion_type ?? null,
      category: data.category ?? data.item_category,
      summary: data.summary ?? data.description ?? "",
      scores: data.scores ?? undefined,
      calorie: data.calorie ?? undefined,
      protein: data.protein ?? undefined,
      sugar: data.sugar ?? undefined,
      source_url: data.source_url ?? data.link ?? "",
    };
  };

  try {
    // 1) 쿼리 방식
    const { data } = await apiClient.get("/items", { params: { item_id: id } });
    if (Array.isArray(data?.items) || Array.isArray(data)) {
      const list = Array.isArray(data?.items) ? data.items : data;
      const found = tryFind(list);
      if (found) return normalizeOne(found);
      // 🔴 기존 버그: 여기서 arr[0] 반환 → 항상 첫 상품
      // ✅ 수정: 못 찾으면 path 방식으로 재조회
      return await fetchByPath();
    }
    if (data && typeof data === "object") {
      return normalizeOne(data);
    }
    return await fetchByPath();
  } catch {
    // 쿼리 실패 시 path 폴백
    return await fetchByPath();
  }
},

  searchProducts: async (keyword, params = {}) => {
    const { data } = await apiClient.get("/ai/search", {
      params: { q: keyword, ...params },
    });
    console.log("🔍 [searchProducts] raw:", data);
    return data;
  },

  createProduct: async () => { throw new Error("Not supported by backend"); },
  updateProduct: async () => { throw new Error("Not supported by backend"); },
  deleteProduct: async () => { throw new Error("Not supported by backend"); },
};

// ---- Bookmarks ----
const BK_KEY = "bookmarks_v1";
const readBK = () => {
  try { return JSON.parse(localStorage.getItem(BK_KEY) || "[]"); }
  catch { return []; }
};
const writeBK = (list) => localStorage.setItem(BK_KEY, JSON.stringify(list));

export const bookmarkAPI = {
  getBookmarks: async () => readBK(),
  addBookmark: async (productId) => {
    const id = Number(productId);
    const set = new Set(readBK().map(Number));
    set.add(id);
    writeBK(Array.from(set));
    return { ok: true };
  },
  removeBookmark: async (bookmarkId) => {
    const id = Number(bookmarkId);
    const next = readBK().filter((x) => Number(x) !== id);
    writeBK(next);
    return { ok: true };
  },
  removeBookmarkByProduct: async (productId) => {
    const id = Number(productId);
    const next = readBK().filter((x) => Number(x) !== id);
    writeBK(next);
    return { ok: true };
  },
  checkBookmark: async (productId) => {
    const id = Number(productId);
    const has = readBK().some((x) => Number(x) === id);
    return { bookmarked: has };
  },
};

// ---- Preferences ----
export const preferencesAPI = {
  getPreferences: async () => {
    const { data } = await apiClient.get("/preferences");
    return data;
  },
  createPreferences: async (preferences) => {
    const { data } = await apiClient.post("/preferences", preferences);
    return data;
  },
  updatePreferences: async (preferences) => {
    const { data } = await apiClient.put("/preferences", preferences);
    return data;
  },
  deletePreferences: async () => {
    const { data } = await apiClient.delete("/preferences");
    return data;
  },
};

// ---- AI similar ----
export const aiAPI = {
  similar: async (itemId, opts = {}) => {
    const id = String(itemId);
    const topK = Number(opts.top_k ?? 8);

    const normalizeList = (data) => {
      let arr = [];
      if (Array.isArray(data?.items)) arr = data.items;
      else if (Array.isArray(data?.results)) arr = data.results;
      else if (Array.isArray(data)) arr = data;
      else if (data && typeof data === "object" && data.item) arr = [data.item];

      return arr.map((it, idx) => {
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
        };
      });
    };

    const limitAndFilter = (items) =>
      items.filter((x) => String(x.id) !== id && String(x.item_id) !== id).slice(0, topK);

    try {
      const { data } = await apiClient.get(`/ai/similar/${encodeURIComponent(id)}`, { params: { top_k: topK } });
      const items = limitAndFilter(normalizeList(data));
      return { items };
    } catch (err) {
      console.error("[aiAPI.similar] failed:", err?.message);
      return { items: [] };
    }
  },

  reindex: async () => {
    const { data } = await apiClient.post("/ai/reindex");
    return data;
  },
  adminReindex: async () => {
    const { data } = await apiClient.post("/admin/reindex");
    return data;
  },
};

export default apiClient;

// ---- Auth ----
export const authAPI = {
  login:   async (email, password) => (await userApiClient.post('/auth/login',    { email, password })).data,
  register:async (email, password, username) => (await userApiClient.post('/auth/register', { email, password, username })).data,
  me:      async () => (await userApiClient.get('/auth/me')).data,
  logout:  async () => { try { await userApiClient.post('/auth/logout'); } catch (e) { console.error('로그아웃 API 에러:', e); } },
  deleteMe:async () => (await userApiClient.delete('/auth/withdrawal')).data,
  verifyPassword: async (password) => (await userApiClient.post('/auth/verify-password', { password })).data,
  updateProfile:  async (username) => (await userApiClient.patch('/auth/me', { username })).data,
  changePassword: async (current_password, new_password) => (await userApiClient.patch('/auth/password', { current_password, new_password })).data,
};

// src/components/SimilarDrawer.jsx
import { useEffect, useState } from "react";
import { aiAPI } from "../services/api"; // ← API 클라이언트 사용으로 통일

export default function SimilarDrawer({
  open,
  itemId,
  onClose,
}) {
  const [loading, setLoading] = useState(false);
  const [items, setItems] = useState([]);

  useEffect(() => {
    if (!open || !itemId) return;
    let aborted = false;

    (async () => {
      setLoading(true);
      try {
        // ✅ 항상 최대 8개로 통일
        const { items: sims } = await aiAPI.similar(String(itemId), { top_k: 8 });
        if (!aborted) setItems(sims || []);
      } catch (e) {
        if (!aborted) setItems([]);
      } finally {
        if (!aborted) setLoading(false);
      }
    })();

    return () => { aborted = true; };
  }, [open, itemId]);

  return (
    <div
      className={`fixed inset-0 z-40 ${open ? "pointer-events-auto" : "pointer-events-none"}`}
      aria-hidden={!open}
    >
      {/* overlay */}
      <div
        className={`absolute inset-0 bg-black/30 transition ${open ? "opacity-100" : "opacity-0"}`}
        onClick={onClose}
      />
      {/* drawer */}
      <aside
        className={`absolute right-0 top-0 h-full w-full max-w-lg transform bg-white p-5 shadow-2xl transition ${open ? "translate-x-0" : "translate-x-full"}`}
      >
        <div className="mb-3 flex items-center justify-between">
          <h3 className="text-lg font-bold">비슷한 상품</h3>
          <button onClick={onClose} className="rounded-lg border px-3 py-1">닫기</button>
        </div>

        {loading ? (
          <div className="text-gray-500">불러오는 중...</div>
        ) : items.length === 0 ? (
          <div className="text-gray-500">추천할 상품이 없어요.</div>
        ) : (
          <div className="grid grid-cols-2 gap-4">
            {items.map((it) => (
              <div key={`${it.id}-${it.name}`} className="rounded-xl border p-3 hover:shadow">
                {it.image_url ? (
                  <img
                    src={it.image_url}
                    alt={it.name}
                    className="mx-auto h-28 w-full object-contain"
                    loading="lazy"
                    onError={(e)=>{e.currentTarget.style.visibility="hidden";}}
                  />
                ) : (
                  <div className="flex h-28 items-center justify-center rounded bg-gray-100 text-gray-400">
                    이미지 없음
                  </div>
                )}
                <div className="mt-2 line-clamp-2 text-sm">{it.name}</div>
                <div className="mt-1 text-sm text-gray-500">{it.store}</div>
                <div className="mt-1 text-base font-semibold">
                  {new Intl.NumberFormat("ko-KR").format(it.price)}원
                </div>
              </div>
            ))}
          </div>
        )}
      </aside>
    </div>
  );
}

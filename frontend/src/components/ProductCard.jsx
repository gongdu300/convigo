// src/components/ProductCard.jsx
import { Flame, DollarSign, Heart } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export default function ProductCard({ product, onSimilar }) {
  const navigate = useNavigate();

  // 브랜드별 색상
  const brandColors = {
    CU: 'bg-purple-500',
    GS25: 'bg-blue-500',
    '세븐일레븐': 'bg-green-500',
    SEVEN: 'bg-green-500',
  };

  // 점수별 색상
  const getScoreColor = (score) => {
    if (score >= 8) return 'bg-green-100 text-green-800';
    if (score >= 6) return 'bg-yellow-100 text-yellow-800';
    return 'bg-red-100 text-red-800';
  };

  const handleCardClick = () => {
    if (!product) return;
    const id = product.id ?? product.item_id;
    if (id == null) return;
    navigate(`/product/${id}`);
  };

  return (
    <div className="product-card" onClick={handleCardClick}>
      {/* 이미지 영역 */}
      <div className="relative h-36 md:h-40 bg-white overflow-hidden border rounded-lg ">
        <img
          src={
            product.image_url ||
            product.img ||
            product.item_img_src ||
            'https://via.placeholder.com/300x300?text=No+Image'
          }
          alt={product.name}
          className="max-h-full max-w-full object-contain mx-auto"
          loading="lazy"
          decoding="async"
          onError={(e) => {
            // 이미지 없을 때 깜빡임 방지: 숨김 처리
            e.currentTarget.style.visibility = 'hidden';
          }}
        />

        {/* 브랜드 배지 */}
        <div
          className={`absolute top-2 left-2 ${
            brandColors[product.brand] || brandColors[product.store] || 'bg-gray-500'
          } text-white px-3 py-1 rounded-full text-xs font-bold`}
        >
          {product.brand || product.store || '기타'}
        </div>

        {/* 할인율 배지 */}
        {product.discount_rate && (
          <div className="absolute top-2 right-2 bg-red-500 text-white px-3 py-1 rounded-full text-xs font-bold">
            {Number(product.discount_rate).toFixed(0)}% ↓
          </div>
        )}
      </div>

      {/* 정보 영역 */}
      <div className="p-4">
        {/* 상품명 */}
        <h3 className="font-bold text-lg mb-2 line-clamp-2 h-14">{product.name}</h3>

        {/* 가격 */}
        <div className="flex items-center gap-2 mb-3">
          <span className="text-2xl font-bold text-primary">
            {Number(product.price)?.toLocaleString()}원
          </span>
          {product.original_price && (
            <span className="text-sm text-gray-400 line-through">
              {Number(product.original_price)?.toLocaleString()}원
            </span>
          )}
        </div>

        {/* 요약 */}
        {product.summary && (
          <p className="text-sm text-gray-600 mb-3 line-clamp-2">{product.summary}</p>
        )}

        {/* 점수 (맛/가성비/건강) */}
        <div className="flex gap-2 flex-wrap">
          {product.taste_score && (
            <span className={`score-badge ${getScoreColor(product.taste_score)}`}>
              <Flame className="w-3 h-3 mr-1" />
              맛 {Number(product.taste_score).toFixed(1)}
            </span>
          )}
          {product.value_score && (
            <span className={`score-badge ${getScoreColor(product.value_score)}`}>
              <DollarSign className="w-3 h-3 mr-1" />
              가성비 {Number(product.value_score).toFixed(1)}
            </span>
          )}
          {product.health_score && (
            <span className={`score-badge ${getScoreColor(product.health_score)}`}>
              <Heart className="w-3 h-3 mr-1" />
              건강 {Number(product.health_score).toFixed(1)}
            </span>
          )}
        </div>

        {/* 칼로리 */}
        {product.calories && (
          <div className="mt-3 text-xs text-gray-500">🔥 {product.calories} kcal</div>
        )}

        {/* 비슷한 상품 버튼 (카드 클릭으로 상세 이동 막기 위해 stopPropagation) */}
        <div className="mt-3 flex gap-2">
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              onSimilar && onSimilar();
            }}
            className="px-2 py-1 text-xs rounded-md border hover:bg-gray-50"
          >
            비슷한 상품
          </button>
        </div>
      </div>
    </div>
  );
}

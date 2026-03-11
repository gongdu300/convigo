import { useState } from 'react';
import { SlidersHorizontal, X } from 'lucide-react';

const FilterBar = ({ onFilterChange, currentFilters }) => {
  const [showFilters, setShowFilters] = useState(false);
  const [priceRange, setPriceRange] = useState(currentFilters.priceRange || [0, 50000]);
  const [selectedCategory, setSelectedCategory] = useState(currentFilters.category || 'all');
  const [sortBy, setSortBy] = useState(currentFilters.sortBy || 'latest');

  const categories = [
    { value: 'all', label: '전체' },
    { value: '식사', label: '식사' },
    { value: '음료', label: '음료' },
    { value: '스낵', label: '스낵' },
    { value: '아이스크림', label: '아이스크림' },
  ];

  const sortOptions = [
    { value: 'latest', label: '최신순' },
    { value: 'price_low', label: '가격 낮은순' },
    { value: 'price_high', label: '가격 높은순' },
    { value: 'discount', label: '할인율순' },
    { value: 'calories_low', label: '칼로리 낮은순' },
    { value: 'calories_high', label: '칼로리 높은순' },
  ];

  const handleMinChange = (e) => {
    const value = Number(e.target.value);
    setPriceRange([Math.min(value, priceRange[1] - 500), priceRange[1]]);
  };

  const handleMaxChange = (e) => {
    const value = Number(e.target.value);
    setPriceRange([priceRange[0], Math.max(value, priceRange[0] + 500)]);
  };

  const applyFilters = () => {
    onFilterChange({
      priceRange,
      category: selectedCategory,
      sortBy,
    });
    setShowFilters(false);
  };

  const resetFilters = () => {
    setPriceRange([0, 50000]);
    setSelectedCategory('all');
    setSortBy('latest');
    onFilterChange({
      priceRange: [0, 50000],
      category: 'all',
      sortBy: 'latest',
    });
  };

  const hasActiveFilters =
    priceRange[0] !== 0 ||
    priceRange[1] !== 50000 ||
    selectedCategory !== 'all' ||
    sortBy !== 'latest';

  return (
    <div className="relative">
      {/* 필터 토글 버튼 */}
      <button
        onClick={() => setShowFilters(!showFilters)}
        className="flex items-center gap-2 px-4 py-2 bg-white border-2 border-gray-200 rounded-lg hover:border-red-500 hover:text-red-500 transition-all"
      >
        <SlidersHorizontal className="w-5 h-5" />
        <span className="font-medium">필터</span>
        {hasActiveFilters && <span className="w-2 h-2 bg-red-500 rounded-full"></span>}
      </button>

      {/* 필터 패널 */}
      {showFilters && (
        <>
          <div className="fixed inset-0 bg-black/30 z-40" onClick={() => setShowFilters(false)} />
          <div className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 bg-white rounded-xl shadow-2xl z-50 border border-gray-100 overflow-hidden">
            <div className="flex items-center justify-between p-6 border-b border-gray-100">
              <h3 className="text-lg font-bold text-gray-900">필터 설정</h3>
              <button onClick={() => setShowFilters(false)} className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
                <X className="w-5 h-5 text-gray-500" />
              </button>
            </div>

            <div className="p-6 space-y-6 max-h-96 overflow-y-auto">
              {/* 가격 범위 슬라이더 */}
              <div>
                <label className="block text-sm font-semibold text-gray-900 mb-4">가격 범위</label>
                
                {/* 가격 표시 */}
                <div className="flex items-center justify-between text-sm mb-4">
                  <span className="px-3 py-1 bg-red-50 rounded-lg font-medium text-red-700">
                    {priceRange[0].toLocaleString()}원
                  </span>
                  <span className="text-gray-400">~</span>
                  <span className="px-3 py-1 bg-red-50 rounded-lg font-medium text-red-700">
                    {priceRange[1].toLocaleString()}원
                  </span>
                </div>

                {/* 듀얼 레인지 슬라이더 */}
                <div className="relative h-12 pt-2">
                  {/* 배경 트랙 */}
                  <div className="absolute top-5 w-full h-2 bg-gray-200 rounded-full"></div>
                  
                  {/* 활성 범위 (선택된 구간) */}
                  <div
                    className="absolute top-5 h-2 bg-gradient-to-r from-red-400 to-red-500 rounded-full"
                    style={{
                      left: `${(priceRange[0] / 50000) * 100}%`,
                      right: `${100 - (priceRange[1] / 50000) * 100}%`,
                    }}
                  ></div>

                  {/* 최솟값 슬라이더 */}
                  <input
                    type="range"
                    min="0"
                    max="50000"
                    step="500"
                    value={priceRange[0]}
                    onChange={handleMinChange}
                    className="absolute w-full top-2 h-1 appearance-none bg-transparent pointer-events-none py-4
                             [&::-webkit-slider-thumb]:pointer-events-auto
                             [&::-webkit-slider-thumb]:appearance-none 
                             [&::-webkit-slider-thumb]:w-5 
                             [&::-webkit-slider-thumb]:h-5 
                             [&::-webkit-slider-thumb]:rounded-full 
                             [&::-webkit-slider-thumb]:bg-red-500
                             [&::-webkit-slider-thumb]:border-3
                             [&::-webkit-slider-thumb]:border-red-500
                             [&::-webkit-slider-thumb]:cursor-pointer
                             [&::-webkit-slider-thumb]:shadow-lg
                             [&::-webkit-slider-thumb]:hover:scale-110
                             [&::-webkit-slider-thumb]:transition-transform
                             [&::-webkit-slider-thumb]:z-10
                             [&::-moz-range-thumb]:pointer-events-auto
                             [&::-moz-range-thumb]:appearance-none 
                             [&::-moz-range-thumb]:w-5 
                             [&::-moz-range-thumb]:h-5 
                             [&::-moz-range-thumb]:rounded-full 
                             [&::-moz-range-thumb]:bg-red-500
                             [&::-moz-range-thumb]:border-3
                             [&::-moz-range-thumb]:border-red-500
                             [&::-moz-range-thumb]:cursor-pointer
                             [&::-moz-range-thumb]:shadow-lg"
                    style={{ zIndex: priceRange[0] > 25000 ? 5 : 4 }}
                  />

                  {/* 최댓값 슬라이더 */}
                  <input
                    type="range"
                    min="0"
                    max="50000"
                    step="500"
                    value={priceRange[1]}
                    onChange={handleMaxChange}
                    className="absolute w-full top-2 h-1 appearance-none bg-transparent pointer-events-none py-4
                             [&::-webkit-slider-thumb]:pointer-events-auto
                             [&::-webkit-slider-thumb]:appearance-none 
                             [&::-webkit-slider-thumb]:w-5 
                             [&::-webkit-slider-thumb]:h-5 
                             [&::-webkit-slider-thumb]:rounded-full 
                             [&::-webkit-slider-thumb]:bg-red-500
                             [&::-webkit-slider-thumb]:border-3
                             [&::-webkit-slider-thumb]:border-red-500
                             [&::-webkit-slider-thumb]:cursor-pointer
                             [&::-webkit-slider-thumb]:shadow-lg
                             [&::-webkit-slider-thumb]:hover:scale-110
                             [&::-webkit-slider-thumb]:transition-transform
                             [&::-moz-range-thumb]:pointer-events-auto
                             [&::-moz-range-thumb]:appearance-none 
                             [&::-moz-range-thumb]:w-5 
                             [&::-moz-range-thumb]:h-5 
                             [&::-moz-range-thumb]:rounded-full 
                             [&::-moz-range-thumb]:bg-red-500
                             [&::-moz-range-thumb]:border-3
                             [&::-moz-range-thumb]:border-red-500
                             [&::-moz-range-thumb]:cursor-pointer
                             [&::-moz-range-thumb]:shadow-lg"
                    style={{ zIndex: priceRange[1] <= 25000 ? 5 : 4 }}
                  />
                </div>
              </div>

              {/* 카테고리 */}
              <div>
                <label className="block text-sm font-semibold text-gray-900 mb-3">카테고리</label>
                <div className="flex flex-wrap gap-2">
                  {categories.map((cat) => (
                    <button
                      key={cat.value}
                      onClick={() => setSelectedCategory(cat.value)}
                      className={`px-4 py-2 rounded-lg font-medium transition-all ${
                        selectedCategory === cat.value
                          ? 'bg-red-500 text-white shadow-md'
                          : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                      }`}
                    >
                      {cat.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* 정렬 */}
              <div>
                <label className="block text-sm font-semibold text-gray-900 mb-3">정렬</label>
                <div className="grid grid-cols-2 gap-2">
                  {sortOptions.map((option) => (
                    <button
                      key={option.value}
                      onClick={() => setSortBy(option.value)}
                      className={`px-4 py-2 rounded-lg font-medium transition-all text-sm ${
                        sortBy === option.value
                          ? 'bg-red-500 text-white shadow-md'
                          : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                      }`}
                    >
                      {option.label}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            <div className="p-4 border-t border-gray-100 flex gap-2">
              <button
                onClick={resetFilters}
                className="flex-1 py-3 border-2 border-gray-200 text-gray-700 rounded-lg font-medium hover:bg-gray-50 transition-colors"
              >
                초기화
              </button>
              <button
                onClick={applyFilters}
                className="flex-1 py-3 bg-red-500 text-white rounded-lg font-medium hover:bg-red-600 transition-colors shadow-md"
              >
                적용하기
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default FilterBar;
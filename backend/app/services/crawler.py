"""
편의점 행사상품 통합 크롤러 (Playwright Async) - 개선 버전
- CU, GS25, 세븐일레븐 크롤링
- 페이지네이션 지원 (> 버튼 클릭)
- 강화된 에러 처리 및 재시도 로직
"""
import asyncio
import re
from typing import List, Dict, Optional
from playwright.async_api import async_playwright, Page, Browser, TimeoutError as PlaywrightTimeout
from urllib.parse import urljoin
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ConvenienceStoreCrawler:
    """편의점 크롤러 통합 클래스 (개선 버전)"""
    
    def __init__(self, headless: bool = True, delay: float = 1.5):
        self.headless = headless
        self.delay = delay
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        self.max_retries = 3
    
    async def crawl_all(self, max_per_brand: int = 50) -> Dict[str, List[Dict]]:
        """
        모든 편의점 크롤링 실행
        
        Args:
            max_per_brand: 브랜드당 최대 크롤링 개수
            
        Returns:
            {'CU': [...], 'GS25': [...], '세븐일레븐': [...]}
        """
        results = {
            "CU": [],
            "GS25": [],
            "세븐일레븐": []
        }
        
        start_time = datetime.now()
        logger.info(f"🚀 크롤링 시작 - {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=self.headless,
                args=['--disable-blink-features=AutomationControlled']
            )
            
            try:
                # CU 크롤링
                logger.info("📍 CU 크롤링 시작...")
                results["CU"] = await self.crawl_cu(browser, max_per_brand)
                await asyncio.sleep(self.delay)
                
                # GS25 크롤링
                logger.info("📍 GS25 크롤링 시작...")
                results["GS25"] = await self.crawl_gs25(browser, max_per_brand)
                await asyncio.sleep(self.delay)
                
                # 세븐일레븐 크롤링
                logger.info("📍 세븐일레븐 크롤링 시작...")
                results["세븐일레븐"] = await self.crawl_seven_eleven(browser, max_per_brand)
                
            except Exception as e:
                logger.error(f"❌ 크롤링 실패: {e}")
            finally:
                await browser.close()
        
        # 결과 요약
        end_time = datetime.now()
        elapsed = (end_time - start_time).seconds
        total_products = sum(len(products) for products in results.values())
        
        logger.info(f"\n{'='*50}")
        logger.info(f"✅ 크롤링 완료 - 소요시간: {elapsed}초")
        logger.info(f"📦 총 {total_products}개 상품 수집")
        for brand, products in results.items():
            logger.info(f"   - {brand}: {len(products)}개")
        logger.info(f"{'='*50}\n")
        
        return results
    
    # ==================== CU 크롤러 ====================
    async def crawl_cu(self, browser: Browser, max_products: int) -> List[Dict]:
        """CU 행사상품 크롤링"""
        products = []
        page = None
        
        try:
            page = await browser.new_page(user_agent=self.user_agent)
            url = "https://cu.bgfretail.com/product/product.do?category=product&depth2=4&sf=N"
            
            await page.goto(url, wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(3000)
            
            # 쿠키/팝업 닫기 시도
            await self._close_popups(page)
            
            current_page = 1
            max_pages = 5  # 최대 5페이지
            
            while len(products) < max_products and current_page <= max_pages:
                logger.info(f"   CU 페이지 {current_page} 크롤링 중...")
                
                # 페이지 로딩 대기
                await self._scroll_page(page)
                await page.wait_for_timeout(2000)
                
                # 여러 셀렉터 시도
                items = await self._find_items(page, [
                    ".prodListWrap li",
                    ".prod_list li", 
                    ".product-list li",
                    "ul.prodWrap li",
                    ".itemWrap li"
                ])
                
                logger.info(f"   CU 페이지 {current_page}: {len(items)}개 아이템 발견")
                
                for item in items:
                    if len(products) >= max_products:
                        break
                    
                    try:
                        product = await self._parse_cu_item(item, url)
                        if product and product not in products:
                            products.append(product)
                    except Exception as e:
                        logger.debug(f"   CU 상품 파싱 오류: {e}")
                
                # 다음 페이지 버튼 찾기 및 클릭
                if len(products) < max_products and current_page < max_pages:
                    next_clicked = await self._click_next_page(page, [
                        "a.next",
                        ".pagination .next",
                        "button.next",
                        "a[title='다음']"
                    ])
                    
                    if not next_clicked:
                        logger.info(f"   CU 다음 페이지 없음. 크롤링 종료")
                        break
                    
                    await page.wait_for_timeout(2000)
                    current_page += 1
                else:
                    break
            
        except Exception as e:
            logger.error(f"❌ CU 크롤링 오류: {e}")
        finally:
            if page:
                await page.close()
        
        return products[:max_products]
    
    async def _parse_cu_item(self, item, base_url: str) -> Optional[Dict]:
        """CU 상품 데이터 파싱"""
        try:
            # 상품명 추출
            name = await self._extract_text(item, [
                ".prodName",
                ".prod_name", 
                ".name",
                ".tit",
                ".product_name",
                "dt.name"
            ])
            
            if not name:
                return None
            
            # 가격 정보 추출
            price_text = await self._extract_text(item, [
                ".price",
                ".prod_price",
                ".cost",
                "dd.price"
            ])
            
            original_price, sale_price, discount_rate = self._parse_price(price_text)
            
            # 이미지 URL 추출
            image_url = await self._extract_image(item, base_url)
            
            # 카테고리 추측
            category = self._guess_category(name)
            
            if sale_price == 0:
                return None
            
            return {
                'name': name.strip(),
                'brand': 'CU',
                'category': category,
                'price': sale_price,
                'original_price': original_price,
                'discount_rate': discount_rate,
                'calories': None,
                'protein': None,
                'sugar': None,
                'image_url': image_url,
                'source_url': base_url,
                'summary': None,
                'pros': None,
                'cons': None,
                'taste_score': None,
                'value_score': None,
                'health_score': None
            }
            
        except Exception as e:
            logger.debug(f"CU 파싱 실패: {e}")
            return None
    
    # ==================== GS25 크롤러 ====================
    async def crawl_gs25(self, browser: Browser, max_products: int) -> List[Dict]:
        """GS25 행사상품 크롤링"""
        products = []
        page = None
        
        try:
            page = await browser.new_page(user_agent=self.user_agent)
            url = "http://gs25.gsretail.com/gscvs/ko/products/event-goods"
            
            await page.goto(url, wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(3000)
            
            await self._close_popups(page)
            
            current_page = 1
            max_pages = 5
            
            while len(products) < max_products and current_page <= max_pages:
                logger.info(f"   GS25 페이지 {current_page} 크롤링 중...")
                
                await self._scroll_page(page)
                await page.wait_for_timeout(2000)
                
                items = await self._find_items(page, [
                    ".prod_list li",
                    ".product-list li",
                    ".goods-list li",
                    ".item-list li",
                    "ul.prod_list > li"
                ])
                
                logger.info(f"   GS25 페이지 {current_page}: {len(items)}개 아이템 발견")
                
                for item in items:
                    if len(products) >= max_products:
                        break
                    
                    try:
                        product = await self._parse_gs25_item(item, url)
                        if product and product not in products:
                            products.append(product)
                    except Exception as e:
                        logger.debug(f"   GS25 상품 파싱 오류: {e}")
                
                if len(products) < max_products and current_page < max_pages:
                    next_clicked = await self._click_next_page(page, [
                        "a.next",
                        ".pagination .next",
                        "button.next",
                        ".pagingType01 a.next"
                    ])
                    
                    if not next_clicked:
                        break
                    
                    await page.wait_for_timeout(2000)
                    current_page += 1
                else:
                    break
            
        except Exception as e:
            logger.error(f"❌ GS25 크롤링 오류: {e}")
        finally:
            if page:
                await page.close()
        
        return products[:max_products]
    
    async def _parse_gs25_item(self, item, base_url: str) -> Optional[Dict]:
        """GS25 상품 파싱"""
        try:
            name = await self._extract_text(item, [
                ".prod_name",
                ".tit",
                ".name", 
                ".title",
                ".goods_name"
            ])
            
            if not name:
                return None
            
            price_text = await self._extract_text(item, [
                ".price",
                ".cost",
                ".goods_price"
            ])
            
            original_price, sale_price, discount_rate = self._parse_price(price_text)
            image_url = await self._extract_image(item, base_url)
            category = self._guess_category(name)
            
            if sale_price == 0:
                return None
            
            return {
                'name': name.strip(),
                'brand': 'GS25',
                'category': category,
                'price': sale_price,
                'original_price': original_price,
                'discount_rate': discount_rate,
                'calories': None,
                'protein': None,
                'sugar': None,
                'image_url': image_url,
                'source_url': base_url,
                'summary': None,
                'pros': None,
                'cons': None,
                'taste_score': None,
                'value_score': None,
                'health_score': None
            }
            
        except Exception as e:
            logger.debug(f"GS25 파싱 실패: {e}")
            return None
    
    # ==================== 세븐일레븐 크롤러 ====================
    async def crawl_seven_eleven(self, browser: Browser, max_products: int) -> List[Dict]:
        """세븐일레븐 행사상품 크롤링"""
        products = []
        page = None
        
        try:
            page = await browser.new_page(user_agent=self.user_agent)
            url = "https://www.7-eleven.co.kr/product/presentList.asp"
            
            await page.goto(url, wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(3000)
            
            await self._close_popups(page)
            
            current_page = 1
            max_pages = 5
            
            while len(products) < max_products and current_page <= max_pages:
                logger.info(f"   세븐일레븐 페이지 {current_page} 크롤링 중...")
                
                await self._scroll_page(page)
                await page.wait_for_timeout(2000)
                
                items = await self._find_items(page, [
                    ".prod_item",
                    ".product",
                    ".itemWrap .item",
                    "ul.product_list li",
                    ".listarea li"
                ])
                
                logger.info(f"   세븐일레븐 페이지 {current_page}: {len(items)}개 아이템 발견")
                
                for item in items:
                    if len(products) >= max_products:
                        break
                    
                    try:
                        product = await self._parse_seven_item(item, url)
                        if product and product not in products:
                            products.append(product)
                    except Exception as e:
                        logger.debug(f"   세븐일레븐 상품 파싱 오류: {e}")
                
                if len(products) < max_products and current_page < max_pages:
                    next_clicked = await self._click_next_page(page, [
                        "a.next",
                        ".pagination .next",
                        "img[alt='다음']",
                        "a[title='다음 페이지']"
                    ])
                    
                    if not next_clicked:
                        break
                    
                    await page.wait_for_timeout(2000)
                    current_page += 1
                else:
                    break
            
        except Exception as e:
            logger.error(f"❌ 세븐일레븐 크롤링 오류: {e}")
        finally:
            if page:
                await page.close()
        
        return products[:max_products]
    
    async def _parse_seven_item(self, item, base_url: str) -> Optional[Dict]:
        """세븐일레븐 상품 파싱"""
        try:
            name = await self._extract_text(item, [
                ".name",
                ".prod_name",
                ".tit",
                ".item_name"
            ])
            
            if not name:
                return None
            
            price_text = await self._extract_text(item, [
                ".price",
                ".cost",
                ".item_price"
            ])
            
            original_price, sale_price, discount_rate = self._parse_price(price_text)
            image_url = await self._extract_image(item, base_url)
            category = self._guess_category(name)
            
            if sale_price == 0:
                return None
            
            return {
                'name': name.strip(),
                'brand': '세븐일레븐',
                'category': category,
                'price': sale_price,
                'original_price': original_price,
                'discount_rate': discount_rate,
                'calories': None,
                'protein': None,
                'sugar': None,
                'image_url': image_url,
                'source_url': base_url,
                'summary': None,
                'pros': None,
                'cons': None,
                'taste_score': None,
                'value_score': None,
                'health_score': None
            }
            
        except Exception as e:
            logger.debug(f"세븐일레븐 파싱 실패: {e}")
            return None
    
    # ==================== 유틸리티 함수 ====================
    async def _find_items(self, page: Page, selectors: List[str]):
        """여러 셀렉터로 아이템 찾기"""
        for selector in selectors:
            try:
                items = await page.query_selector_all(selector)
                if items:
                    return items
            except:
                continue
        return []
    
    async def _extract_text(self, element, selectors: List[str]) -> Optional[str]:
        """여러 셀렉터로 텍스트 추출"""
        for selector in selectors:
            try:
                elem = await element.query_selector(selector)
                if elem:
                    text = await elem.inner_text()
                    if text and text.strip():
                        return text.strip()
            except:
                continue
        return None
    
    async def _extract_image(self, element, base_url: str) -> str:
        """이미지 URL 추출"""
        try:
            img_elem = await element.query_selector("img")
            if img_elem:
                src = await img_elem.get_attribute("src") or \
                      await img_elem.get_attribute("data-src") or \
                      await img_elem.get_attribute("data-original")
                
                if src:
                    if src.startswith("//"):
                        return "https:" + src
                    elif src.startswith("http"):
                        return src
                    else:
                        return urljoin(base_url, src)
        except:
            pass
        return ""
    
    def _parse_price(self, price_text: str) -> tuple:
        """가격 텍스트 파싱 (원가, 할인가, 할인율)"""
        if not price_text:
            return 0, 0, 0
        
        prices = re.findall(r'[\d,]+', price_text)
        
        original_price = 0
        sale_price = 0
        discount_rate = 0
        
        if len(prices) >= 2:
            original_price = int(prices[0].replace(',', ''))
            sale_price = int(prices[1].replace(',', ''))
        elif len(prices) == 1:
            sale_price = int(prices[0].replace(',', ''))
            original_price = sale_price
        
        if original_price and sale_price and original_price > sale_price:
            discount_rate = round((original_price - sale_price) / original_price * 100, 1)
        
        return original_price, sale_price, discount_rate
    
    async def _click_next_page(self, page: Page, selectors: List[str]) -> bool:
        """다음 페이지 버튼 클릭"""
        for selector in selectors:
            try:
                next_btn = await page.query_selector(selector)
                if next_btn:
                    # 버튼이 보이는지 확인
                    is_visible = await next_btn.is_visible()
                    if is_visible:
                        await next_btn.click()
                        logger.info(f"   ✓ 다음 페이지 클릭 성공")
                        return True
            except Exception as e:
                logger.debug(f"   다음 페이지 클릭 실패 ({selector}): {e}")
                continue
        return False
    
    async def _scroll_page(self, page: Page):
        """페이지 스크롤 (동적 콘텐츠 로드)"""
        try:
            for _ in range(3):
                await page.evaluate("window.scrollBy(0, window.innerHeight)")
                await page.wait_for_timeout(500)
            await page.evaluate("window.scrollTo(0, 0)")
        except Exception as e:
            logger.debug(f"스크롤 오류: {e}")
    
    async def _close_popups(self, page: Page):
        """팝업/쿠키 배너 닫기"""
        popup_selectors = [
            "button.close",
            ".popup-close",
            ".layer-close",
            "[class*='close']",
            "button[aria-label='닫기']"
        ]
        
        for selector in popup_selectors:
            try:
                close_btn = await page.query_selector(selector)
                if close_btn:
                    await close_btn.click()
                    await page.wait_for_timeout(500)
            except:
                continue
    
    def _guess_category(self, name: str) -> str:
        """상품명으로 카테고리 추측"""
        name_lower = name.lower()
        
        keywords = {
            '식사': ['삼각김밥', '도시락', '샌드위치', '샌드', '버거', '김밥', '컵밥', '죽', '밥'],
            '음료': ['음료', '주스', '커피', '우유', '콜라', '사이다', '워터', '물', '티', '차', '스무디'],
            '스낵': ['과자', '스낵', '칩', '쿠키', '초콜릿', '캔디', '젤리', '껌', '사탕'],
            '아이스크림': ['아이스크림', '빙과', '아이스', '바', '콘'],
            '라면': ['라면', '면', '컵라면', '봉지라면'],
            '디저트': ['케이크', '빵', '베이커리', '도넛', '마카롱']
        }
        
        for category, words in keywords.items():
            if any(word in name_lower for word in words):
                return category
        
        return '기타'


# ==================== 더미 데이터 생성기 ====================
class DummyCrawler:
    """테스트용 더미 데이터 생성"""
    
    async def crawl_all(self, max_per_brand: int = 20) -> Dict[str, List[Dict]]:
        """더미 데이터 반환"""
        logger.info("🎭 더미 데이터 모드 실행 중...")
        
        from urllib.parse import quote
        
        def safe_image(text: str) -> str:
            return f"https://via.placeholder.com/300x300/4A90E2/ffffff?text={quote(text)}"
        
        dummy_data = {
            'CU': [
                {
                    'name': '불닭볶음면 큰사발',
                    'brand': 'CU',
                    'category': '라면',
                    'price': 2500,
                    'original_price': 3000,
                    'discount_rate': 16.7,
                    'calories': 530,
                    'protein': 11.0,
                    'sugar': 8.0,
                    'image_url': safe_image('불닭볶음면'),
                    'source_url': 'https://cu.bgfretail.com',
                    'summary': '매콤한 맛이 일품인 인기 라면',
                    'pros': '매운맛 최고, 양 많음',
                    'cons': '칼로리 높음',
                    'taste_score': 8.5,
                    'value_score': 9.0,
                    'health_score': 4.0
                },
                {
                    'name': '삼각김밥 참치마요',
                    'brand': 'CU',
                    'category': '식사',
                    'price': 1200,
                    'original_price': 1500,
                    'discount_rate': 20.0,
                    'calories': 280,
                    'protein': 8.0,
                    'sugar': 2.0,
                    'image_url': safe_image('삼각김밥'),
                    'source_url': 'https://cu.bgfretail.com',
                    'summary': '간편한 한끼, 참치마요 가득',
                    'pros': '가성비 좋음, 간편함',
                    'cons': '양 적음',
                    'taste_score': 7.5,
                    'value_score': 8.5,
                    'health_score': 6.0
                },
                {
                    'name': 'CU 바나나우유',
                    'brand': 'CU',
                    'category': '음료',
                    'price': 1500,
                    'original_price': 2000,
                    'discount_rate': 25.0,
                    'calories': 180,
                    'protein': 5.0,
                    'sugar': 22.0,
                    'image_url': safe_image('바나나우유'),
                    'source_url': 'https://cu.bgfretail.com',
                    'summary': '달콤한 바나나 향이 가득',
                    'pros': '맛 좋음, 향 좋음',
                    'cons': '당 함량 높음',
                    'taste_score': 9.0,
                    'value_score': 7.5,
                    'health_score': 5.0
                }
            ],
            'GS25': [
                {
                    'name': '코카콜라 제로 500ml',
                    'brand': 'GS25',
                    'category': '음료',
                    'price': 1500,
                    'original_price': 2000,
                    'discount_rate': 25.0,
                    'calories': 0,
                    'protein': 0.0,
                    'sugar': 0.0,
                    'image_url': safe_image('코카콜라제로'),
                    'source_url': 'http://gs25.gsretail.com',
                    'summary': '제로 칼로리 청량음료',
                    'pros': '제로 칼로리, 청량함',
                    'cons': '인공감미료 사용',
                    'taste_score': 8.0,
                    'value_score': 7.0,
                    'health_score': 7.5
                },
                {
                    'name': 'GS25 도시락 불고기',
                    'brand': 'GS25',
                    'category': '식사',
                    'price': 3500,
                    'original_price': 4500,
                    'discount_rate': 22.2,
                    'calories': 650,
                    'protein': 25.0,
                    'sugar': 10.0,
                    'image_url': safe_image('불고기도시락'),
                    'source_url': 'http://gs25.gsretail.com',
                    'summary': '푸짐한 불고기가 가득한 도시락',
                    'pros': '양 많음, 맛 좋음',
                    'cons': '가격이 조금 비쌈',
                    'taste_score': 8.5,
                    'value_score': 7.5,
                    'health_score': 6.0
                }
            ],
            '세븐일레븐': [
                {
                    'name': '허니버터칩',
                    'brand': '세븐일레븐',
                    'category': '스낵',
                    'price': 1800,
                    'original_price': 2200,
                    'discount_rate': 18.2,
                    'calories': 550,
                    'protein': 6.0,
                    'sugar': 15.0,
                    'image_url': safe_image('허니버터칩'),
                    'source_url': 'https://www.7-eleven.co.kr',
                    'summary': '달콤짭짤한 중독성 강한 맛',
                    'pros': '맛있음, 바삭함',
                    'cons': '칼로리 폭탄, 양 적음',
                    'taste_score': 9.0,
                    'value_score': 6.5,
                    'health_score': 3.0
                },
                {
                    'name': '세븐일레븐 샌드위치 햄치즈',
                    'brand': '세븐일레븐',
                    'category': '식사',
                    'price': 2800,
                    'original_price': 3500,
                    'discount_rate': 20.0,
                    'calories': 420,
                    'protein': 18.0,
                    'sugar': 5.0,
                    'image_url': safe_image('햄치즈샌드'),
                    'source_url': 'https://www.7-eleven.co.kr',
                    'summary': '신선한 햄과 치즈의 조화',
                    'pros': '담백함, 간편함',
                    'cons': '빵이 조금 건조함',
                    'taste_score': 7.0,
                    'value_score': 7.5,
                    'health_score': 6.5
                }
            ]
        }
        
        # max_per_brand 만큼만 반환
        result = {k: v[:max_per_brand] for k, v in dummy_data.items()}
        
        # 결과 로깅
        for brand, products in result.items():
            logger.info(f"✅ {brand}: {len(products)}개 더미 데이터 생성")
        
        return result


# ==================== 테스트 실행 ====================
async def test_crawler(use_dummy: bool = False, headless: bool = True):
    """크롤러 테스트"""
    print("\n" + "="*60)
    print("🚀 편의점 크롤러 테스트 시작")
    print("="*60 + "\n")
    
    if use_dummy:
        print("📝 더미 데이터 모드로 실행합니다.\n")
        crawler = DummyCrawler()
    else:
        print("🌐 실제 크롤링 모드로 실행합니다.")
        print(f"   - Headless: {headless}")
        print(f"   - 브랜드당 최대: 10개\n")
        crawler = ConvenienceStoreCrawler(headless=headless, delay=1.5)
    
    results = await crawler.crawl_all(max_per_brand=10)
    
    # 결과 출력
    print("\n" + "="*60)
    print("📊 크롤링 결과")
    print("="*60)
    
    for brand, products in results.items():
        print(f"\n【 {brand} 】 - {len(products)}개 상품")
        print("-" * 60)
        
        for i, product in enumerate(products[:3], 1):  # 상위 3개만 출력
            print(f"{i}. {product['name']}")
            print(f"   가격: {product['price']:,}원 (할인율: {product['discount_rate']}%)")
            print(f"   카테고리: {product['category']}")
            if product.get('calories'):
                print(f"   칼로리: {product['calories']}kcal")
        
        if len(products) > 3:
            print(f"   ... 외 {len(products) - 3}개 상품")
    
    print("\n" + "="*60)
    print("✅ 테스트 완료!")
    print("="*60 + "\n")
    
    return results


if __name__ == "__main__":
    import sys
    
    # 명령행 인자로 모드 선택
    use_dummy = "--dummy" in sys.argv or "-d" in sys.argv
    headless = "--headless" in sys.argv or "-h" in sys.argv or len(sys.argv) == 1
    
    print("\n사용법:")
    print("  python crawler.py              # 실제 크롤링 (headless)")
    print("  python crawler.py --dummy      # 더미 데이터")
    print("  python crawler.py --no-headless # 브라우저 보면서 크롤링\n")
    
    asyncio.run(test_crawler(use_dummy=use_dummy, headless=headless))
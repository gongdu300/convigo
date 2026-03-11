# crawler/seven_crawler.py
from __future__ import annotations

import re
import time
import json
import argparse
from typing import List, Optional, Tuple

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    ElementClickInterceptedException,
    StaleElementReferenceException,
)

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import SQLAlchemyError
from backend.database import Item, init_db, engine
from pathlib import Path

DOCS_DIR = (Path(__file__).resolve().parents[1] / "docs")
DOCS_DIR.mkdir(exist_ok=True)
# ─────────────────────────────────────────────────────────────
# 사이트/탭
HOME_URL = "http://www.7-eleven.co.kr/"
PROMO_PAGE_BY_GNB = "#gnb > li:nth-child(2) > ul > li:nth-child(3) > a"  # 상단 2번 메뉴 hover → 하위 3번째 클릭  :contentReference[oaicite:5]{index=5}

TAB_IDX = {
    "1+1": 1,   # 기본이 1+1 탭이라 클릭 없이 시작 가능하나, 안전하게 index 1로도 대응
    "2+1": 2,
    "할인": 4,  # “할인행사” 탭  :contentReference[oaicite:6]{index=6}
    "전체": 0,  # 별도 의미 없음
}

# 안전장치
MAX_CLICKS_DEFAULT = 0   # 더보기 클릭 횟수 제한(0=무제한)
MAX_CONSEC_SKIP    = 40

# ─────────────────────────────────────────────────────────────
# 유틸
def parse_price(text: str) -> Optional[int]:
    if not text:
        return None
    digits = re.findall(r"\d+", text)
    if not digits:
        return None
    try:
        return int("".join(digits))
    except Exception:
        return None

def get_text_safe(el) -> str:
    try:
        t = el.text.strip()
        if t:
            return t
    except Exception:
        pass
    for attr in ("innerText", "textContent"):
        try:
            t = (el.get_attribute(attr) or "").strip()
            if t:
                return t
        except Exception:
            pass
    return ""

def wait_dom_ready(driver, timeout=15):
    WebDriverWait(driver, timeout).until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )

# ─────────────────────────────────────────────────────────────
# 공통: 카드 탐색 / 버튼 안전 클릭
def find_cards(driver):
    # 7-Eleven 목록은 ul#listUl > li 구조 (첫/마지막은 ‘더보기’/비어있는 엘리먼트이므로 후처리에서 거름)
    return driver.find_elements(By.CSS_SELECTOR, "#listUl > li")

def safe_js_click(driver, locator: Tuple[By, str], timeout=10) -> bool:
    try:
        el = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located(locator)
        )
        WebDriverWait(driver, timeout).until(EC.element_to_be_clickable(locator))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
        try:
            el.click()
        except (ElementClickInterceptedException, StaleElementReferenceException):
            driver.execute_script("arguments[0].click();", el)
        return True
    except TimeoutException:
        return False

# ─────────────────────────────────────────────────────────────
# 네비게이션/탭/더보기 (니 팀원 코드 흐름을 통합)
def go_promo_page(driver, wait):
    # 홈 → gnb 2번에 hover → 하위 3번째 클릭  :contentReference[oaicite:7]{index=7}
    driver.get(HOME_URL)
    wait_dom_ready(driver)
    parent = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "#gnb > li:nth-child(2)")))
    ActionChains(driver).move_to_element(parent).pause(0.2).perform()
    safe_js_click(driver, (By.CSS_SELECTOR, PROMO_PAGE_BY_GNB), timeout=10)
    time.sleep(0.8)

def click_tab(driver, tab_key: str):
    """wrap_tab의 li 인덱스로 탭 전환 (1=1+1, 2=2+1, 4=할인)"""
    idx = TAB_IDX.get(tab_key, 0)
    if idx <= 0:
        return
    locator = (By.CSS_SELECTOR, f".wrap_tab ul > li:nth-child({idx}) a")
    safe_js_click(driver, locator, timeout=8)
    wait_dom_ready(driver)
    # 리스트 등장 대기
    WebDriverWait(driver, 12).until(EC.presence_of_element_located((By.CSS_SELECTOR, "ul#listUl")))

def expand_all_items(driver, max_clicks: int = 0, growth_timeout=10, delay=0.6):
    """
    ‘더보기’가 사라질 때까지 클릭. 클릭 전/후 카드 수 증가를 확인해 stale/무의미 클릭 방지.
    (원본 스크립트의 more 버튼 로직을 안전화해서 통합)  :contentReference[oaicite:8]{index=8} :contentReference[oaicite:9]{index=9}
    """
    locator = (By.CSS_SELECTOR, "li.btn_more > a")
    clicks = 0
    while True:
        if max_clicks and clicks >= max_clicks:
            print(f"[INFO] 더보기 {max_clicks}회 제한 도달 → 중단")
            break
        prev = len(find_cards(driver))
        clicked = safe_js_click(driver, locator, timeout=6)
        if not clicked:
            print("[INFO] 더보기 버튼 없음/비활성 → 종료")
            break
        clicks += 1
        time.sleep(delay)
        try:
            WebDriverWait(driver, growth_timeout).until(lambda d: len(find_cards(d)) > prev)
        except TimeoutException:
            print("[INFO] 더보기 클릭 후 목록 증가 없음 → 종료")
            break

# ─────────────────────────────────────────────────────────────
# 파싱
def extract_one(li_el, tab_key: Optional[str]) -> Optional[dict]:
    """
    - 이름: .name
    - 가격: .price (콤마 제거 후 숫자 파싱)
    - 이미지: img @src
    - 행사 구분: 탭 키로 우선 지정, 없으면 배지 텍스트(.tag_list_01 내부)에서 보조 추정
      * 1+1: .ico_tag_06, 2+1: .ico_tag_07, 할인: .ico_tag_02  :contentReference[oaicite:10]{index=10} :contentReference[oaicite:11]{index=11} :contentReference[oaicite:12]{index=12}
    """
    # 일부 li는 더보기/빈칸이 섞여있어 노이즈 스킵
    klass = (li_el.get_attribute("class") or "").lower()
    if "btn_more" in klass:
        return None

    # 이름
    name = ""
    try:
        name = get_text_safe(li_el.find_element(By.CLASS_NAME, "name"))
    except Exception:
        pass

    # 가격
    price = None
    try:
        raw = get_text_safe(li_el.find_element(By.CLASS_NAME, "price"))
        raw = raw.replace(",", "")
        price = parse_price(raw)
    except Exception:
        pass

    # 이미지
    image_url = ""
    try:
        image_url = li_el.find_element(By.TAG_NAME, "img").get_attribute("src") or ""
    except Exception:
        pass

    # 배지
    badge_txt = ""
    try:
        badge_txt = get_text_safe(li_el.find_element(By.CSS_SELECTOR, ".tag_list_01"))
    except Exception:
        pass

    promo = tab_key if tab_key in ("1+1", "2+1", "할인") else None
    if not promo:
        if "1+1" in badge_txt:
            promo = "1+1"
        elif "2+1" in badge_txt:
            promo = "2+1"
        elif "할인" in badge_txt:
            promo = "할인"

    if not name or price is None:
        return None

    return {
        "store": "SEVEN",
        "name": name,
        "price": price,
        "image_url": image_url,
        "is_promo": True,
        "promotion_type": promo,
        "is_new": False,
    }

# ─────────────────────────────────────────────────────────────
# 본체
def crawl_one_tab(tab_key: str, max_clicks: int) -> List[dict]:
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1280,1200")

    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 15)

    results: List[dict] = []

    try:
        go_promo_page(driver, wait)     # 홈 → 행사 페이지  :contentReference[oaicite:13]{index=13}
        click_tab(driver, tab_key)      # 탭 전환
        time.sleep(0.6)

        expand_all_items(driver, max_clicks=(max_clicks or 0))  # 더보기 무제한  :contentReference[oaicite:14]{index=14}

        cards = find_cards(driver)
        # 원본들은 첫/마지막 li를 건너뛰었음 → 동일하게 스킵  :contentReference[oaicite:15]{index=15} :contentReference[oaicite:16]{index=16} :contentReference[oaicite:17]{index=17}
        if len(cards) >= 2:
            cards = cards[1:-1]

        consecutive_skip = 0
        for li in cards:
            row = extract_one(li, tab_key)
            if not row:
                consecutive_skip += 1
                if consecutive_skip >= MAX_CONSEC_SKIP:
                    print("[WARN] 연속 스킵 과다 → 나머지 생략")
                    break
                continue
            results.append(row)

    finally:
        driver.quit()

    # 디버깅 덤프
    with open(DOCS_DIR / f"seven_{tab_key}.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    return results

# ─────────────────────────────────────────────────────────────
# DB 저장 (GS·CU와 동일)
def save_to_db(rows: List[dict]) -> None:
    if not rows:
        print("[DB] 저장할 데이터 없음")
        return
    try:
        stmt = pg_insert(Item.__table__).values(rows)
        stmt = stmt.on_conflict_do_nothing(index_elements=["store", "name", "promotion_type"])
        with engine.begin() as conn:
            conn.execute(stmt)
        print(f"[DB] upsert 완료: {len(rows)}건 (중복 무시)")
    except SQLAlchemyError as e:
        print("[DB-FAIL]", e)

# ─────────────────────────────────────────────────────────────
# CLI (GS·CU와 동일 UX)
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--type", choices=["1+1", "2+1", "할인", "전체"], help="특정 탭만 수집")
    parser.add_argument("--all", action="store_true", help="1+1/2+1/할인 전부 수집")
    parser.add_argument("--pages", type=int, default=MAX_CLICKS_DEFAULT,
                        help=f"더보기 최대 클릭 수 (기본 {MAX_CLICKS_DEFAULT}, 0=무제한)")
    args = parser.parse_args()

    init_db()

    targets = ["2+1"]
    if args.all:
        targets = ["1+1", "2+1", "할인"]
    elif args.type:
        targets = [args.type]

    total = 0
    for t in targets:
        print(f"\n=== SEVEN {t} 크롤링 시작 (더보기 {args.pages if args.pages else '무제한'}) ===")
        data = crawl_one_tab(t, max_clicks=args.pages)
        print(f"[{t}] 수집 {len(data)}건")
        save_to_db(data)
        total += len(data)

    print(f"\n총 {total}건 저장 시도 완료")

if __name__ == "__main__":
    main()

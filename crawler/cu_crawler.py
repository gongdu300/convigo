# crawler/cu_crawler.py
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
# 페이지/탭
EVENT_URL = "https://cu.bgfretail.com/event/plus.do?category=event&depth2=1&sf=N"

TAB_TEXT = {
    "전체": "전체",
    "1+1": "1+1",
    "2+1": "2+1",
}

# 안전장치
MAX_PAGES_DEFAULT = 0   # 0이면 무제한(= 더보기 제한 없음)
MAX_CONSEC_SKIP   = 40  # 한 페이지 내 연속 파싱 실패 허용치

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
    """innerText / textContent / .text 전부 시도해서 최대한 텍스트 확보."""
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
    """
    CU의 목록 li는 보통 'li.prod_list' 형태.
    넓게 탐색해서 6개 이상 잡히는 첫 셀렉터를 채택.
    """
    sels = [
        ".prodListWrap ul > li.prod_list",
        "ul.prod_list > li",
        "ul.prodList > li",
        "ul > li.prod_list",
    ]
    for sel in sels:
        els = driver.find_elements(By.CSS_SELECTOR, sel)
        if len(els) >= 6:
            return els
    return driver.find_elements(By.CSS_SELECTOR, "li.prod_list")

def safe_js_click(driver, locator: Tuple[By, str], timeout=10) -> bool:
    """
    stale 방지: 매번 재조회 + JS 클릭 + 클릭 가능 대기.
    """
    try:
        el = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located(locator)
        )
        WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable(locator)
        )
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
        try:
            el.click()
        except (ElementClickInterceptedException, StaleElementReferenceException):
            driver.execute_script("arguments[0].click();", el)
        return True
    except TimeoutException:
        return False

# ─────────────────────────────────────────────────────────────
# CU 전용: 탭 전환 + 더보기 확장
def click_tab(driver, wait, tab_key: str) -> None:
    """왼쪽/상단 필터에서 '전체' / '1+1' / '2+1' 선택 후, 리스트 갯수 변화로 전환 완료 확인."""
    if tab_key == "전체":
        return
    label = TAB_TEXT.get(tab_key, tab_key)

    before = len(find_cards(driver))
    candidates = [
        (By.XPATH, f"//a[normalize-space()='{label}']"),
        (By.XPATH, f"//button[normalize-space()='{label}']"),
        (By.XPATH, f"//*[self::a or self::button or self::span][normalize-space()='{label}']"),
    ]
    for how, sel in candidates:
        try:
            el = wait.until(EC.presence_of_element_located((how, sel)))
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
            driver.execute_script("arguments[0].click();", el)
            break
        except Exception:
            continue

    # 전환 완료: 카드 개수가 바뀌거나 최소 1개 이상 로드될 때까지
    try:
        WebDriverWait(driver, 12).until(
            lambda d: len(find_cards(d)) != before and len(find_cards(d)) >= 1
        )
    except TimeoutException:
        # 변화가 없더라도 계속 진행(일부 페이지는 기본이 동일 목록)
        pass

def expand_all_items(driver, max_clicks: int = 0, growth_timeout=10, delay=0.6):
    """
    '더보기'를 가능한 한 끝까지 클릭.
    - 매 클릭 전후 카드 수가 증가하는지 확인(증가 안 하면 종료)
    - locator는 매번 재조회해서 stale element 방지
    """
    clicks = 0
    locator = (By.CSS_SELECTOR, "div.prodListBtn a[href^='javascript:nextPage']")

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

        # 클릭 후 증가 대기
        try:
            WebDriverWait(driver, growth_timeout).until(
                lambda d: len(find_cards(d)) > prev
            )
        except TimeoutException:
            # 마지막 구간: 증가가 없으면 종료
            print("[INFO] 더보기 클릭 후 목록 증가 없음 → 종료")
            break

# ─────────────────────────────────────────────────────────────
# 파싱
def extract_one(item_el, promo_key: Optional[str]) -> Optional[dict]:
    """
    우리 DB 스키마에 맞게 필드 매핑:
      - name: .name 계열
      - price: .price 계열 (숫자만 추출)
      - image_url: img @src
      - promotion_type: 탭 키(1+1/2+1) 우선, 없으면 배지 텍스트에서 추정
    """
    # 이름
    name = ""
    for sel in ["p.name", "span.name", "strong.name", ".name", "dt.name", "dd.name"]:
        try:
            name = get_text_safe(item_el.find_element(By.CSS_SELECTOR, sel))
            if name:
                break
        except Exception:
            continue

    # 가격
    price = None
    for sel in [".price", "p.price", "span.price", "strong.price", "em.price",
                ".prod_price", ".tx_num", "li.price", "div.price"]:
        try:
            raw = get_text_safe(item_el.find_element(By.CSS_SELECTOR, sel))
            price = parse_price(raw)
            if price is not None:
                break
        except Exception:
            continue
    if price is None:
        price = parse_price(get_text_safe(item_el))  # 카드 전체 텍스트에서 보루 추출

    # 이미지
    image_url = ""
    for sel in ["img", "figure img", ".thumb img", ".prod_img img"]:
        try:
            image_url = item_el.find_element(By.CSS_SELECTOR, sel).get_attribute("src") or ""
            if image_url:
                break
        except Exception:
            continue

    # 배지(없어도 됨)
    badge = ""
    try:
        badge = get_text_safe(item_el.find_element(By.CLASS_NAME, "badge"))
    except Exception:
        pass

    promo = promo_key if promo_key in ("1+1", "2+1") else None
    if not promo:
        if "1+1" in badge:
            promo = "1+1"
        elif "2+1" in badge:
            promo = "2+1"

    if not name or price is None:
        return None

    return {
        "store": "CU",
        "name": name,
        "price": price,
        "image_url": image_url,
        "is_promo": True,
        "promotion_type": promo,
        "is_new": False,
    }

# ─────────────────────────────────────────────────────────────
# 본체
def crawl_one_tab(promo_key: str, max_pages: int) -> List[dict]:
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1280,1200")

    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 15)

    results: List[dict] = []

    try:
        driver.get(EVENT_URL)
        wait_dom_ready(driver)
        click_tab(driver, wait, promo_key)
        time.sleep(0.8)

        # 더보기 버튼을 페이지(=클릭) 제한만큼 눌러 전체 로드
        expand_all_items(driver, max_clicks=(max_pages or 0))

        # 전체가 로드되었으니 한 번에 수집
        cards = find_cards(driver)
        if not cards:
            print("[WARN] 카드 요소를 찾지 못함")

        consecutive_skip = 0
        for card in cards:
            row = extract_one(card, promo_key if promo_key != "전체" else None)
            if not row:
                consecutive_skip += 1
                if consecutive_skip >= MAX_CONSEC_SKIP:
                    print("[WARN] 연속 스킵 과다 → 남은 카드 생략")
                    break
                continue
            results.append(row)

    finally:
        driver.quit()

    # 디버깅용 덤프
    with open(DOCS_DIR / f"cu_{promo_key}.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    return results

# ─────────────────────────────────────────────────────────────
# DB 저장
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
# CLI
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--type", choices=["1+1", "2+1", "전체"], help="특정 탭만 수집")
    parser.add_argument("--all", action="store_true", help="1+1/2+1 전부 수집")
    parser.add_argument("--pages", type=int, default=MAX_PAGES_DEFAULT,
                        help=f"더보기 최대 클릭 수 (기본 {MAX_PAGES_DEFAULT}, 0=무제한)")
    args = parser.parse_args()

    init_db()

    targets = ["2+1"]
    if args.all:
        targets = ["1+1", "2+1"]
    elif args.type:
        targets = [args.type]

    total = 0
    for t in targets:
        print(f"\n=== CU {t} 크롤링 시작 (더보기 {args.pages if args.pages else '무제한'}) ===")
        data = crawl_one_tab(t, max_pages=args.pages)
        print(f"[{t}] 수집 {len(data)}건")
        save_to_db(data)
        total += len(data)

    print(f"\n총 {total}건 저장 시도 완료")

if __name__ == "__main__":
    main()

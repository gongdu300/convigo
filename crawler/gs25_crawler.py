# crawler/gs25_crawler.py
from __future__ import annotations

import re
import time
import json
import argparse
from typing import List, Optional

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import SQLAlchemyError
from backend.database import Item, init_db, engine
from pathlib import Path

DOCS_DIR = (Path(__file__).resolve().parents[1] / "docs")
DOCS_DIR.mkdir(exist_ok=True)
# ─────────────────────────────────────────────────────────────
# 사이트/탭 텍스트
EVENT_URL = "http://gs25.gsretail.com/gscvs/ko/products/event-goods#;"

# 팀원 코드의 메뉴 이동/리스트 접근 흐름을 사용 (홈 → 상품 → 행사상품 → 전체)  ← gs25.py 로직 반영
# 이후 탭 전환은 가능한 한 텍스트 기반으로 처리
TAB_TEXT = {
    "전체": "TOTAL",        # 상단 필터 버튼 id
    "1+1": "1+1 행사",
    "2+1": "2+1 행사",
    "증정": "덤증정 행사",
}

# 안전장치
MAX_PAGES_DEFAULT = 0  # 0이면 무제한
MAX_CONSEC_SKIP = 40

# ─────────────────────────────────────────────────────────────
# 유틸
def parse_price(text: str) -> Optional[int]:
    """'2,500원', '￦2,500', ' 2 500 ' 등에서 숫자만 뽑기 (우리 프로젝트 공통 파서)"""
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
    """innerText/textContent/text 순회해서 안전하게 텍스트 추출"""
    try:
        t = el.text.strip()
        if t:
            return t
    except Exception:
        pass
    for attr in ("innerText", "textContent"):
        try:
            t = el.get_attribute(attr) or ""
            t = t.strip()
            if t:
                return t
        except Exception:
            pass
    return ""

def wait_dom_ready(driver, timeout=15):
    """DOM 완전 로드까지 대기 (팀원 로직 반영)"""
    WebDriverWait(driver, timeout).until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )

def wait_prodlist_ready(driver, timeout=15):
    return WebDriverWait(driver, timeout).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "ul.prod_list, div.prod_box"))
    )

def find_visible_prodlist(driver):
    """보이는 prod_list 하나 선택 (팀원 로직 반영)"""
    prod_lists = [ul for ul in driver.find_elements(By.CSS_SELECTOR, "ul.prod_list") if ul.is_displayed()]
    return prod_lists[0] if prod_lists else None

# ⬇️ find_visible_prodlist 아래에 추가
def get_items_on_page(driver):
    # 1) ul.prod_list > li 패턴
    uls = [ul for ul in driver.find_elements(By.CSS_SELECTOR, "ul.prod_list") if ul.is_displayed()]
    if uls:
        try:
            return uls[0].find_elements(By.TAG_NAME, "li")
        except Exception:
            pass
    # 2) 카드형(div.prod_box) 패턴
    return driver.find_elements(By.CSS_SELECTOR, "div.prod_box")

def extract_item_li(li_el) -> Optional[dict]:
    """
    팀원 파싱 로직을 우리 스키마로 매핑:
      - 이름: .tit
      - 가격: .price
      - 이미지: img @src
      - 행사 뱃지: .flg01 (있으면 promotion_type 추정)
    """
    try:
        name = get_text_safe(li_el.find_element(By.CLASS_NAME, "tit"))
    except Exception:
        name = ""

    price = None
    try:
        raw_price = get_text_safe(li_el.find_element(By.CLASS_NAME, "price"))
        price = parse_price(raw_price)
    except Exception:
        pass

    image_url = ""
    try:
        image_url = li_el.find_element(By.TAG_NAME, "img").get_attribute("src") or ""
    except Exception:
        pass

    promo = None
    try:
        badge = get_text_safe(li_el.find_element(By.CLASS_NAME, "flg01"))
        if "1+1" in badge:
            promo = "1+1"
        elif "2+1" in badge:
            promo = "2+1"
        elif "증정" in badge or "덤" in badge:
            promo = "증정"
    except Exception:
        pass

    if not name or price is None:
        return None

    return {
        "store": "GS25",
        "name": name,
        "price": price,
        "image_url": image_url,
        "is_promo": True,
        "promotion_type": promo,   # 탭 클릭에서 고정되지 않으면 뱃지로 추정
        "is_new": False,
    }


def select_tab_if_needed(driver, promo_key: str):
    """탭 전환을 JS클릭으로 강제하고, 배지(flg01)에 해당 탭 문자열이 나타날 때까지 대기"""
    if promo_key == "전체":
        return
    label = TAB_TEXT.get(promo_key, promo_key).replace(" 행사", "")
    # 후보 셀렉터(보이는 것만)
    cands = [
        (By.LINK_TEXT, label),
        (By.PARTIAL_LINK_TEXT, label),
        (By.XPATH, f"//a[normalize-space()[contains(., '{label}')]]"),
    ]
    for how, sel in cands:
        try:
            el = WebDriverWait(driver, 8).until(EC.presence_of_element_located((how, sel)))
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
            driver.execute_script("arguments[0].click();", el)
            break
        except Exception:
            continue
    # 탭 반영 대기: 첫 아이템의 배지 텍스트가 해당 탭 키워드를 포함할 때까지
    # 탭 클릭 후: 리스트가 다시 로드될 때까지 대기
    WebDriverWait(driver, 12).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "ul.prod_list li"))
    )

def get_max_page(driver) -> Optional[int]:
    """팀원 코드의 movePage(n) 파싱 로직 반영"""
    try:
        el = driver.find_element(By.XPATH, '//*[@id="wrap"]/div[4]/div[2]/div[3]/div/div/div[4]/div/a[4]')
        onclick = el.get_attribute("onclick") or ""
        m = re.search(r"movePage\((\d+)\)", onclick)
        if m:
            return int(m.group(1))
    except Exception:
        pass
    return None

# ─────────────────────────────────────────────────────────────
# 크롤링 본체
def crawl_one_tab(promo_key: str, max_pages: int) -> List[dict]:
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1280,1200")

    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 15)

    results: List[dict] = []
    pages_done = 0

    try:
        driver.get(EVENT_URL)
        wait_dom_ready(driver)      # 팀원 네비게이션 반영
        select_tab_if_needed(driver, promo_key)
        # 탭 전환 반영 후 리스트 대기(갱신 보장)
        wait_dom_ready(driver)
        wait_prodlist_ready(driver)

        # 최대 페이지 추정 (없으면 while로 next 버튼 탐색)
        max_page = get_max_page(driver)
        # 페이지 루프
        while True:
            pages_done += 1
            if max_pages and pages_done > max_pages:
                print(f"[WARN] 페이지 {max_pages}개 초과, 강제 종료")
                break
            time.sleep(0.6)
            wait_dom_ready(driver)
            prodlist = find_visible_prodlist(driver)

            if not prodlist:
                print("[WARN] prod_list 없음 → 다음 페이지 시도")
            consecutive_skip = 0
            added_this_page = 0

            items = get_items_on_page(driver)

            for li in items:
                row = extract_item_li(li)
                if not row:
                    consecutive_skip += 1
                    if consecutive_skip >= MAX_CONSEC_SKIP:
                        print("[WARN] 연속 스킵 과다 → 다음 페이지 이동")
                        break
                    continue

                # 탭이 고정되어 있으면 promotion_type을 탭으로 강제
                if promo_key != "전체":
                    row["promotion_type"] = promo_key

                results.append(row)
                added_this_page += 1

            # 페이지 루프 내부에서
            if added_this_page == 0:
                zero_pages += 1
                if zero_pages >= 2:
                    print("[WARN] 연속 2페이지에서 신규 0건 → 종료")
                    break
            else:
                zero_pages = 0  

            # 다음 페이지 (현재 탭에서 '보이는' next만)
            next_btn = None
            for a in driver.find_elements(By.CSS_SELECTOR, "div.paging a.next"):
                if a.is_displayed():
                    next_btn = a
                    break
            if not next_btn:
                break
            cls = (next_btn.get_attribute("class") or "").lower()
            if "disabled" in cls:
                break

            try:
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", next_btn)
                driver.execute_script("arguments[0].click();", next_btn)
                time.sleep(1.1)
                wait_dom_ready(driver)
                wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "ul.prod_list, div.prod_box")))
            except Exception:
                break


            # 팀원 로직처럼 최대 페이지가 명확하면 빠른 종료
            if max_page and pages_done >= max_page:
                break

    finally:
        driver.quit()

    # 디버깅 저장(우리 관례 유지)
    with open(DOCS_DIR / f"gs25_{promo_key}.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    return results

# ─────────────────────────────────────────────────────────────
# DB 저장 (우리 프로젝트 로직 그대로)
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
# CLI (우리 프로젝트 규약 그대로)
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--type", choices=["1+1", "2+1", "증정", "전체"], help="특정 탭만 수집")
    parser.add_argument("--all", action="store_true", help="1+1/2+1/증정 전부 수집")
    parser.add_argument(
        "--pages", type=int, default=0,
        help="탭당 최대 페이지 수 (0 = 무제한)"
    )
    args = parser.parse_args()

    init_db()

    targets = ["2+1"]
    if args.all:
        targets = ["1+1", "2+1", "증정"]
    elif args.type:
        targets = [args.type]

    total = 0
    for t in targets:
        print(f"\n=== GS25 {t} 크롤링 시작 (최대 {args.pages}p) ===")
        data = crawl_one_tab(t, max_pages=args.pages)
        print(f"[{t}] 수집 {len(data)}건")
        save_to_db(data)
        total += len(data)

    print(f"\n총 {total}건 저장 시도 완료")

if __name__ == "__main__":
    main()

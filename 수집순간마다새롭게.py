# 롯데호텔이용권 웹 스크래핑
# 환경 : 고도몰 이커머스
# 주소 : https://eshop.lottehotel.com/goods/goods_list.php?cateCd=005
# 페이지소스보기 : view-source:https://eshop.lottehotel.com/goods/goods_list.php?cateCd=005
# 브랜드 : .item_info_cont .item_tit_box .item_brand strong
# 상품명 : .item_info_cont .item_tit_box .item_name
# 가격 : .item_money_box .item_price span
# 페이지네이션 : .pagination .pagination ul li 
# 파이썬이 아닌척 보완에 안걸리고 수집을 계속하려면

"""
인간미 넘치는 휴먼 에뮬레이션
클릭과 클릭 사이에 반드시 무작위 대기 시간을 섞어주어야 합니다.
끝이 어디인지 모르는 상태에서 더 이상 상품이 없을 때까지 
자동으로 계속 다음 페이지를 찾아가는 보편적인(Generic) 코드
"""

from datetime import datetime
import os
import random
import time
import pandas as pd
import requests
from bs4 import BeautifulSoup

# 1. 대상 URL 세팅 (카테고리 번호만 지정)
base_url = "https://eshop.lottehotel.com/goods/goods_list.php?cateCd=005"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://eshop.lottehotel.com/",
    "Connection": "keep-alive",
}

product_list = []
page = 1  # 1페이지부터 시작
consecutive_failures = 0

print("🚀 마지막 페이지를 찾을 때까지 무한 수집을 시작합니다...")

while True:  # 💡 끝날 때까지 무한 반복
    target_url = f"{base_url}&page={page}"
    print(f"\n[페이지 {page}] 수집 시도 중... 🔗 {target_url}")

    try:
        response = requests.get(target_url, headers=headers, timeout=10)

        # 차단 혹은 에러 체크
        if response.status_code != 200:
            print(
                f"⚠️ 차단 감지 또는 에러 발생! (HTTP 상태 코드: {response.status_code})"
            )
            consecutive_failures += 1
            if consecutive_failures >= 2:
                print("🚨 연속 차단으로 인해 안전을 위해 수집을 즉시 중단합니다.")
                break
            continue

        consecutive_failures = 0
        soup = BeautifulSoup(response.text, "html.parser")

        # 상품 박스 전체 찾기
        items = soup.select(".item_info_cont")

        # 🔥 [종료 조건 1] 해당 페이지에 상품이 단 하나도 없을 때 (끝 페이지 도달)
        if not items:
            print(
                f"🏁 [알림] {page}페이지에 상품이 없습니다. 수집을 정상 종료합니다."
            )
            break

        # 상품 정보 파싱
        for item in items:
            brand_el = item.select_one(".item_tit_box .item_brand strong")
            brand = brand_el.text.strip() if brand_el else "N/A"

            name_el = item.select_one(".item_tit_box .item_name")
            name = name_el.text.strip() if name_el else "N/A"

            price_el = item.select_one(".item_money_box .item_price span")
            if not price_el:
                parent = item.parent
                price_el = parent.select_one(".item_money_box .item_price span")
            price = price_el.text.strip() if price_el else "N/A"

            product_list.append(
                {"페이지": page, "브랜드": brand, "상품명": name, "가격": price}
            )

        print(f"✅ {page}페이지 완료! (현재까지 누적 상품 수: {len(product_list)}개)")

        # 🔥 [종료 조건 2] 페이지네이션에서 '다음 페이지' 버튼이 더 이상 없는지 체크
        next_btn = soup.select_one(".btn_page_next")
        if next_btn and ("href" in next_btn.attrs) and ("#" in next_btn["href"]):
            print("🏁 [알림] 마지막 페이지 버튼을 감지하여 수집을 종료합니다.")
            break

    except Exception as e:
        print(f"❌ 예외 발생 (현재 {page} 페이지): {e}")
        break

    # 다음 페이지로 번호 증가
    page += 1

    # 차단 우회를 위한 사람다운 패턴 (랜덤 대기)
    sleep_time = random.uniform(1.8, 3.2)
    print(f"💤 {sleep_time:.2f}초 동안 대기 후 다음 페이지로...")
    time.sleep(sleep_time)

# 3. 데이터프레임 시각화 포맷으로 변환 및 저장
df = pd.DataFrame(product_list)

print("\n================ 최종 수집 결과 ================")
if not df.empty:
    print(f"총 수집된 상품: {len(df)}개")

    # data 폴더가 없으면 자동으로 생성해 주는 안전장치
    if not os.path.exists("data"):
        os.makedirs("data")

    # 📌 현재 날짜와 시간(연월일_시분초)을 조합하여 유니크한 파일명 생성
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = os.path.join("data", f"lotte_hotel_data_{timestamp}.csv")

    # encoding='utf-8-sig'를 넣어줘야 구글 시트나 엑셀에서 한글이 깨지지 않습니다.
    df.to_csv(file_path, index=False, encoding="utf-8-sig")
    print(f"📁 '{file_path}' 파일로 저장이 완료되었습니다!")
else:
    print("수집된 데이터가 없습니다.")
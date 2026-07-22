# 롯데호텔이용권 웹 스크래핑
# 환경 : 고도몰 이커머스
# 주소 : https://eshop.lottehotel.com/goods/goods_list.php?cateCd=005
# 페이지소스보기 : view-source:https://eshop.lottehotel.com/goods/goods_list.php?cateCd=005
# 브랜드 : .item_info_cont .item_tit_box .item_brand strong
# 상품명 : .item_info_cont .item_tit_box .item_name
# 가격 : .item_money_box .item_price span
# 페이지네이션 : .pagination .pagination ul li 
# 3페이지까지 데이터를 수집하여 데이터프레임으로 변환하는 파이썬 스크래핑 코드

"""
고도몰의 경우 페이지 이동 시 page 파라미터를 사용하므로, 
URL 뒤에 &page=1, &page=2 형태를 붙여 반복문으로 처리하도록 설계했습니다. 
또한, 해당 사이트는 봇 차단(403 Forbidden)이 발생할 수 있으므로 
브라우저인 것처럼 속이는 User-Agent 헤더를 추가했습니다.
"""
import time
import pandas as pd
import requests
from bs4 import BeautifulSoup

# 기본 설정
base_url = (
    "https://eshop.lottehotel.com/goods/goods_list.php?cateCd=005&page="
)
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# 데이터를 저장할 리스트
product_list = []

print("데이터 수집을 시작합니다...")

# 1페이지부터 3페이지까지 반복
for page in range(1, 4):
    target_url = f"{base_url}{page}"
    print(f"[{page} 페이지 수집 중] : {target_url}")

    try:
        response = requests.get(target_url, headers=headers, timeout=10)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")

            # 상품 리스트가 담긴 부모 컨테이너 찾기 (일반적으로 고도몰은 .item_goods_sec 이나 리스트 형태 내부)
            # 제공해주신 선택자를 기반으로 개별 상품 영역을 탐색합니다.
            # 보통 .item_info_cont를 가지고 있는 부모/동등 레벨 요소를 기준으로 묶습니다.
            items = soup.select(".item_info_cont")

            for item in items:
                # 브랜드 추출
                brand_el = item.select_one(".item_tit_box .item_brand strong")
                brand = brand_el.text.strip() if brand_el else "N/A"

                # 상품명 추출
                name_el = item.select_one(".item_tit_box .item_name")
                name = name_el.text.strip() if name_el else "N/A"

                # 가격 추출 (가격 박스는 item_info_cont 내부에 있거나 바로 옆에 위치함)
                # item 내부에 없다면 상위/형제 노드에서 찾아야 할 수 있습니다.
                price_el = item.select_one(".item_money_box .item_price span")
                if not price_el:
                    # 구조에 따라 상위 요소나 형제 요소에서 검색 시도
                    parent = item.parent
                    price_el = parent.select_one(
                        ".item_money_box .item_price span"
                    )

                price = price_el.text.strip() if price_el else "N/A"

                # 데이터 저장
                product_list.append(
                    {"페이지": page, "브랜드": brand, "상품명": name, "가격": price}
                )

        else:
            print(
                f"❌ {page} 페이지 접속 실패 (상태코드: {response.status_code})"
            )

    except Exception as e:
        print(f"⚠️ 오류 발생 ({page} 페이지): {e}")

    # 서버 부하 방지를 위한 1초 대기
    time.sleep(1)

# 데이터프레임 변환
df = pd.DataFrame(product_list)

print("\n--- 수집 완료 ---")
print(f"총 수집된 상품 수: {len(df)}개")

# 결과 출력 (시각화/확인용)
print(df)

# 필요한 경우 엑셀이나 CSV로 저장하려면 아래 주석을 해제하세요.
# df.to_csv("lotte_hotel_vouchers.csv", index=False, encoding="utf-8-sig")

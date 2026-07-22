# python -m streamlit run app.py
# Windows CMD / PowerShell용 대체 명령어
# python -c "import importlib.metadata; open('requirements.txt', 'w', encoding='utf-8').write('\n'.join([f'{d.metadata[\"Name\"]}>={ \".\".join(d.version.split(\".\")[:2]) }' for d in importlib.metadata.distributions()]))"
import streamlit as st
import pandas as pd
from gspread_helper import get_spreadsheet
import time

# 페이지 기본 설정
st.set_page_config(
    page_title="롯데호텔 이용권 대시보드",
    page_icon="🏨",
    layout="wide"
)

st.title("🏨 롯데호텔 이용권 가격 및 상품 분석 대시보드")
st.markdown("구글 시트에 수집된 날짜별 데이터를 선택하여 실시간으로 시각화합니다.")

# 구글 시트 연결 및 탭 목록 가져오기 함수


@st.cache_data(ttl=60) # 1분간 저장하도록 
# 데이터 로딩 함수(예: 구글 시트 데이터를 불러오는 함수)의 결과를 캐싱(임시 저장)하여 앱의 속도를 빠르게 만들어 주는 데코레이터
# 60초가 지나면 캐시가 만료됩니다
def get_sheet_and_titles():
    try:
        spreadsheet_name = "스크래핑에서데이터저장시각화"
        spreadsheet = get_spreadsheet(spreadsheet_name)
        worksheets = spreadsheet.worksheets()
        sheet_titles = [ws.title for ws in worksheets]
        return spreadsheet, sheet_titles
    except Exception as e:
        return None, []

# 스프레드시트 객체와 탭 이름 목록 로드
spreadsheet, sheet_titles = get_sheet_and_titles()

if sheet_titles:
    # 📌 사이드바에서 수집된 탭(파일) 선택 기능 제공
    st.sidebar.header("⚙️ 데이터 선택")
    selected_sheet = st.sidebar.selectbox("수집 일시별 탭 선택", sheet_titles)
    
    # 선택한 탭의 데이터를 가져오는 함수
    @st.cache_data(ttl=600) #10분
    def load_data_from_sheet(sheet_title):
        for attempt in range(3):
            try:
                # 함수 내부에서 spreadsheet를 직접 참조하는 대신 새로 열거나 안전하게 가져옴
                # 만약 스프레드시트 이름("스크래핑에서데이터저장시각화")을 알고 있다면 아래처럼 안에서 바로 열어도 안전합니다.
                from gspread_helper import get_spreadsheet
                sp = get_spreadsheet("스크래핑에서데이터저장시각화")
                worksheet = sp.worksheet(sheet_title)
                data = worksheet.get_all_records()
                return pd.DataFrame(data)
            except Exception as e:
                if attempt == 2:
                    st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
                    return pd.DataFrame()
                time.sleep(1)

    df = load_data_from_sheet(selected_sheet)

    if not df.empty:
        # 데이터 전처리: '가격' 문자열을 숫자(int)로 변환
        if "가격" in df.columns:
            df["가격_숫자"] = df["가격"].astype(str).str.replace(r"[^\d]", "", regex=True)
            df["가격_숫자"] = pd.to_numeric(df["가격_숫자"], errors="coerce").fillna(0)

        # 1. 상단 핵심 지표(Metric) 카드 레이아웃
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(label="총 수집 상품 수", value=f"{len(df):,}개")
        with col2:
            if "가격_숫자" in df.columns and len(df) > 0:
                avg_price = df["가격_숫자"].mean()
                st.metric(label="평균 상품 가격", value=f"{int(avg_price):,}원")
        with col3:
            brand_count = df["브랜드"].nunique() if "브랜드" in df.columns else 0
            st.metric(label="등록된 브랜드 수", value=f"{brand_count}개")

        st.markdown("---")

        # 2. 필터 및 검색 기능
        st.subheader("🔍 상품 상세 필터")
        search_query = st.text_input("상품명 검색", placeholder="예: 상품명을 입력하세요...")
        
        filtered_df = df.copy()
        if search_query:
            filtered_df = filtered_df[filtered_df["상품명"].str.contains(search_query, na=False)]

        # 3. 시각화 영역 (바 차트)
        if "브랜드" in df.columns and "가격_숫자" in df.columns:
            st.subheader(f"📊 [{selected_sheet}] 브랜드별 평균 가격 비교")
            brand_price_avg = df.groupby("브랜드")["가격_숫자"].mean().reset_index()
            st.bar_chart(brand_price_avg.set_index("브랜드"))

        # 4. 데이터 테이블 출력
        st.subheader("📋 전체 수집 데이터 원본")
        st.dataframe(filtered_df, width="stretch")

    else:
        st.warning(f"'{selected_sheet}' 탭에 데이터가 비어 있습니다.")
else:
    st.error("구글 시트를 찾을 수 없거나 연결에 실패했습니다. 시트 이름과 Secrets 설정을 확인해주세요.")
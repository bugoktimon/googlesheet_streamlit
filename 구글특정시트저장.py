# pip install gspread google-auth pandas
# 구글콘솔로 접속한다.
# 구글 클라우드 콘솔(Google Cloud Console)에 로그인한 뒤 
# 가장 먼저 프로젝트를 생성해야만 
# 서비스 계정 = "가상의 비서(로봇)", 
# API 활성화 (2가지 켜기) - "Google Drive API", "Google Sheets API"
# 서비스 계정만들기 거기 이메일 주소 복붙해두기(사용자인증정보만들기)
# greenpython610@greenpython610.iam.gserviceaccount.com
# 구글 시트 연동에 필요한 API를 켜고 비밀 키(JSON)를 발급

# data 폴더 내의 CSV 파일들을 지정한 구글 시트에 파일명과 
# 동일한 이름의 탭으로 자동 생성하고 벌크(Bulk) 저장


import os
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

# ==========================================
# ⚙️ 사용자 설정 영역
# ==========================================
# 1. 구글 인증 키 파일 경로 (콘솔에서 다운로드한 JSON 파일)
CREDENTIALS_FILE = "key/credentials.json"

# 2. 데이터를 저장할 실제 구글 스프레드시트의 정확한 이름
# (예: '롯데호텔_수집_대시보드')
TARGET_SPREADSHEET_NAME = "웹스크래핑데이터저장시트"

# 3. CSV 파일들이 들어있는 폴더 경로
FOLDER_PATH = "data"
# ==========================================


def get_gspread_client(cred_file):
    """구글 API 인증을 처리하고 gspread 클라이언트를 반환합니다."""
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = Credentials.from_service_account_file(cred_file, scopes=scopes)
    return gspread.authorize(creds)


def upload_csv_to_sheets():
    # 1. 'data' 폴더 존재 여부 확인
    if not os.path.exists(FOLDER_PATH):
        print(f"❌ '{FOLDER_PATH}' 폴더가 존재하지 않습니다. 크롤링을 먼저 진행해주세요.")
        return

    # 2. 폴더 내의 CSV 파일 목록 가져오기
    csv_files = [f for f in os.listdir(FOLDER_PATH) if f.endswith(".csv")]
    if not csv_files:
        print(f"❌ '{FOLDER_PATH}' 폴더 내에 저장된 CSV 파일이 없습니다.")
        return

    print(f"📁 총 {len(csv_files)}개의 CSV 파일을 발견했습니다: {csv_files}")

    try:
        # 3. 구글 시트 접속
        gc = get_gspread_client(CREDENTIALS_FILE)
        spreadsheet = gc.open(TARGET_SPREADSHEET_NAME)
        print(f"🎯 구글 시트 연결 성공: '{TARGET_SPREADSHEET_NAME}'")

        # 4. 각 CSV 파일별로 루프를 돌며 업로드 진행
        for csv_file in csv_files:
            file_path = f"{FOLDER_PATH}/{csv_file}"
            
            # 확장자(.csv)를 제외한 순수한 파일명을 탭 이름으로 지정
            sheet_title = os.path.splitext(csv_file)[0]
            print(f"\n⏳ '{csv_file}' ➡️ 구글 시트 탭 '{sheet_title}' 업로드 시작...")

            # CSV 파일 열기 (한글 깨짐 방지 utf-8-sig)
            df = pd.read_csv(file_path, encoding="utf-8-sig")
            # 결측치(NaN)가 있으면 빈 칸("")으로 치환하여 전송 에러 예방
            df = df.fillna("")

            # pandas 데이터프레임을 구글 시트용 2차원 리스트 형식으로 변환
            # (첫 행은 열 헤더명, 두 번째 행부터는 데이터들)
            all_data = [df.columns.values.tolist()] + df.values.tolist()

            try:
                # 동일한 이름의 탭이 이미 존재하는지 확인
                worksheet = spreadsheet.worksheet(sheet_title)
                # 존재한다면 기존 데이터 전부 초기화
                worksheet.clear()
                print(f"ℹ️ 기존 '{sheet_title}' 탭이 존재하여 내용을 초기화(덮어쓰기)했습니다.")
            except gspread.exceptions.WorksheetNotFound:
                # 존재하지 않는다면 신규 탭 생성 (데이터 크기에 알맞은 행/열 지정)
                worksheet = spreadsheet.add_worksheet(
                    title=sheet_title, rows=len(all_data), cols=len(df.columns)
                )
                print(f"✨ 새로운 탭 '{sheet_title}'을 생성했습니다.")

            # 🔥 전체 데이터를 1번의 API 호출로 단숨에 입력 (할당량 제한 극복 및 드롭 방지)
            worksheet.update("A1", all_data)
            print(f"✅ '{sheet_title}' 탭에 {len(df)}개의 데이터 저장 완료!")

        print("\n🎉 모든 CSV 파일이 구글 시트에 완벽하게 저장되었습니다!")

    except gspread.exceptions.SpreadsheetNotFound:
        print(f"❌ '{TARGET_SPREADSHEET_NAME}' 이라는 이름의 구글 시트를 찾을 수 없습니다.")
        print("📍 [체크리스트]")
        print(" 1. 구글 시트의 이름이 오타 없이 정확한지 확인하세요.")
        print(" 2. 실제 구글 시트 우측 상단 '공유' 버튼을 눌러, credentials.json 내부의 서비스 계정 이메일(client_email)을 '편집자'로 추가했는지 꼭 확인하세요.")
    except Exception as e:
        print(f"❌ 오류 발생: {e}")


if __name__ == "__main__":
    upload_csv_to_sheets()
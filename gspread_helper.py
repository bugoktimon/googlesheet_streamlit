import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

@st.cache_resource(ttl=600)
def get_gspread_client(cred_file="key/credentials.json"):
    """로컬 및 Streamlit Cloud 환경을 모두 지원하는 구글 인증 클라이언트"""
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    
    # Streamlit Cloud의 Secrets에 설정되어 있는 경우 (배포 환경)
    if "gcp_service_account" in st.secrets:
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        return gspread.authorize(creds)
    
    # 로컬 환경인 경우 (JSON 파일 사용)
    creds = Credentials.from_service_account_file(cred_file, scopes=scopes)
    return gspread.authorize(creds)

def get_spreadsheet(spreadsheet_name, cred_file="key/credentials.json"):
    gc = get_gspread_client(cred_file)
    return gc.open(spreadsheet_name)
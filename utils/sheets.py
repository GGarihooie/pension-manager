import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import streamlit as st

COLUMNS = [
    '연도', '성함', '전화번호', '예약 월', '예약 일자',
    '숙박 월', '숙박 일자', '숙박 일수', '퇴실 일자',
    '인원수', '어른 인원수', '아이 인원수', '추가 인원수',
    '바비큐 1', '불멍', '바비큐+불멍', '수영장 사용', '리뷰이벤트',
    '금액', '비고', '캘린더ID'
]

SERVICE_COLS = ['바비큐 1', '불멍', '바비큐+불멍', '수영장 사용', '리뷰이벤트']
SERVICE_NAMES = ['바비큐', '불멍', '바비큐+불멍', '수영장', '리뷰이벤트']


@st.cache_resource
def get_client():
    scopes = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=scopes
    )
    return gspread.Client(auth=creds)


def get_sheet():
    client = get_client()
    return client.open_by_url(st.secrets["sheet_url"]).sheet1


def load_data():
    sheet = get_sheet()
    records = sheet.get_all_records()
    if not records:
        return pd.DataFrame(columns=COLUMNS)
    df = pd.DataFrame(records)

    # 실제 시트 행 번호 기록 (헤더=1행, 데이터 시작=2행)
    df['_sheet_row'] = range(2, len(df) + 2)

    if '금액' in df.columns:
        df['금액'] = pd.to_numeric(
            df['금액'].astype(str).str.replace(',', '').str.replace('₩', ''),
            errors='coerce'
        ).fillna(0)
    numeric_cols = ['연도', '숙박 일수', '인원수', '어른 인원수', '아이 인원수', '추가 인원수',
                    '예약 월', '숙박 월']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    int_cols = ['연도', '예약 월', '숙박 월']
    for col in int_cols:
        if col in df.columns:
            df[col] = df[col].astype(int)

    # 빈 행 제거 (연도가 0이거나 성함이 비어있는 행)
    if '연도' in df.columns:
        df = df[df['연도'] > 0]
    if '성함' in df.columns:
        df = df[df['성함'].astype(str).str.strip() != '']

    df = df.reset_index(drop=True)
    return df


def is_checked(value):
    return str(value).strip().upper() in ['O', 'Y', 'YES', '예', 'TRUE', '1', '✓', 'V']


def add_row(row_data):
    sheet = get_sheet()
    # No 컬럼 자동 채우기 (기존 데이터 수 + 1)
    all_records = sheet.get_all_records()
    next_no = len(all_records) + 1
    sheet.append_row([next_no] + row_data, value_input_option='USER_ENTERED')


def update_row(sheet_row_index, row_data):
    """sheet_row_index: 1-based (1=헤더, 2=첫번째 데이터)
    No 컬럼(A열)은 건드리지 않고 B열부터 업데이트"""
    sheet = get_sheet()
    col_end = chr(ord('B') + len(row_data) - 1)
    sheet.update([row_data], f'B{sheet_row_index}:{col_end}{sheet_row_index}')


def delete_row(sheet_row_index):
    """sheet_row_index: 1-based"""
    sheet = get_sheet()
    sheet.delete_rows(sheet_row_index)

from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
import streamlit as st
import pandas as pd

CALENDAR_ID = "263d65a20eca6fde95edc2631d7c75aee874715603032eacb82aa37c98970122@group.calendar.google.com"

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/calendar',
]


def get_calendar_service():
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=SCOPES
    )
    return build('calendar', 'v3', credentials=creds)


def normalize_date(date_str):
    s = str(date_str).strip()
    if not s or s in ['0', 'nan', '']:
        return None
    parts = s.replace('/', '-').split('-')
    if len(parts) == 3 and len(parts[0]) == 2:
        s = '20' + s
    result = pd.to_datetime(s, errors='coerce')
    return result if not pd.isna(result) else None


def is_checked(value):
    return str(value).strip().upper() in ['O', 'Y', 'YES', '예', 'TRUE', '1']


def add_calendar_event(name, phone, adults, children, bbq, bonfire, bbq_bonfire, pool, review, stay_date_str, notes=''):
    try:
        service = get_calendar_service()

        date = normalize_date(stay_date_str)
        if date is None:
            return False, "숙박 일자를 파싱할 수 없습니다."

        date_str = date.strftime('%Y-%m-%d')

        # 제목
        title = f"{name} (성인 {int(adults)}명 / 아이 {int(children)}명)"

        # 체크된 서비스만 표시
        services = []
        if is_checked(bbq):
            services.append("🍖 바비큐")
        if is_checked(bonfire):
            services.append("🔥 불멍")
        if is_checked(bbq_bonfire):
            services.append("🍖🔥 바비큐+불멍")
        if is_checked(pool):
            services.append("🏊 수영장")
        if is_checked(review):
            services.append("⭐ 리뷰이벤트")

        description = (
            f"📞 전화번호: {phone}\n"
            f"👨‍👩‍👧 성인: {int(adults)}명 / 아이: {int(children)}명"
        )
        if services:
            description += "\n\n" + " / ".join(services)
        if notes and str(notes).strip() and str(notes).strip() != 'nan':
            description += f"\n\n📝 비고: {str(notes).strip()}"

        event = {
            'summary': title,
            'description': description,
            'start': {'date': date_str},
            'end': {'date': date_str},
        }

        result = service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
        event_id = result.get('id', '')
        return True, event_id

    except Exception as e:
        return False, str(e)


def delete_calendar_event(event_id):
    try:
        if not event_id or str(event_id).strip() in ['', 'nan']:
            return False, "캘린더ID 없음"
        service = get_calendar_service()
        service.events().delete(calendarId=CALENDAR_ID, eventId=str(event_id).strip()).execute()
        return True, "캘린더 삭제 완료"
    except Exception as e:
        return False, str(e)

import streamlit as st
import pandas as pd
from datetime import datetime
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.sheets import load_data, add_row, update_row, delete_row, COLUMNS, is_checked
from utils.calendar_utils import add_calendar_event, delete_calendar_event

st.set_page_config(page_title="예약 관리", page_icon="📋", layout="wide")

col_title, col_btn = st.columns([5, 1])
with col_title:
    st.title("📋 예약 관리")
with col_btn:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔄 새로고침", use_container_width=True):
        st.rerun()

tab1, tab2 = st.tabs(["📋 예약 목록 / 수정 / 삭제", "➕ 새 예약 추가"])

# ═══════════════════════════════════════════════════════════
# TAB 1: 예약 목록
# ═══════════════════════════════════════════════════════════
with tab1:
    with st.spinner("데이터 불러오는 중..."):
        df = load_data()

    if df.empty:
        st.warning("등록된 예약이 없습니다. '새 예약 추가' 탭에서 추가해주세요.")
    else:
        # ── 필터 ──
        col1, col2, col3 = st.columns(3)
        with col1:
            years = ["전체"] + sorted(df['연도'].astype(str).unique().tolist(), reverse=True)
            year_filter = st.selectbox("연도", years)
        with col2:
            months = ["전체"] + [str(m) for m in range(1, 13)]
            month_filter = st.selectbox("숙박 월", months)
        with col3:
            search_name = st.text_input("성함 검색", placeholder="이름 입력...")

        filtered = df.copy()
        if year_filter != "전체":
            filtered = filtered[filtered['연도'].astype(str) == year_filter]
        if month_filter != "전체":
            filtered = filtered[filtered['숙박 월'].astype(str) == month_filter]
        if search_name:
            filtered = filtered[filtered['성함'].astype(str).str.contains(search_name, na=False)]

        st.markdown(f"**총 {len(filtered)}건**")

        display_cols = ['연도', '예약 월', '예약 일자', '숙박 월', '숙박 일자', '퇴실 일자', '성함', '전화번호',
                        '인원수', '숙박 일수', '바비큐 1', '불멍', '바비큐+불멍',
                        '수영장 사용', '리뷰이벤트', '금액', '비고']
        display_cols = [c for c in display_cols if c in filtered.columns]

        st.dataframe(
            filtered[display_cols].style.format({'금액': '₩{:,.0f}'}),
            use_container_width=True,
            height=300
        )

        # ── 수정 / 삭제 ──
        st.divider()
        st.subheader("예약 수정 / 삭제")

        if filtered.empty:
            st.info("필터 조건에 해당하는 예약이 없습니다.")
        else:
            # 이름 검색으로 빠르게 좁히기
            edit_search = st.text_input("🔍 이름으로 검색", placeholder="성함 입력...", key="edit_search")
            edit_df = filtered[filtered['성함'].astype(str).str.contains(edit_search, na=False)] if edit_search else filtered

            if edit_df.empty:
                st.warning("검색 결과가 없습니다.")
                st.stop()

            options = []
            for df_idx, row in edit_df.iterrows():
                label = (f"{row.get('연도', '')}년 "
                         f"{row.get('숙박 월', '')}월 "
                         f"{row.get('숙박 일자', '')} - "
                         f"{row.get('성함', '')} "
                         f"({int(row.get('금액', 0)):,}원)")
                options.append((label, df_idx))

            selected_label = st.selectbox(f"예약 선택 ({len(options)}건)", [o[0] for o in options])
            selected_df_idx = next(o[1] for o in options if o[0] == selected_label)
            selected_row = df.loc[selected_df_idx]
            sheet_row = int(selected_row['_sheet_row'])

            action = st.radio("작업 선택", ["수정", "삭제"], horizontal=True)

            if action == "수정":
                from datetime import timedelta

                def parse_to_date(val):
                    try:
                        s = str(val).strip()
                        if not s or s in ['0', 'nan', '']:
                            return datetime.now().date()
                        parts = s.replace('/', '-').split('-')
                        if len(parts) == 3 and len(parts[0]) == 2:
                            s = '20' + s
                        result = pd.to_datetime(s, errors='coerce')
                        return result.date() if not pd.isna(result) else datetime.now().date()
                    except:
                        return datetime.now().date()

                st.markdown("**예약 정보 수정**")
                col1, col2 = st.columns(2)
                with col1:
                    e_name = st.text_input("성함", value=str(selected_row.get('성함', '')), key="e_name")
                    e_phone = st.text_input("전화번호", value=str(selected_row.get('전화번호', '')), key="e_phone")
                    e_res_date = st.date_input("예약 일자", value=parse_to_date(selected_row.get('예약 일자', '')), key="e_res_date")
                with col2:
                    e_stay_date = st.date_input("숙박 일자", value=parse_to_date(selected_row.get('숙박 일자', '')), key="e_stay_date")
                    e_nights = st.number_input("숙박 일수", 1, 30, int(selected_row.get('숙박 일수', 1)), key="e_nights")
                    e_checkout = e_stay_date + timedelta(days=int(e_nights))
                    st.success(f"퇴실 일자: **{e_checkout.strftime('%Y-%m-%d')}** (자동계산)")

                col3, col4 = st.columns(2)
                with col3:
                    e_total = st.number_input("인원수(총)", 1, 50, int(selected_row.get('인원수', 2)), key="e_total")
                    e_adults = st.number_input("어른 인원수", 0, 50, int(selected_row.get('어른 인원수', 2)), key="e_adults")
                    e_children = st.number_input("아이 인원수", 0, 50, int(selected_row.get('아이 인원수', 0)), key="e_children")
                    e_extra = max(0, e_total - 2)
                    st.info(f"추가 인원수: **{e_extra}명** (자동계산: 총 인원 - 2)")
                with col4:
                    e_bbq = st.checkbox("바비큐 1", value=is_checked(selected_row.get('바비큐 1', '')), key="e_bbq")
                    e_bonfire = st.checkbox("불멍", value=is_checked(selected_row.get('불멍', '')), key="e_bonfire")
                    e_bbq_bonfire = st.checkbox("바비큐+불멍", value=is_checked(selected_row.get('바비큐+불멍', '')), key="e_bbq_bonfire")
                    e_pool = st.checkbox("수영장 사용", value=is_checked(selected_row.get('수영장 사용', '')), key="e_pool")
                    e_review = st.checkbox("리뷰이벤트", value=is_checked(selected_row.get('리뷰이벤트', '')), key="e_review")

                e_amount = st.number_input("금액(원)", 0, 99999999, int(selected_row.get('금액', 0)), step=10000, key="e_amount")
                e_notes = st.text_area("비고", value=str(selected_row.get('비고', '')), key="e_notes")

                if st.button("✅ 수정 저장", type="primary", use_container_width=True):
                    row_data = [
                        e_res_date.year, e_name, e_phone,
                        e_res_date.month, e_res_date.strftime('%Y-%m-%d'),
                        e_stay_date.month, e_stay_date.strftime('%Y-%m-%d'),
                        e_nights, e_checkout.strftime('%Y-%m-%d'),
                        e_total, e_adults, e_children, e_extra,
                        'O' if e_bbq else 'X',
                        'O' if e_bonfire else 'X',
                        'O' if e_bbq_bonfire else 'X',
                        'O' if e_pool else 'X',
                        'O' if e_review else 'X',
                        e_amount, e_notes
                    ]
                    update_row(sheet_row, row_data)
                    st.success(f"✅ {e_name} 님 예약이 수정되었습니다!")
                    st.rerun()

            else:  # 삭제
                st.warning(f"**{selected_row.get('성함', '')}** 님 ({selected_row.get('숙박 월', '')}월 {selected_row.get('숙박 일자', '')}일) 예약을 삭제하시겠습니까?")
                col_yes, col_no, _ = st.columns([1, 1, 3])
                with col_yes:
                    if st.button("🗑️ 삭제 확인", type="primary"):
                        # 캘린더 이벤트 먼저 삭제
                        cal_event_id = selected_row.get('캘린더ID', '')
                        cal_ok, cal_msg = delete_calendar_event(cal_event_id)
                        delete_row(sheet_row)
                        if cal_ok:
                            st.success("삭제되었습니다. 📅 캘린더에서도 삭제됐어요!")
                        else:
                            st.success("삭제되었습니다.")
                        st.rerun()
                with col_no:
                    if st.button("취소"):
                        st.rerun()

# ═══════════════════════════════════════════════════════════
# TAB 2: 새 예약 추가
# ═══════════════════════════════════════════════════════════
with tab2:
    from datetime import timedelta
    st.subheader("새 예약 추가")
    now = datetime.now()

    col1, col2 = st.columns(2)
    with col1:
        a_name = st.text_input("성함 *", placeholder="홍길동", key="a_name")
        a_phone = st.text_input("전화번호 *", placeholder="010-0000-0000", key="a_phone")
        a_res_date = st.date_input("예약 일자", value=now.date(), key="a_res_date")

    with col2:
        a_stay_date = st.date_input("숙박 일자", value=now.date(), key="a_stay_date")
        a_nights = st.number_input("숙박 일수", 1, 30, 1, key="a_nights")
        a_checkout = a_stay_date + timedelta(days=int(a_nights))
        st.success(f"퇴실 일자: **{a_checkout.strftime('%Y-%m-%d')}** (자동계산)")

    st.divider()
    col3, col4 = st.columns(2)
    with col3:
        a_total = st.number_input("인원수(총)", 1, 50, 2, key="a_total")
        a_adults = st.number_input("어른 인원수", 0, 50, 2, key="a_adults")
        a_children = st.number_input("아이 인원수", 0, 50, 0, key="a_children")
        a_extra = max(0, a_total - 2)
        st.info(f"추가 인원수: **{a_extra}명** (자동계산: 총 인원 - 2)")

    with col4:
        st.markdown("**추가 서비스**")
        a_bbq = st.checkbox("바비큐 1", key="a_bbq")
        a_bonfire = st.checkbox("불멍", key="a_bonfire")
        a_bbq_bonfire = st.checkbox("바비큐+불멍", key="a_bbq_bonfire")
        a_pool = st.checkbox("수영장 사용", key="a_pool")
        a_review = st.checkbox("리뷰이벤트", key="a_review")

    st.divider()
    a_amount = st.number_input("금액(원)", 0, 99999999, 0, step=10000, key="a_amount")
    a_notes = st.text_area("비고", placeholder="특이사항 입력...", key="a_notes")

    if st.button("✅ 예약 추가", type="primary", use_container_width=True):
        if not a_name.strip():
            st.error("성함을 입력해주세요.")
        elif not a_phone.strip():
            st.error("전화번호를 입력해주세요.")
        else:
            year = a_res_date.year
            res_month = a_res_date.month
            res_date = a_res_date.strftime('%Y-%m-%d')
            stay_month = a_stay_date.month
            stay_date = a_stay_date.strftime('%Y-%m-%d')
            checkout = a_checkout.strftime('%Y-%m-%d')

            # 구글 캘린더 자동 등록 (먼저 실행해서 event_id 획득)
            cal_ok, cal_msg = add_calendar_event(
                name=a_name,
                phone=a_phone,
                adults=a_adults,
                children=a_children,
                bbq='O' if a_bbq else 'X',
                bonfire='O' if a_bonfire else 'X',
                bbq_bonfire='O' if a_bbq_bonfire else 'X',
                pool='O' if a_pool else 'X',
                review='O' if a_review else 'X',
                stay_date_str=stay_date,
                notes=a_notes
            )
            calendar_event_id = cal_msg if cal_ok else ''

            row_data = [
                year, a_name.strip(), a_phone,
                res_month, res_date,
                stay_month, stay_date, a_nights, checkout,
                a_total, a_adults, a_children, a_extra,
                'O' if a_bbq else 'X',
                'O' if a_bonfire else 'X',
                'O' if a_bbq_bonfire else 'X',
                'O' if a_pool else 'X',
                'O' if a_review else 'X',
                a_amount, a_notes, calendar_event_id
            ]
            add_row(row_data)

            if cal_ok:
                st.success(f"✅ {a_name} 님 예약이 추가되었습니다! 📅 캘린더에도 등록됐어요!")
            else:
                st.success(f"✅ {a_name} 님 예약이 추가되었습니다!")
                st.warning(f"캘린더 등록 실패: {cal_msg}")
            st.balloons()

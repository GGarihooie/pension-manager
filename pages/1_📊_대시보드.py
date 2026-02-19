import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.sheets import load_data, SERVICE_COLS, SERVICE_NAMES, is_checked

st.set_page_config(page_title="대시보드", page_icon="📊", layout="wide")

col_title, col_btn = st.columns([5, 1])
with col_title:
    st.title("📊 대시보드")
with col_btn:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔄 새로고침", use_container_width=True):
        st.rerun()

with st.spinner("데이터 불러오는 중..."):
    df = load_data()

if df.empty:
    st.warning("데이터가 없습니다. 예약관리 메뉴에서 예약을 추가해주세요.")
    st.stop()

now = datetime.now()
current_year = now.year
current_month = now.month

df_year = df[df['연도'] == current_year]
df_month = df_year[df_year['숙박 월'] == current_month]

prev_month = current_month - 1 if current_month > 1 else 12
prev_year = current_year if current_month > 1 else current_year - 1
df_prev = df[(df['연도'] == prev_year) & (df['숙박 월'] == prev_month)]

# ── 예약 리드타임 계산 (예약일 ~ 숙박일 평균 차이) ──────────
def normalize_date(date_str):
    s = str(date_str).strip()
    if not s or s in ['0', 'nan', '']:
        return None
    parts = s.replace('/', '-').split('-')
    if len(parts) == 3 and len(parts[0]) == 2:
        s = '20' + s
    return pd.to_datetime(s, errors='coerce')

def calc_lead_time(row):
    try:
        book_date = normalize_date(row['예약 일자'])
        stay_date = normalize_date(row['숙박 일자'])
        if book_date is None or stay_date is None:
            return None
        diff = (stay_date - book_date).days
        return diff if diff >= 0 else None
    except:
        return None

if all(c in df_year.columns for c in ['예약 일자', '숙박 일자']):
    df_year = df_year.copy()
    df_year['리드타임'] = df_year.apply(calc_lead_time, axis=1)
    avg_lead = df_year['리드타임'].dropna().mean()

    with st.expander("🔍 리드타임 계산 내역 확인"):
        debug_df = df_year[['성함', '예약 일자', '숙박 일자', '리드타임']].dropna(subset=['리드타임'])
        st.dataframe(debug_df, use_container_width=True)
else:
    avg_lead = None

# ── KPI 1행: 매출/예약 현황 ────────────────────────────────
st.subheader("매출 현황")
col1, col2, col3, col4 = st.columns(4)

with col1:
    monthly_revenue = df_month['금액'].sum()
    delta = monthly_revenue - df_prev['금액'].sum()
    st.metric("이번 달 매출", f"₩{monthly_revenue:,.0f}", f"₩{delta:+,.0f}")

with col2:
    monthly_res = len(df_month)
    prev_res = len(df_prev)
    st.metric("이번 달 예약 수", f"{monthly_res}건", f"{monthly_res - prev_res:+d}건")

with col3:
    yearly_revenue = df_year['금액'].sum()
    st.metric("올해 총 매출", f"₩{yearly_revenue:,.0f}")

with col4:
    yearly_res = len(df_year)
    st.metric("올해 총 예약 수", f"{yearly_res}건")

# ── KPI 2행: 인원/평균 통계 ────────────────────────────────
st.subheader("인원 및 평균 통계")
col1, col2, col3, col4 = st.columns(4)

with col1:
    avg_guests = df_year['인원수'].mean() if '인원수' in df_year.columns and len(df_year) > 0 else 0
    st.metric("건당 평균 인원수", f"{avg_guests:.1f}명")

with col2:
    avg_amount = df_year['금액'].mean() if len(df_year) > 0 else 0
    st.metric("건당 평균 금액", f"₩{avg_amount:,.0f}")

with col3:
    if '어른 인원수' in df_year.columns and '아이 인원수' in df_year.columns:
        total_adults = df_year['어른 인원수'].sum()
        total_children = df_year['아이 인원수'].sum()
        total_people = total_adults + total_children
        if total_people > 0:
            adult_ratio = total_adults / total_people * 100
            child_ratio = total_children / total_people * 100
            st.metric("어른/아이 비율", f"{adult_ratio:.0f}% / {child_ratio:.0f}%")
        else:
            st.metric("어른/아이 비율", "데이터 없음")
    else:
        st.metric("어른/아이 비율", "데이터 없음")

with col4:
    if avg_lead is not None and not pd.isna(avg_lead):
        st.metric("평균 예약 리드타임", f"{avg_lead:.0f}일 전")
    else:
        st.metric("평균 예약 리드타임", "데이터 없음")

st.divider()

# ── 그래프 1행: 월별 매출 + 서비스 이용 ──────────────────────
col1, col2 = st.columns(2)

with col1:
    all_years = sorted(df['연도'].unique().tolist(), reverse=True)
    sel_col, _ = st.columns([1, 2])
    with sel_col:
        chart_year = st.selectbox("연도 선택", all_years, index=0, key="chart_year")
    df_chart = df[df['연도'] == chart_year]

    st.subheader(f"{chart_year}년 월별 매출")
    all_months = pd.DataFrame({'숙박 월': range(1, 13)})
    monthly = df_chart.groupby('숙박 월')['금액'].sum().reset_index()
    monthly = all_months.merge(monthly, on='숙박 월', how='left').fillna(0)
    monthly['월_표시'] = monthly['숙박 월'].astype(int).astype(str) + '월'

    fig = px.bar(monthly, x='월_표시', y='금액', text='금액',
                 color_discrete_sequence=['#FF6B6B'])
    fig.update_traces(texttemplate='₩%{text:,.0f}', textposition='outside')
    fig.update_layout(showlegend=False, xaxis_title='', yaxis_title='매출(원)', height=320)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader(f"{chart_year}년 추가 서비스 이용 현황")
    counts = []
    for col in SERVICE_COLS:
        count = df_chart[col].apply(is_checked).sum() if col in df_chart.columns else 0
        counts.append(count)

    service_df = pd.DataFrame({'서비스': SERVICE_NAMES, '이용횟수': counts})
    service_df = service_df[service_df['이용횟수'] > 0]

    if not service_df.empty:
        fig2 = px.pie(service_df, names='서비스', values='이용횟수',
                      color_discrete_sequence=px.colors.qualitative.Pastel, hole=0.4)
        fig2.update_layout(height=320)
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("서비스 이용 데이터가 없습니다.")

# ── 그래프 2행: 월별 평균 인원수 + 어른/아이/추가 누적 ──────
col1, col2 = st.columns(2)

with col1:
    st.subheader(f"{chart_year}년 월별 평균 인원수")
    if '인원수' in df_chart.columns:
        all_months = pd.DataFrame({'숙박 월': range(1, 13)})
        monthly_guests = df_chart.groupby('숙박 월')['인원수'].mean().reset_index()
        monthly_guests = all_months.merge(monthly_guests, on='숙박 월', how='left').fillna(0)
        monthly_guests['월_표시'] = monthly_guests['숙박 월'].astype(int).astype(str) + '월'

        fig3 = px.line(monthly_guests, x='월_표시', y='인원수',
                       markers=True, color_discrete_sequence=['#4ECDC4'],
                       labels={'인원수': '평균 인원수'})
        fig3.update_layout(xaxis_title='', yaxis_title='평균 인원수(명)', height=320)
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.info("인원수 데이터가 없습니다.")

with col2:
    st.subheader(f"{chart_year}년 어른 / 아이 / 추가인원")
    needed = ['어른 인원수', '아이 인원수', '추가 인원수']
    if all(c in df_chart.columns for c in needed):
        all_months = pd.DataFrame({'숙박 월': range(1, 13)})
        stacked = df_chart.groupby('숙박 월')[needed].sum().reset_index()
        stacked = all_months.merge(stacked, on='숙박 월', how='left').fillna(0)
        stacked['월_표시'] = stacked['숙박 월'].astype(int).astype(str) + '월'

        fig4 = go.Figure()
        colors = {'어른 인원수': '#45B7D1', '아이 인원수': '#FF6B6B', '추가 인원수': '#96CEB4'}
        labels = {'어른 인원수': '어른', '아이 인원수': '아이', '추가 인원수': '추가인원'}
        for col in needed:
            fig4.add_trace(go.Bar(
                x=stacked['월_표시'], y=stacked[col],
                name=labels[col], marker_color=colors[col]
            ))
        fig4.update_layout(barmode='stack', xaxis_title='', yaxis_title='인원수(명)',
                           height=320, legend=dict(orientation='h', yanchor='bottom', y=1.02))
        st.plotly_chart(fig4, use_container_width=True)
    else:
        st.info("인원 상세 데이터가 없습니다.")

st.divider()

# ── 서비스 통계 표 ─────────────────────────────────────────
st.subheader(f"{chart_year}년 서비스 이용 통계")
total = len(df_chart)
stats = []
for col, name in zip(SERVICE_COLS, SERVICE_NAMES):
    if col in df_chart.columns and total > 0:
        count = int(df_chart[col].apply(is_checked).sum())
        rate = round(count / total * 100, 1)
        stats.append({'서비스': name, '이용 횟수': f"{count}건", '이용률': f"{rate}%"})

if stats:
    stats_df = pd.DataFrame(stats)
    st.dataframe(stats_df, use_container_width=True, hide_index=True)

st.divider()

# ── 최근 예약 내역 ─────────────────────────────────────────
col_title, col_slider = st.columns([3, 1])
with col_title:
    st.subheader("최근 예약 내역")
with col_slider:
    show_count = st.slider("표시 건수", min_value=5, max_value=50, value=10, step=5)

display_cols = ['연도', '숙박 월', '숙박 일자', '성함', '인원수', '숙박 일수', '금액']
display_cols = [c for c in display_cols if c in df.columns]
recent = df.tail(show_count).iloc[::-1].reset_index(drop=True)

st.dataframe(
    recent[display_cols].style.format({'금액': '₩{:,.0f}'}),
    use_container_width=True
)

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.sheets import load_data, SERVICE_COLS, SERVICE_NAMES, is_checked

st.set_page_config(page_title="매출 분석", page_icon="📈", layout="wide")

col_title, col_btn = st.columns([5, 1])
with col_title:
    st.title("📈 매출 분석")
with col_btn:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔄 새로고침", use_container_width=True):
        st.rerun()

with st.spinner("데이터 불러오는 중..."):
    df = load_data()

if df.empty:
    st.warning("데이터가 없습니다.")
    st.stop()

# ── 연도 선택 ──────────────────────────────────────────────
years = sorted(df['연도'].astype(str).unique().tolist(), reverse=True)
selected_year = st.selectbox("분석 연도", years)
df_year = df[df['연도'].astype(str) == selected_year]

st.divider()

# ── KPI ───────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("연간 매출", f"₩{df_year['금액'].sum():,.0f}")
with col2:
    st.metric("총 예약 수", f"{len(df_year)}건")
with col3:
    avg = df_year['금액'].mean() if len(df_year) > 0 else 0
    st.metric("평균 예약 금액", f"₩{avg:,.0f}")
with col4:
    total_nights = df_year['숙박 일수'].sum() if '숙박 일수' in df_year.columns else 0
    st.metric("총 숙박 일수", f"{int(total_nights)}박")

st.divider()

# ── 월별 매출 + 예약수 복합 차트 ──────────────────────────
st.subheader(f"{selected_year}년 월별 매출 추이")

all_months = pd.DataFrame({'숙박 월': range(1, 13)})
monthly = df_year.groupby('숙박 월').agg(
    매출=('금액', 'sum'),
    예약수=('금액', 'count')
).reset_index()
monthly = all_months.merge(monthly, on='숙박 월', how='left').fillna(0)
monthly['월_표시'] = monthly['숙박 월'].astype(int).astype(str) + '월'

fig = go.Figure()
fig.add_trace(go.Bar(
    x=monthly['월_표시'], y=monthly['매출'],
    name='매출(원)', marker_color='#FF6B6B',
    text=monthly['매출'].apply(lambda x: f'₩{x:,.0f}' if x > 0 else ''),
    textposition='outside', yaxis='y1'
))
fig.add_trace(go.Scatter(
    x=monthly['월_표시'], y=monthly['예약수'],
    name='예약수', line=dict(color='#4ECDC4', width=2),
    mode='lines+markers', yaxis='y2'
))
fig.update_layout(
    yaxis=dict(title='매출(원)', showgrid=False),
    yaxis2=dict(title='예약수', overlaying='y', side='right'),
    legend=dict(orientation='h', yanchor='bottom', y=1.02),
    hovermode='x unified',
    height=400
)
st.plotly_chart(fig, use_container_width=True)

st.divider()

col1, col2 = st.columns(2)

with col1:
    # ── 연도별 매출 비교 ──
    st.subheader("연도별 매출 비교")
    yearly = df.groupby('연도')['금액'].sum().reset_index()
    yearly.columns = ['연도', '매출']
    yearly['연도'] = yearly['연도'].astype(str)

    fig2 = px.bar(
        yearly, x='연도', y='매출',
        text='매출', color_discrete_sequence=['#45B7D1']
    )
    fig2.update_traces(texttemplate='₩%{text:,.0f}', textposition='outside')
    fig2.update_layout(
        showlegend=False, xaxis_title='', yaxis_title='매출(원)', height=350,
        xaxis=dict(type='category', tickmode='array', tickvals=yearly['연도'].tolist())
    )
    st.plotly_chart(fig2, use_container_width=True)

with col2:
    # ── 서비스 이용률 ──
    st.subheader(f"{selected_year}년 추가 서비스 이용률")
    total = len(df_year)
    data = []
    for col, name in zip(SERVICE_COLS, SERVICE_NAMES):
        if col in df_year.columns and total > 0:
            count = int(df_year[col].apply(is_checked).sum())
            rate = round(count / total * 100, 1)
            data.append({'서비스': name, '이용횟수': count, '이용률(%)': rate})

    if data:
        service_df = pd.DataFrame(data)
        fig3 = px.bar(
            service_df, x='서비스', y='이용률(%)',
            text='이용률(%)', color_discrete_sequence=['#96CEB4']
        )
        fig3.update_traces(texttemplate='%{text}%', textposition='outside')
        fig3.update_layout(showlegend=False, yaxis_title='이용률(%)', xaxis_title='', height=350)
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.info("서비스 데이터가 없습니다.")

st.divider()

# ── 월별 상세 테이블 ──────────────────────────────────────
st.subheader(f"{selected_year}년 월별 상세 현황")

agg_dict = {
    '예약수': ('금액', 'count'),
    '총매출': ('금액', 'sum'),
    '평균금액': ('금액', 'mean'),
}
if '숙박 일수' in df_year.columns:
    agg_dict['총숙박 일수'] = ('숙박 일수', 'sum')
if '인원수' in df_year.columns:
    agg_dict['총인원'] = ('인원수', 'sum')

monthly_detail = df_year.groupby('숙박 월').agg(**agg_dict).reset_index()
monthly_detail['숙박 월'] = monthly_detail['숙박 월'].astype(int).astype(str) + '월'
monthly_detail = monthly_detail.rename(columns={'숙박 월': '월'})

fmt = {'총매출': '₩{:,.0f}', '평균금액': '₩{:,.0f}'}
if '총숙박 일수' in monthly_detail.columns:
    fmt['총숙박 일수'] = '{:.0f}박'
if '총인원' in monthly_detail.columns:
    fmt['총인원'] = '{:.0f}명'

st.dataframe(
    monthly_detail.style.format(fmt),
    use_container_width=True
)

st.divider()

# ── 인원수 분석 ────────────────────────────────────────────
st.subheader(f"{selected_year}년 인원수 분포")
if '인원수' in df_year.columns and len(df_year) > 0:
    fig4 = px.histogram(
        df_year, x='인원수', nbins=10,
        color_discrete_sequence=['#FFEAA7'],
        labels={'인원수': '인원수', 'count': '예약 수'}
    )
    fig4.update_layout(xaxis_title='인원수(명)', yaxis_title='예약 수', height=300)
    st.plotly_chart(fig4, use_container_width=True)

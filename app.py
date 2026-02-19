import streamlit as st
from pathlib import Path

st.set_page_config(
    page_title="남산댁 펜션 관리",
    page_icon="🏡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── 사이드바 "app" 숨기고 "Menu" 표시 ───────────────────────
st.markdown("""
<style>
/* "app" 네비게이션 항목 숨기기 */
[data-testid="stSidebarNav"] li:first-child {
    display: none;
}
/* "Menu" 텍스트 추가 */
[data-testid="stSidebarNav"]::before {
    content: "Menu";
    display: block;
    font-size: 1.1rem;
    font-weight: 700;
    color: #555;
    padding: 0.8rem 1rem 0.5rem 1rem;
    border-bottom: 1px solid #eee;
    margin-bottom: 0.5rem;
}
</style>
""", unsafe_allow_html=True)

# ── 타이틀 + 이미지 ─────────────────────────────────────────
img_path = Path(__file__).parent / ".streamlit" / "image1.png"
col_img, col_title = st.columns([1, 10])
with col_img:
    if img_path.exists():
        st.image(str(img_path), width=45)
with col_title:
    st.title("남산댁 펜션 관리 시스템")

st.markdown("---")

st.markdown("""
### 환영합니다!

좌측 메뉴에서 원하는 기능을 선택하세요:

- 📊 **대시보드** - 이번 달 매출 현황 및 연간 요약
- 📋 **예약관리** - 예약 조회 / 추가 / 수정 / 삭제
- 📈 **매출분석** - 월별·연도별 매출 그래프 및 서비스 분석
""")

st.info("💡 데이터는 Google Sheets에 실시간으로 저장됩니다.")

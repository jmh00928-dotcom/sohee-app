import streamlit as st
import time
import random

# --- 1. 페이지 설정 (모바일 화면처럼 좁게 보기) ---
st.set_page_config(page_title="소희야 어디갈까", page_icon="📍")

# CSS로 디자인 다듬기 (버튼 색상, 폰트 등)
st.markdown("""
<style>
    .stButton>button {
        width: 100%;
        border-radius: 20px;
        height: 3em;
        font-weight: bold;
    }
    .big-font {
        font-size: 20px !important;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. 메인 로직 (아까 만든 두뇌) ---
def get_recommendation(category, km):
    # 실제로는 여기서 API 호출 및 이미지 분석이 돌아갑니다.
    # 지금은 시뮬레이션입니다.
    time.sleep(2) # 분석하는 척 시간 끌기
    
    if category == "식당":
        return {
            "name": "맛나 파스타",
            "desc": "⭐ 4.5 (리뷰 120개) | 대표메뉴: 해산물 파스타",
            "img": "https://images.unsplash.com/photo-1473093295043-cdd812d0e601?w=600", # 임시 이미지
            "msg": "여기 어때? 실패 없을 거야! 😋",
            "link": "https://map.kakao.com"
        }
    else:
        return {
            "name": "카페 블랑",
            "desc": "🤍 화이트톤 일치도 95% | 리뷰 5개 (완전 신상!)",
            "img": "https://images.unsplash.com/photo-1497935586351-b67a49e012bf?w=600",
            "msg": "여기 완전 하양하양해 🤍 인생샷 각!",
            "link": "https://map.naver.com"
        }

# --- 3. 화면 UI 구성 ---

# 타이틀
st.title("📍 소희야 어디갈까")
st.caption("결정장애 친구들을 위한 AI 추천 서비스")

# 탭으로 식당/카페 나누기
tab1, tab2 = st.tabs(["🍚 배고파 (식당)", "☕ 카페갈래 (카페)"])

# --- 탭 1: 식당 ---
with tab1:
    st.image("https://images.unsplash.com/photo-1540189549336-e6e99c3679fe?w=600", caption="맛있는 거 먹자!")
    
    st.write("### 소희야, 밥 먹으러 어디까지 갈 수 있어?")
    
    # 거리 슬라이더
    distance_food = st.slider("거리 선택 (km)", 0.5, 10.0, 1.0, key="dist_food")
    
    if distance_food < 1.5:
        st.info("🚶 걸어서 갈 수 있는 거리야!")
    else:
        st.info("🚗 차 타거나 버스 타야 해!")

    if st.button("맛집 찾아줘! (Click)", type="primary"):
        with st.spinner("소희가 카카오맵 별점 확인 중...⭐"):
            result = get_recommendation("식당", distance_food)
            
        st.success("찾았다!")
        st.image(result['img'])
        st.markdown(f"### {result['name']}")
        st.write(result['desc'])
        st.info(f"🗣️ 소희: {result['msg']}")
        st.link_button("카카오맵으로 보기", result['link'])

# --- 탭 2: 카페 ---
with tab2:
    st.image("https://images.unsplash.com/photo-1445116572660-3999b7068ecd?w=600", caption="예쁜 곳 가자!")
    
    st.write("### 소희야, 커피 마시러 어디까지 갈 수 있어?")
    
    distance_cafe = st.slider("거리 선택 (km)", 0.5, 10.0, 3.0, key="dist_cafe")
    
    if distance_cafe < 1.5:
        st.info("🚶 산책 겸 걸어가자!")
    else:
        st.info("🚗 드라이브 겸 가보자!")

    if st.button("예쁜 카페 찾아줘! (Click)", type="primary"):
        with st.spinner("소희가 사진 분석 중... (하얀색인가? 👀)"):
            result = get_recommendation("카페", distance_cafe)
            
        st.success("찾았다!")
        st.image(result['img'])
        st.markdown(f"### {result['name']}")
        st.write(result['desc'])
        st.info(f"🗣️ 소희: {result['msg']}")
        st.link_button("네이버 지도로 보기", result['link'])
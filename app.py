import streamlit as st
import random
import time

# --- 1. 페이지 설정 및 디자인 ---
st.set_page_config(page_title="소희야 어디갈까", page_icon="📍")

st.markdown("""
<style>
    .stButton>button {
        width: 100%;
        border-radius: 15px;
        height: 3.5em;
        font-weight: bold;
        background-color: #FF6F61;
        color: white;
    }
    .result-card {
        background-color: #f9f9f9;
        padding: 20px;
        border-radius: 15px;
        margin-bottom: 20px;
        border: 1px solid #ddd;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. 데이터 (가상 데이터베이스) ---
# 실제로는 API로 가져와야 하지만, 프로토타입에서는 이렇게 목록을 만들어두고 씁니다.
food_db = [
    {"name": "감성타코", "menu": "멕시칸", "score": 4.5},
    {"name": "우래옥", "menu": "평양냉면", "score": 4.6},
    {"name": "다운타우너", "menu": "수제버거", "score": 4.4},
    {"name": "정돈", "menu": "프리미엄 돈카츠", "score": 4.7},
    {"name": "땀땀", "menu": "곱창 쌀국수", "score": 4.3},
    {"name": "호랑이식당", "menu": "탄탄면", "score": 4.2},
    {"name": "빠레뜨한남", "menu": "파스타", "score": 4.1},
    {"name": "몽탄", "menu": "우대갈비", "score": 4.8},
]

cafe_db = [
    {"name": "어니언", "tag": "한옥 감성", "white_score": 80},
    {"name": "블루보틀", "tag": "미니멀 화이트", "white_score": 95},
    {"name": "아우어베이커리", "tag": "더티초코 맛집", "white_score": 40},
    {"name": "카멜커피", "tag": "빈티지 브라운", "white_score": 30},
    {"name": "카페 노티드", "tag": "귀여운 도넛", "white_score": 85},
    {"name": "테일러커피", "tag": "모던 심플", "white_score": 70},
    {"name": "로우커피스탠드", "tag": "힙한 감성", "white_score": 60},
]

# --- 3. 핵심 로직 함수 ---

def get_random_coords(radius_km):
    """중심지에서 랜덤한 거리와 방향을 계산하는 함수 (시각적 효과용)"""
    angle = random.uniform(0, 360)
    distance = random.uniform(0.1, radius_km)
    
    # 방향을 텍스트로 변환
    directions = ["북쪽", "북동쪽", "동쪽", "남동쪽", "남쪽", "남서쪽", "서쪽", "북서쪽"]
    dir_idx = int((angle / 45) % 8)
    direction_str = directions[dir_idx]
    
    return distance, direction_str

def recommend_places(category, location, radius_km):
    """위치와 카테고리를 받아 3개의 장소를 추천"""
    results = []
    
    # 1. 랜덤 로직 수행 (시각적 표현)
    dist, direction = get_random_coords(radius_km)
    st.info(f"📍 '{location}' 기준 {direction}으로 {dist:.1f}km 떨어진 곳을 탐색했어요!")
    
    # 2. 데이터 뽑기 (랜덤으로 3개)
    if category == "식당":
        # 별점 4.0 이상만 필터링
        candidates = [f for f in food_db if f['score'] >= 4.0]
        picks = random.sample(candidates, 3) # 3개 랜덤 추출
        
        for p in picks:
            results.append({
                "name": p['name'],
                "desc": f"⭐ {p['score']} | 대표메뉴: {p['menu']}",
                "query": f"{location} {p['name']}", # 검색어 조합
                "map_url": f"https://map.kakao.com/link/search/{location} {p['name']}" # 실제 링크
            })
            
    else: # 카페
        # '화이트' 점수가 높거나, 리뷰가 적은(신상) 컨셉으로 필터링 (여기선 랜덤)
        picks = random.sample(cafe_db, 3)
        
        for p in picks:
            is_white = "🤍 화이트톤 인테리어" if p['white_score'] >= 70 else "☕ 아늑한 분위기"
            results.append({
                "name": p['name'],
                "desc": f"{is_white} | 특징: {p['tag']}",
                "query": f"{location} {p['name']}",
                "map_url": f"https://map.naver.com/v5/search/{location} {p['name']}" # 실제 링크
            })
            
    return results

# --- 4. 앱 화면 구성 (UI) ---

st.title("📍 소희야 어디갈까")
st.write("결정장애? 소희가 대신 골라줄게! (랜덤 추천)")

# [수정 1] 내 위치 입력 받기
location = st.text_input("지금 어디야?", placeholder="예: 강남역, 홍대입구, 성수동...")

if location: # 위치가 입력되었을 때만 아래 내용 표시
    
    tab1, tab2 = st.tabs(["🍚 밥 먹자 (식당)", "☕ 커피 한잔 (카페)"])

    # --- 식당 탭 ---
    with tab1:
        st.write("### 밥 먹으러 어디까지 갈 수 있어?")
        # [수정 2] 거리 선택
        radius_food = st.slider("이동 반경 (km)", 0.5, 5.0, 1.0, key="r_food")
        
        if st.button("맛집 골라줘! (3곳 추천)", key="btn_food"):
            with st.spinner(f"소희가 '{location}' 주변 맛집 탐색 중... 🧐"):
                time.sleep(1.5) # 분석하는 척
                recommendations = recommend_places("식당", location, radius_food)
            
            st.success("짜잔! 여기 어때?")
            
            # [수정 3] 결과물 3개 보여주기
            for item in recommendations:
                with st.container():
                    st.markdown(f"""
                    <div class="result-card">
                        <h3 style="margin:0;">{item['name']}</h3>
                        <p style="color:gray;">{item['desc']}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    # [수정 4] 실제 작동하는 링크 연결
                    st.link_button(f"👉 {item['name']} 위치 보기 (카카오맵)", item['map_url'])

    # --- 카페 탭 ---
    with tab2:
        st.write("### 카페는 어디까지 갈 거야?")
        radius_cafe = st.slider("이동 반경 (km)", 0.5, 5.0, 2.0, key="r_cafe")
        
        if st.button("예쁜 카페 골라줘! (3곳 추천)", key="btn_cafe"):
            with st.spinner(f"소희가 '{location}' 근처 신상/화이트톤 카페 찾는 중... 🤍"):
                time.sleep(1.5)
                recommendations = recommend_places("카페", location, radius_cafe)
            
            st.success("인생샷 건지러 가자!")
            
            for item in recommendations:
                with st.container():
                    st.markdown(f"""
                    <div class="result-card">
                        <h3 style="margin:0;">{item['name']}</h3>
                        <p style="color:gray;">{item['desc']}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    st.link_button(f"👉 {item['name']} 위치 보기 (네이버 지도)", item['map_url'])

else:
    # 위치 입력 안 했을 때 안내
    st.info("👆 먼저 위칸에 '현재 위치'를 입력해줘!")

import streamlit as st
import random
import requests
import math
from streamlit_js_eval import get_geolocation

# --- 1. 환경 설정 ---
st.set_page_config(page_title="소희야 어디갈까", page_icon="📍")

st.markdown("""
<style>
    .stButton>button {
        width: 100%;
        border-radius: 15px;
        height: 3.5em;
        font-weight: bold;
        background-color: #FEE500;
        color: #191919;
    }
    .result-card {
        background-color: #fff;
        padding: 20px;
        border-radius: 15px;
        margin-bottom: 20px;
        border: 1px solid #ddd;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    .success-msg {
        background-color: #E8F5E9;
        color: #2E7D32;
        padding: 10px;
        border-radius: 10px;
        font-weight: bold;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. 핵심 함수들 ---

def get_random_coordinate(lat, lng, max_dist_km):
    # 최소 1km ~ 최대 20km 사이로 이동
    random_dist = random.uniform(1.0, max_dist_km)
    random_angle = random.uniform(0, 360)
    
    delta_lat = (random_dist / 111.0) * math.cos(math.radians(random_angle))
    delta_lng = (random_dist / (111.0 * math.cos(math.radians(lat)))) * math.sin(math.radians(random_angle))
    
    return lat + delta_lat, lng + delta_lng, random_dist

def fetch_places(lat, lng, category_code, radius_meter):
    url = "https://dapi.kakao.com/v2/local/search/category.json"
    headers = {"Authorization": f"KakaoAK {st.secrets['KAKAO_API_KEY']}"}
    params = {
        "category_group_code": category_code,
        "x": lng, 
        "y": lat,
        "radius": radius_meter,
        "size": 15,
        "sort": "accuracy"
    }
    try:
        response = requests.get(url, headers=headers, params=params)
        return response.json().get('documents', [])
    except:
        return []

# --- 3. [수정됨] 무한 재시도 로직 ---
def recommend_logic_with_retry(start_lat, start_lng, mode):
    
    max_retries = 10 # 최대 10번까지 다시 시도함
    
    # 모드별 설정
    if mode == "식당":
        code = "FD6"
        search_radius = 5000 # 검색 반경 5km (좀 더 넓혀서 확률 높임)
        keyword = "음식점"
    else: # 카페
        code = "CE7"
        search_radius = 10000 # 검색 반경 10km
        keyword = "카페"

    for i in range(max_retries):
        # 1. 랜덤 좌표 생성
        target_lat, target_lng, moved_km = get_random_coordinate(start_lat, start_lng, 20.0)
        
        # 2. API 찔러보기
        raw_places = fetch_places(target_lat, target_lng, code, search_radius)
        
        # 3. 데이터가 있고, 키워드가 맞는지 확인
        valid_places = [p for p in raw_places if keyword in p.get('category_name', '')]
        
        if valid_places:
            # 성공! (찾았음)
            # 결과 섞어서 3개 뽑기
            picks = random.sample(valid_places, min(3, len(valid_places)))
            return picks, moved_km, i + 1 # (결과, 거리, 시도횟수) 반환
        
        # 실패하면 루프가 다시 돌면서 새로운 좌표를 찍음
    
    # 10번 다 했는데도 못 찾음 (거의 희박함)
    return [], 0, max_retries

# --- 4. UI ---
st.title("📍 소희야 어디갈까 (Auto-Retry)")

loc = get_geolocation()

if loc:
    cur_lat = loc['coords']['latitude']
    cur_lng = loc['coords']['longitude']
    
    st.success("📍 GPS 연결 성공!")
    
    tab1, tab2 = st.tabs(["🍽️ 식당", "☕ 카페"])
    
    # 식당 탭
    with tab1:
        if st.button("맛집 찾아줘!", key="btn_food"):
            with st.spinner("소희가 맛집 있는 동네 나올 때까지 지도 돌리는 중... 🎲"):
                picks, km, try_count = recommend_logic_with_retry(cur_lat, cur_lng, "식당")
            
            if picks:
                # 성공 메시지
                st.markdown(f"""
                <div class="success-msg">
                🎉 {try_count}번 시도 끝에 발견!<br>
                여기서 {km:.1f}km 떨어진 동네야.
                </div>
                """, unsafe_allow_html=True)
                
                for p in picks:
                    st.markdown(f"**{p['place_name']}**")
                    st.link_button("카카오맵 보기", p['place_url'])
            else:
                st.error("10번이나 던졌는데 전부 산이나 바다에 떨어졌어... 😭 다시 눌러줘!")

    # 카페 탭
    with tab2:
        if st.button("카페 찾아줘!", key="btn_cafe"):
            with st.spinner("소희가 예쁜 카페 찾을 때까지 지도 돌리는 중... 🎲"):
                picks, km, try_count = recommend_logic_with_retry(cur_lat, cur_lng, "카페")
            
            if picks:
                st.markdown(f"""
                <div class="success-msg">
                🎉 {try_count}번 시도 끝에 발견!<br>
                여기서 {km:.1f}km 떨어진 동네야.
                </div>
                """, unsafe_allow_html=True)
                
                for p in picks:
                    st.markdown(f"**{p['place_name']}**")
                    url = f"https://m.search.naver.com/search.naver?query={p['place_name']} {p['road_address_name']}"
                    st.link_button("네이버 리뷰 보기", url)
            else:
                st.error("주변 20km가 전부 카페 불모지인가봐... 다시 눌러줘!")

else:
    st.info("👆 [내 위치 찾기] 버튼을 누르고 잠시만 기다려주세요.")

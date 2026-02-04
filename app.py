import streamlit as st
import random
import requests
import math
from streamlit_js_eval import get_geolocation

# --- 1. 환경 설정 ---
st.set_page_config(page_title="소희야 어디갈까", page_icon="📍", layout="wide")

st.markdown("""
<style>
    .stButton>button {
        width: 100%;
        border-radius: 12px;
        height: 3em;
        font-weight: bold;
    }
    /* 식당 탭 버튼 스타일 */
    div[data-testid="stHorizontalBlock"] button[kind="secondary"] {
        background-color: #FEE500; color: black; border: none;
    }
    /* 카페 탭 버튼 스타일 (카카오 통일감을 위해 같은 노란색 계열이나 약간 다르게) */
    div[data-testid="stHorizontalBlock"] button[kind="primary"] {
        background-color: #FEE500; color: black; border: none;
    }
    .place-title {
        font-size: 20px; font-weight: bold; margin-bottom: 5px; color: #333;
    }
    .time-badge {
        display: inline-block;
        background-color: #E3F2FD;
        color: #1565C0;
        padding: 4px 8px;
        border-radius: 6px;
        font-size: 13px;
        font-weight: bold;
        margin-bottom: 8px;
    }
    .place-addr {
        font-size: 14px; color: #666; margin-bottom: 10px;
    }
    .result-box {
        background-color: white;
        padding: 20px;
        border-radius: 15px;
        border: 1px solid #eee;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. 계산 함수들 ---

def calculate_time_and_distance(lat1, lon1, lat2, lon2):
    """직선 거리 및 대중교통 예상 시간 계산"""
    R = 6371
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    a = math.sin(dLat/2) * math.sin(dLat/2) + \
        math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * \
        math.sin(dLon/2) * math.sin(dLon/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    distance_km = R * c
    
    # 예상 시간 (거리 * 1.4배 굴곡 / 시속 25km + 도보 15분)
    estimated_min = int(((distance_km * 1.4) / 25) * 60 + 15)
    return distance_km, estimated_min

def get_random_coordinate(lat, lng, max_dist_km):
    random_dist = random.uniform(1.0, max_dist_km)
    random_angle = random.uniform(0, 360)
    delta_lat = (random_dist / 111.0) * math.cos(math.radians(random_angle))
    delta_lng = (random_dist / (111.0 * math.cos(math.radians(lat)))) * math.sin(math.radians(random_angle))
    return lat + delta_lat, lng + delta_lng, random_dist

def get_region_name(lat, lng):
    url = "https://dapi.kakao.com/v2/local/geo/coord2regioncode.json"
    headers = {"Authorization": f"KakaoAK {st.secrets['KAKAO_API_KEY']}"}
    params = {"x": lng, "y": lat}
    try:
        response = requests.get(url, headers=headers, params=params)
        data = response.json()
        if data.get('documents'):
            return data['documents'][0]['address_name']
        return None
    except:
        return None

def search_keyword_kakao(keyword, lat, lng, radius=5000):
    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    headers = {"Authorization": f"KakaoAK {st.secrets['KAKAO_API_KEY']}"}
    params = {
        "query": keyword, "x": lng, "y": lat, "radius": radius, "size": 15, "sort": "accuracy" 
    }
    try:
        response = requests.get(url, headers=headers, params=params)
        return response.json().get('documents', [])
    except:
        return []

def recommend_logic_final(start_lat, start_lng, mode):
    max_retries = 10 
    for i in range(max_retries):
        target_lat, target_lng, moved_km = get_random_coordinate(start_lat, start_lng, 20.0)
        region_name = get_region_name(target_lat, target_lng)
        if not region_name: continue

        if mode == "식당":
            query = f"{region_name} 맛집"
            filter_code = "FD6"
        else: 
            cafe_adj = ["분위기 좋은", "예쁜", "디저트 맛집", "감성", "로스팅"]
            selected_adj = random.choice(cafe_adj)
            query = f"{region_name} {selected_adj} 카페"
            filter_code = "CE7"

        places = search_keyword_kakao(query, target_lat, target_lng)
        valid_places = [p for p in places if p['category_group_code'] == filter_code]
        
        if valid_places:
            picks = random.sample(valid_places, min(3, len(valid_places)))
            return picks, region_name, query, moved_km
    return [], None, None, 0

# --- 3. UI 구성 ---
st.title("📍 소희야 어디갈까")

if 'KAKAO_API_KEY' not in st.secrets:
    st.error("🚨 카카오 API 키가 없습니다!")
    st.stop()

loc = get_geolocation()

if loc:
    cur_lat = loc['coords']['latitude']
    cur_lng = loc['coords']['longitude']
    
    st.success("📍 GPS 연결 성공!")
    
    tab1, tab2 = st.tabs(["🍽️ 찐맛집", "☕ 예쁜카페"])
    
    # [식당 탭]
    with tab1:
        st.info("랜덤 동네의 **맛집**을 찾아줄게!")
        if st.button("맛집 찾아줘!", key="btn_food"):
            with st.spinner("소희가 맛집 찾는 중... 😋"):
                picks, region, query, km = recommend_logic_final(cur_lat, cur_lng, "식당")
            
            if picks:
                st.success(f"🚀 **{region}** (직선거리 {km:.1f}km) 도착!")
                
                for p in picks:
                    name = p['place_name']
                    cat = p['category_name'].split('>')[-1].strip()
                    addr = p['road_address_name']
                    review_url = p['place_url'] # 카카오맵 상세페이지
                    
                    dest_lat = p['y']
                    dest_lng = p['x']
                    
                    # 카카오맵 길찾기 URL (출발지: 내위치)
                    route_url = f"https://map.kakao.com/link/to/{name},{dest_lat},{dest_lng}/from/내위치,{cur_lat},{cur_lng}"
                    
                    dist, mins = calculate_time_and_distance(cur_lat, cur_lng, float(dest_lat), float(dest_lng))
                    
                    with st.container():
                        st.markdown(f"""
                        <div class="result-box">
                            <div class="place-title">{name} <span style="font-size:14px; color:#888;">({cat})</span></div>
                            <div class="time-badge">⏱️ 대중교통 약 {mins}분 예상</div>
                            <div class="place-addr">📍 {addr}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.link_button("⭐ 리뷰 보기", review_url, use_container_width=True)
                        with col2:
                            st.link_button("🚀 길찾기", route_url, use_container_width=True)

    # [카페 탭]
    with tab2:
        st.info("랜덤 동네의 **카페**를 찾아줄게!")
        if st.button("카페 찾아줘!", key="btn_cafe"):
            with st.spinner("소희가 예쁜 카페 찾는 중... ✨"):
                picks, region, query, km = recommend_logic_final(cur_lat, cur_lng, "카페")
            
            if picks:
                st.success(f"🚀 **{region}** (직선거리 {km:.1f}km) 도착!")
                
                for p in picks:
                    name = p['place_name']
                    cat = p['category_name'].split('>')[-1].strip()
                    addr = p['road_address_name']
                    
                    # [수정됨] 카카오맵 리뷰/상세 URL로 변경
                    review_url = p['place_url'] 
                    
                    dest_lat = p['y']
                    dest_lng = p['x']
                    
                    # [수정됨] 카카오맵 길찾기 URL로 변경
                    route_url = f"https://map.kakao.com/link/to/{name},{dest_lat},{dest_lng}/from/내위치,{cur_lat},{cur_lng}"
                    
                    dist, mins = calculate_time_and_distance(cur_lat, cur_lng, float(dest_lat), float(dest_lng))

                    with st.container():
                        st.markdown(f"""
                        <div class="result-box">
                            <div class="place-title">{name} <span style="font-size:14px; color:#888;">({cat})</span></div>
                            <div class="time-badge">⏱️ 대중교통 약 {mins}분 예상</div>
                            <div class="place-addr">📍 {addr}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            # 카카오맵 아이콘 느낌을 위해 별(⭐) 아이콘 사용
                            st.link_button("⭐ 리뷰 보기", review_url, use_container_width=True)
                        with col2:
                            st.link_button("🚀 길찾기", route_url, use_container_width=True)

else:
    st.info("👆 [내 위치 찾기] 버튼을 눌러주세요.")

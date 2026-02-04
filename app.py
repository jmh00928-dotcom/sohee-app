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
    div[data-testid="stHorizontalBlock"] button[kind="secondary"] {
        background-color: #FEE500; color: black; border: none;
    }
    div[data-testid="stHorizontalBlock"] button[kind="primary"] {
        background-color: #03C75A; color: white; border: none;
    }
    .place-title {
        font-size: 18px; font-weight: bold; margin-bottom: 5px; color: #333;
    }
    .place-info {
        font-size: 13px; color: #666; margin-bottom: 3px;
    }
    .time-badge {
        display: inline-block;
        background-color: #E3F2FD;
        color: #1565C0;
        padding: 3px 8px;
        border-radius: 8px;
        font-size: 12px;
        font-weight: bold;
        margin-bottom: 5px;
    }
    img { border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

# --- 2. 계산 및 이미지 함수 ---

def get_category_image(category_name):
    """카테고리별 이미지 매칭"""
    category_name = category_name or ""
    if any(x in category_name for x in ["카페", "커피"]):
        return "https://images.unsplash.com/photo-1497935586351-b67a49e012bf?w=400&h=300&fit=crop"
    if any(x in category_name for x in ["디저트", "베이커리"]):
        return "https://images.unsplash.com/photo-1551024601-bec78aea704b?w=400&h=300&fit=crop"
    if any(x in category_name for x in ["한식", "찌개", "고기", "국밥"]):
        return "https://images.unsplash.com/photo-1580651315530-69c8e0026377?w=400&h=300&fit=crop"
    if any(x in category_name for x in ["양식", "파스타", "피자"]):
        return "https://images.unsplash.com/photo-1551183053-bf91a1d81141?w=400&h=300&fit=crop"
    if any(x in category_name for x in ["일식", "초밥", "돈까스"]):
        return "https://images.unsplash.com/photo-1553621042-f6e147245754?w=400&h=300&fit=crop"
    if any(x in category_name for x in ["중식", "짜장"]):
        return "https://images.unsplash.com/photo-1525201548942-d8732f6617a0?w=400&h=300&fit=crop"
    return "https://images.unsplash.com/photo-1414235077428-338989a2e8c0?w=400&h=300&fit=crop"

def calculate_time_and_distance(lat1, lon1, lat2, lon2):
    """
    [핵심] 두 좌표 사이의 거리와 대중교통 예상 시간을 계산함
    - Haversine 공식으로 직선 거리를 구함
    - 직선 거리 x 1.4 (도로 굴곡 보정) / 시속 25km (대중교통 평균) 로 시간 추산
    """
    R = 6371  # 지구 반지름 (km)
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    a = math.sin(dLat/2) * math.sin(dLat/2) + \
        math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * \
        math.sin(dLon/2) * math.sin(dLon/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    distance_km = R * c
    
    # 예상 시간 계산 (분 단위)
    # 로직: (거리 * 1.4배) / 시속 25km * 60분 + 도보/대기시간 15분
    estimated_min = int(((distance_km * 1.4) / 25) * 60 + 15)
    
    return distance_km, estimated_min

# --- 3. 기본 로직 함수들 ---

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
        valid_places = [p for p in places if p['category_group_code'] == filter

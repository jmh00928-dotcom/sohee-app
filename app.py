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
    .badge-no-franchise {
        background-color: #FFEBEE;
        color: #C62828;
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 11px;
        margin-left: 5px;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. [NEW] 프랜차이즈 차단 목록 (블랙리스트) ---
# 여기에 있는 단어가 가게 이름에 포함되면 결과에서 제외합니다.
FRANCHISE_LIST = [
    # 카페
    "스타벅스", "투썸플레이스", "이디야", "메가MGC", "메가커피", "컴포즈", "빽다방", 
    "할리스", "엔제리너스", "파스쿠찌", "폴바셋", "더벤티", "공차", "아마스빈", "블루보틀",
    # 패스트푸드/피자/치킨
    "맥도날드", "버거킹", "롯데리아", "KFC", "맘스터치", "프랭크버거", "서브웨이",
    "도미노", "미스터피자", "피자헛", "BBQ", "BHC", "교촌", "굽네",
    # 식당/제과
    "아웃백", "빕스", "애슐리", "파리바게뜨", "뚜레쥬르", "던킨", "배스킨라빈스",
    "홍콩반점", "새마을식당", "한신포차", "역전우동", "롤링파스타", "국수나무", 
    "김밥천국", "싸움의고수", "채선당", "샤브향", "쿠우쿠우", "명륜진사"
]

def is_franchise(name):
    """가게 이름에 프랜차이즈 키워드가 있는지 확인"""
    for fran in FRANCHISE_LIST:
        if fran in name: # 예: '스타벅스 강남점' -> True
            return True
    return False

# --- 3. 계산 함수들 ---

def calculate_time_and_distance(lat1, lon1, lat2, lon2):
    R = 6371
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    a = math.sin(dLat/2) * math.sin(dLat/2) + \
        math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * \
        math.sin(dLon/2) * math.sin(dLon/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    distance_km = R * c
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
        
        # [핵심 변경] 프랜차이즈 필터링 로직 추가
        valid_places = []
        for p in places:
            # 1. 카테고리 코드 확인
            if p['category_group_code'] == filter_code:
                # 2. 프랜차이즈 이름인지 확인 (아니어야 통과)
                if not is_franchise(p['place_name']):
                    valid_places.append(p)
        
        if valid_places:
            picks = random.sample(valid_places, min(3, len(valid_places)))
            return picks, region_name, query, moved_km
    return [], None, None, 0

# --- 4. UI 구성 ---
st.title("📍 소희야 어디갈까")
st.caption("프랜차이즈는 빼고, 진짜 숨은 곳만 찾아줄게!")

if 'KAKAO_API_KEY' not in st.secrets:
    st.error("🚨 카카오 API 키가 없습니다!")
    st.stop()

loc = get_geolocation()

if loc:
    cur_lat = loc['coords']['latitude']
    cur_lng = loc['coords']['longitude']
    
    st.success("📍 GPS 연결 성공!")
    
    tab1, tab2 = st.tabs(["🍽️ 찐맛집 (No 프랜차이즈)", "☕ 개인카페 (No 체인점)"])
    
    # [식당 탭]
    with tab1:
        st.info("랜덤 동네의 **개인 맛집**만 골라서 찾아줄게!")
        if st.button("맛집 찾아줘!", key="btn_food"):
            with st.spinner("프랜차이즈 걸러내고 맛집 찾는 중... 😋"):
                picks, region, query, km = recommend_logic_final(cur_lat, cur_lng, "식당")
            
            if picks:
                st.success(f"🚀 **{region}** (직선거리 {km:.1f}km) 도착!")
                
                for p in picks:
                    name = p['place_name']
                    cat = p['category_name'].split('>')[-1].strip()
                    addr = p['road_address_name']
                    review_url = p['place_url']
                    
                    dest_lat = p['y']
                    dest_lng = p['x']
                    
                    route_url = f"https://map.kakao.com/link/to/{name},{dest_lat},{dest_lng}/from/내위치,{cur_lat},{cur_lng}"
                    dist, mins = calculate_time_and_distance(cur_lat, cur_lng, float(dest_lat), float(dest_lng))
                    
                    with st.container():
                        st.markdown(f"""
                        <div class="result-box">
                            <div class="place-title">
                                {name} <span style="font-size:14px; color:#888;">({cat})</span>
                            </div>
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
        st.info("랜덤 동네의 **개인 카페**만 골라서 찾아줄게!")
        if st.button("카페 찾아줘!", key="btn_cafe"):
            with st.spinner("스타벅스, 메가커피 빼고 찾는 중... ✨"):
                picks, region, query, km = recommend_logic_final(cur_lat, cur_lng, "카페")
            
            if picks:
                st.success(f"🚀 **{region}** (직선거리 {km:.1f}km) 도착!")
                
                for p in picks:
                    name = p['place_name']
                    cat = p['category_name'].split('>')[-1].strip()
                    addr = p['road_address_name']
                    review_url = p['place_url']
                    
                    dest_lat = p['y']
                    dest_lng = p['x']
                    
                    route_url = f"https://map.kakao.com/link/to/{name},{dest_lat},{dest_lng}/from/내위치,{cur_lat},{cur_lng}"
                    dist, mins = calculate_time_and_distance(cur_lat, cur_lng, float(dest_lat), float(dest_lng))

                    with st.container():
                        st.markdown(f"""
                        <div class="result-box">
                            <div class="place-title">
                                {name} <span style="font-size:14px; color:#888;">({cat})</span>
                            </div>
                            <div class="time-badge">⏱️ 대중교통 약 {mins}분 예상</div>
                            <div class="place-addr">📍 {addr}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.link_button("⭐ 리뷰 보기", review_url, use_container_width=True)
                        with col2:
                            st.link_button("🚀 길찾기", route_url, use_container_width=True)

else:
    st.info("👆 [내 위치 찾기] 버튼을 눌러주세요.")

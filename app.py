import streamlit as st
import random
import requests
import math
import re
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
        background-color: #03C75A; /* 네이버 그린 (기본) */
        color: white;
    }
    /* 식당 탭 버튼만 노란색으로 */
    div[data-testid="stHorizontalBlock"] button[kind="secondary"] {
        background-color: #FEE500;
        color: black;
    }
    .result-card {
        background-color: #fff;
        padding: 20px;
        border-radius: 15px;
        margin-bottom: 20px;
        border: 1px solid #e0e0e0;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    .tag {
        font-size: 12px; color: #888; margin-bottom: 5px; display: block;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. 핵심 함수들 ---

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
        "query": keyword, 
        "x": lng, "y": lat,
        "radius": radius, 
        "size": 15,
        "sort": "accuracy" 
    }
    try:
        response = requests.get(url, headers=headers, params=params)
        return response.json().get('documents', [])
    except:
        return []

# --- 3. 추천 로직 (카페 키워드 수정됨) ---

def recommend_logic_final(start_lat, start_lng, mode):
    max_retries = 10 
    
    for i in range(max_retries):
        # 1. 랜덤 이동
        target_lat, target_lng, moved_km = get_random_coordinate(start_lat, start_lng, 20.0)
        
        # 2. 동네 이름
        region_name = get_region_name(target_lat, target_lng)
        if not region_name: continue

        # 3. 검색어 설정 (여기가 핵심!)
        if mode == "식당":
            # "OO동 맛집" (가장 정확함)
            query = f"{region_name} 맛집"
            filter_code = "FD6"
        else: # 카페
            # "신상" 키워드 제거 (검색 안됨 방지)
            # 대신 다양한 감성 키워드를 랜덤으로 사용
            cafe_adj = ["분위기 좋은", "예쁜", "디저트 맛집", "감성", "로스팅"]
            selected_adj = random.choice(cafe_adj)
            query = f"{region_name} {selected_adj} 카페"
            filter_code = "CE7"

        # 4. API 검색
        places = search_keyword_kakao(query, target_lat, target_lng)
        
        # 5. 결과 필터링
        valid_places = [p for p in places if p['category_group_code'] == filter_code]
        
        if valid_places:
            picks = random.sample(valid_places, min(3, len(valid_places)))
            return picks, region_name, query, moved_km
    
    return [], None, None, 0

# --- 4. UI ---
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
    
    # [식당]
    with tab1:
        st.info("랜덤 동네의 **검증된 맛집**을 찾아줄게!")
        if st.button("맛집 찾아줘!", key="btn_food"):
            with st.spinner("소희가 맛집 찾는 중... 😋"):
                picks, region, query, km = recommend_logic_final(cur_lat, cur_lng, "식당")
            
            if picks:
                st.success(f"🚀 **{region}** ({km:.1f}km 이동) 도착!")
                st.caption(f"🔍 검색어: '{query}'")
                
                for p in picks:
                    name = p['place_name']
                    cat = p['category_name'].split('>')[-1].strip()
                    url = p['place_url'] # 카카오맵 링크
                    
                    st.markdown(f"""
                    <div class="result-card">
                        <span class="tag">🍽️ {cat}</span>
                        <h3 style="margin:0;">{name}</h3>
                        <p style="color:gray; margin-top:5px;">📍 {p['road_address_name']}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    st.link_button(f"👉 카카오맵으로 보기", url)
            else:
                st.error("맛집을 못 찾았어.. 다시 돌려줘!")

    # [카페]
    with tab2:
        st.info("랜덤 동네의 **분위기 좋은 카페**를 찾아줄게!")
        if st.button("카페 찾아줘!", key="btn_cafe"):
            with st.spinner("소희가 예쁜 카페 찾는 중... ✨"):
                picks, region, query, km = recommend_logic_final(cur_lat, cur_lng, "카페")
            
            if picks:
                st.success(f"🚀 **{region}** ({km:.1f}km 이동) 도착!")
                st.caption(f"🔍 검색어: '{query}'")
                
                for p in picks:
                    name = p['place_name']
                    cat = p['category_name'].split('>')[-1].strip()
                    
                    # [핵심] 네이버 지도 검색 링크 생성
                    # 네이버 API 없이도 URL만으로 네이버 맵을 열 수 있습니다.
                    naver_map_url = f"https://m.map.naver.com/search2/search.naver?query={name}"
                    
                    st.markdown(f"""
                    <div class="result-card">
                        <span class="tag">☕ {cat}</span>
                        <h3 style="margin:0;">{name}</h3>
                        <p style="color:gray; margin-top:5px;">📍 {p['road_address_name']}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    # 버튼 누르면 네이버 지도로 이동
                    st.link_button(f"👉 네이버 지도로 보기", naver_map_url)
            else:
                st.error("카페를 못 찾았어.. 다시 돌려줘!")

else:
    st.info("👆 [내 위치 찾기] 버튼을 눌러주세요.")

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
        background-color: #FEE500; /* 카카오 메인 컬러 */
        color: #191919;
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
        font-size: 12px; color: #666; margin-bottom: 5px; display: block;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. 핵심 함수들 (좌표 계산 & 주소 변환) ---

def get_random_coordinate(lat, lng, max_dist_km):
    """현재 위치에서 랜덤한 거리(1~20km)만큼 이동한 좌표 반환"""
    random_dist = random.uniform(1.0, max_dist_km)
    random_angle = random.uniform(0, 360)
    
    delta_lat = (random_dist / 111.0) * math.cos(math.radians(random_angle))
    delta_lng = (random_dist / (111.0 * math.cos(math.radians(lat)))) * math.sin(math.radians(random_angle))
    
    return lat + delta_lat, lng + delta_lng, random_dist

def get_region_name(lat, lng):
    """좌표 -> 행정구역 이름(예: 서교동) 변환"""
    url = "https://dapi.kakao.com/v2/local/geo/coord2regioncode.json"
    headers = {"Authorization": f"KakaoAK {st.secrets['KAKAO_API_KEY']}"}
    params = {"x": lng, "y": lat}
    
    try:
        response = requests.get(url, headers=headers, params=params)
        data = response.json()
        if data.get('documents'):
            # 행정동 명칭 반환
            return data['documents'][0]['address_name']
        return None
    except:
        return None

def search_keyword_kakao(keyword, lat, lng, radius=5000):
    """카카오 키워드 검색 (식당/카페 공용)"""
    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    headers = {"Authorization": f"KakaoAK {st.secrets['KAKAO_API_KEY']}"}
    params = {
        "query": keyword, 
        "x": lng, "y": lat,
        "radius": radius, 
        "size": 15,
        "sort": "accuracy" # 정확도순 (키워드 매칭 중요)
    }
    try:
        response = requests.get(url, headers=headers, params=params)
        return response.json().get('documents', [])
    except:
        return []

# --- 3. 추천 로직 (카카오 통합) ---

def recommend_logic_kakao_only(start_lat, start_lng, mode):
    max_retries = 10 # 10번 재시도
    
    for i in range(max_retries):
        # 1. 랜덤 이동 (20km 이내)
        target_lat, target_lng, moved_km = get_random_coordinate(start_lat, start_lng, 20.0)
        
        # 2. 동네 이름 알아내기
        region_name = get_region_name(target_lat, target_lng)
        if not region_name: continue

        # 3. 모드별 검색어 설정
        if mode == "식당":
            query = f"{region_name} 맛집"
            category_filter = "FD6" # 음식점
        else: # 카페
            query = f"{region_name} 신상 카페" # 카카오에서도 이 키워드 먹힙니다!
            category_filter = "CE7" # 카페

        # 4. API 검색
        places = search_keyword_kakao(query, target_lat, target_lng)
        
        # 5. 결과 필터링 (카테고리 코드로 이중 검증)
        valid_places = [p for p in places if p['category_group_code'] == category_filter]
        
        if valid_places:
            # 결과가 있으면 3개 랜덤 추출
            picks = random.sample(valid_places, min(3, len(valid_places)))
            return picks, region_name, query, moved_km
    
    return [], None, None, 0

# --- 4. UI 구성 ---
st.title("📍 소희야 어디갈까 (Only Kakao)")

# 카카오 키 확인
if 'KAKAO_API_KEY' not in st.secrets:
    st.error("🚨 카카오 API 키가 없습니다! secrets.toml을 확인해주세요.")
    st.stop()

loc = get_geolocation()

if loc:
    cur_lat = loc['coords']['latitude']
    cur_lng = loc['coords']['longitude']
    
    st.success("📍 GPS 연결 성공!")
    
    tab1, tab2 = st.tabs(["🍽️ 찐맛집 찾기", "☕ 신상 카페 찾기"])
    
    # [식당 탭]
    with tab1:
        st.info("랜덤 동네의 **'맛집'**을 찾아줄게!")
        
        if st.button("맛집 찾아줘!", key="btn_food"):
            with st.spinner("소희가 맛있는 동네 찾는 중... 😋"):
                picks, region, query, km = recommend_logic_kakao_only(cur_lat, cur_lng, "식당")
            
            if picks:
                st.balloons()
                st.success(f"🚀 **{region}** ({km:.1f}km 이동) 도착!")
                st.caption(f"🔍 검색어: '{query}'")
                
                for p in picks:
                    name = p['place_name']
                    cat = p['category_name'].split('>')[-1].strip()
                    url = p['place_url']
                    
                    st.markdown(f"""
                    <div class="result-card">
                        <span class="tag">🍽️ {cat}</span>
                        <h3 style="margin:0;">{name}</h3>
                        <p style="color:gray; margin-top:5px;">📍 {p['road_address_name']}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    st.link_button(f"👉 카카오맵으로 보기", url)
            else:
                st.error("맛집을 못 찾았어.. 다시 찾아볼까?")

    # [카페 탭]
    with tab2:
        st.info("랜덤 동네의 **'신상 카페'**를 찾아줄게!")
        # 카페 버튼 색상을 약간 다르게 (커피색 느낌)
        st.markdown('<style>div.stButton > button[kind="primary"] {background-color: #6f4e37; color: white;}</style>', unsafe_allow_html=True)
        
        if st.button("신상 카페 찾아줘!", key="btn_cafe"):
            with st.spinner("소희가 분위기 좋은 신상 카페 찾는 중... ✨"):
                picks, region, query, km = recommend_logic_kakao_only(cur_lat, cur_lng, "카페")
            
            if picks:
                st.balloons()
                st.success(f"🚀 **{region}** ({km:.1f}km 이동) 도착!")
                st.caption(f"🔍 검색어: '{query}'")
                
                for p in picks:
                    name = p['place_name']
                    cat = p['category_name'].split('>')[-1].strip()
                    url = p['place_url']
                    
                    st.markdown(f"""
                    <div class="result-card">
                        <span class="tag">☕ {cat}</span>
                        <h3 style="margin:0;">{name}</h3>
                        <p style="color:gray; margin-top:5px;">📍 {p['road_address_name']}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    st.link_button(f"👉 카카오맵으로 보기", url)
            else:
                st.error("이 동네엔 신상 카페가 안 잡히네.. 다시 돌려줘!")

else:
    st.info("👆 [내 위치 찾기] 버튼을 눌러주세요.")

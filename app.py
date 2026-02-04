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
    .tag {
        font-size: 12px; color: #888; margin-bottom: 5px; display: block;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. 핵심 함수들 ---

# (1) 랜덤 좌표 계산
def get_random_coordinate(lat, lng, max_dist_km):
    random_dist = random.uniform(1.0, max_dist_km)
    random_angle = random.uniform(0, 360)
    delta_lat = (random_dist / 111.0) * math.cos(math.radians(random_angle))
    delta_lng = (random_dist / (111.0 * math.cos(math.radians(lat)))) * math.sin(math.radians(random_angle))
    return lat + delta_lat, lng + delta_lng, random_dist

# (2) [NEW] 좌표를 동네 이름(주소)으로 바꾸기
def get_region_name(lat, lng):
    """좌표를 주면 '마포구 서교동' 같은 행정구역 이름을 반환함"""
    url = "https://dapi.kakao.com/v2/local/geo/coord2regioncode.json"
    headers = {"Authorization": f"KakaoAK {st.secrets['KAKAO_API_KEY']}"}
    params = {"x": lng, "y": lat}
    
    try:
        response = requests.get(url, headers=headers, params=params)
        data = response.json()
        # 행정동(H) 또는 법정동(B) 중 먼저 나오는 것의 전체 주소 반환
        if data.get('documents'):
            return data['documents'][0]['address_name']
        return None
    except:
        return None

# (3) [NEW] 키워드로 장소 검색하기
def search_keyword(keyword, lat, lng, radius_meter):
    """
    단순 카테고리 검색이 아니라 'OO동 맛집' 같은 키워드로 검색함.
    이래야 진짜 맛집이 나옵니다.
    """
    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    headers = {"Authorization": f"KakaoAK {st.secrets['KAKAO_API_KEY']}"}
    params = {
        "query": keyword, # 예: "서교동 맛집", "연남동 신상 카페"
        "x": lng,         # 기준 좌표를 주면 그 근처를 우선 검색해줌
        "y": lat,
        "radius": radius_meter,
        "size": 15,
        "sort": "accuracy" # 정확도순 (맛집 키워드는 정확도가 중요)
    }
    try:
        response = requests.get(url, headers=headers, params=params)
        return response.json().get('documents', [])
    except:
        return []

# --- 3. 추천 로직 (개선됨) ---
def recommend_logic_v2(start_lat, start_lng, mode):
    
    max_retries = 5 # 최대 5번 재시도
    
    for i in range(max_retries):
        # 1. 랜덤 이동 (20km 이내)
        target_lat, target_lng, moved_km = get_random_coordinate(start_lat, start_lng, 20.0)
        
        # 2. 이동한 곳의 '동네 이름' 알아내기
        region_name = get_region_name(target_lat, target_lng)
        
        if not region_name:
            continue # 바다 한가운데면 다시!

        # 3. 모드별 검색어 만들기 (여기가 핵심!)
        if mode == "식당":
            # 그냥 식당이 아니라 "OO동 맛집"으로 검색
            search_query = f"{region_name} 맛집"
            search_radius = 5000 
        else:
            # "OO동 신상 카페"로 검색 (네이버 스타일)
            # 만약 신상이 없으면 '분위기 좋은 카페' 등으로 확장 가능
            search_query = f"{region_name} 신상 카페"
            search_radius = 10000

        # 4. API 검색
        places = search_keyword(search_query, target_lat, target_lng, search_radius)
        
        if places:
            # 결과가 있으면 3개 랜덤 추출
            picks = random.sample(places, min(3, len(places)))
            return picks, region_name, search_query
    
    return [], None, None

# --- 4. UI ---
st.title("📍 소희야 어디갈까 (Advanced)")

loc = get_geolocation()

if loc:
    cur_lat = loc['coords']['latitude']
    cur_lng = loc['coords']['longitude']
    
    st.success("📍 GPS 연결 성공!")
    
    tab1, tab2 = st.tabs(["🍽️ 찐맛집 찾기", "☕ 핫플 카페 찾기"])
    
    # --- 식당 탭 ---
    with tab1:
        st.info("랜덤한 동네의 **'맛집'** 키워드로 검색한 결과를 보여줄게!")
        if st.button("맛집 찾아줘!", key="btn_food"):
            with st.spinner("소희가 맛있는 동네 찾는 중... 😋"):
                picks, region, query = recommend_logic_v2(cur_lat, cur_lng, "식당")
            
            if picks:
                st.balloons()
                st.success(f"🚀 **{region}** 으로 이동했어!")
                st.caption(f"🔍 검색어: '{query}'")
                
                for p in picks:
                    name = p['place_name']
                    category = p['category_name'].split('>')[-1].strip()
                    url = p['place_url'] # 식당은 카카오맵 링크
                    
                    st.markdown(f"""
                    <div class="result-card">
                        <span class="tag">🍽️ {category}</span>
                        <h3 style="margin:0;">{name}</h3>
                        <p style="color:gray; margin-top:5px;">📍 {p['road_address_name']}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    st.link_button(f"👉 카카오맵으로 '{name}' 보기", url)
            else:
                st.error("5번이나 돌렸는데 맛집이 없는 산골짜기인가봐 ㅠㅠ 다시 눌러줘!")

    # --- 카페 탭 ---
    with tab2:
        st.info("랜덤한 동네의 **'신상 카페'**를 네이버 검색하듯 찾아줄게!")
        if st.button("신상 카페 찾아줘!", key="btn_cafe"):
            with st.spinner("소희가 힙한 신상 카페 찾는 중... ✨"):
                picks, region, query = recommend_logic_v2(cur_lat, cur_lng, "카페")
            
            if picks:
                st.balloons()
                st.success(f"🚀 **{region}** 으로 이동했어!")
                st.caption(f"🔍 검색어: '{query}'")
                
                for p in picks:
                    name = p['place_name']
                    # [핵심] 네이버 통합검색 링크 생성 (신상 카페는 블로그 리뷰가 중요하니까)
                    # "카페이름 + 주소"로 검색해야 정확함
                    naver_search_query = f"{name} {p['address_name']}"
                    naver_url = f"https://m.search.naver.com/search.naver?query={naver_search_query}"
                    
                    st.markdown(f"""
                    <div class="result-card">
                        <span class="tag">☕ 신상/감성</span>
                        <h3 style="margin:0;">{name}</h3>
                        <p style="color:gray; margin-top:5px;">📍 {p['road_address_name']}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    st.link_button(f"👉 네이버에서 '{name}' 검색하기", naver_url)
            else:
                st.error("이 주변엔 신상 카페가 아직 없나봐.. 다시 찾아볼까?")

else:
    st.info("👆 [내 위치 찾기] 버튼을 누르고 잠시만 기다려주세요.")

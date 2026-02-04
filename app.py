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
    .btn-kakao>button {
        background-color: #FEE500; /* 카카오 옐로우 */
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
    """카카오 API로 좌표 -> 행정구역 이름(예: 서교동) 변환"""
    url = "https://dapi.kakao.com/v2/local/geo/coord2regioncode.json"
    headers = {"Authorization": f"KakaoAK {st.secrets['KAKAO_API_KEY']}"}
    params = {"x": lng, "y": lat}
    
    try:
        response = requests.get(url, headers=headers, params=params)
        data = response.json()
        if data.get('documents'):
            # 법정동(B) 또는 행정동(H) 중 '동' 단위 이름 추출
            address = data['documents'][0]['address_name'] 
            return address
        return None
    except:
        return None

# --- 3. 검색 함수 (카카오 vs 네이버) ---

def search_kakao_food(keyword, lat, lng):
    """[식당용] 카카오 로컬 API 사용"""
    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    headers = {"Authorization": f"KakaoAK {st.secrets['KAKAO_API_KEY']}"}
    params = {
        "query": keyword, 
        "x": lng, "y": lat,
        "radius": 3000, # 3km 반경 우선
        "size": 15,
        "sort": "accuracy" # 정확도순 (맛집은 이게 좋음)
    }
    try:
        response = requests.get(url, headers=headers, params=params)
        return response.json().get('documents', [])
    except:
        return []

def search_naver_cafe(keyword):
    """[카페용] 네이버 검색 API 사용"""
    url = "https://openapi.naver.com/v1/search/local.json"
    headers = {
        "X-Naver-Client-Id": st.secrets['NAVER_CLIENT_ID'],
        "X-Naver-Client-Secret": st.secrets['NAVER_CLIENT_SECRET']
    }
    params = {
        "query": keyword, # 예: "연남동 신상 카페"
        "display": 5,
        "sort": "random" # 유사도순 (네이버는 날짜순 정렬이 로컬 검색엔 없음)
    }
    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            return []
        return response.json().get('items', [])
    except:
        return []

# --- 4. 추천 로직 (요구사항 반영) ---

def recommend_logic_final(start_lat, start_lng, mode):
    max_retries = 10
    
    for i in range(max_retries):
        # 1. 20km 이내 랜덤 이동
        target_lat, target_lng, moved_km = get_random_coordinate(start_lat, start_lng, 20.0)
        
        # 2. 동네 이름 알아내기 (예: "마포구 서교동")
        region_name = get_region_name(target_lat, target_lng)
        if not region_name: continue

        # 3. 검색 및 필터링
        if mode == "식당":
            # 식당: 카카오맵 사용 / 3km 이내 / 별점 4.0 이상(데이터 없으므로 상위노출 대체) / 리뷰 많은 순
            query = f"{region_name} 맛집"
            places = search_kakao_food(query, target_lat, target_lng)
            
            # 카카오 데이터는 '음식점' 카테고리만 필터링
            valid_places = [p for p in places if "음식점" in p.get('category_name', '')]
            
            if valid_places:
                # 상위 10개 중 3개 랜덤 (인기 있는 곳 위주)
                picks = random.sample(valid_places, min(3, len(valid_places)))
                return picks, region_name, query, moved_km

        else: # 카페
            # 카페: 네이버 맵 사용 / 신상 카페 / 리뷰 적은 곳
            query = f"{region_name} 신상 카페"
            places = search_naver_cafe(query)
            
            # 네이버 데이터는 태그 제거 필요 (<b>태그 등)
            valid_places = []
            for p in places:
                # HTML 태그 제거
                clean_title = re.sub('<[^<]+?>', '', p['title'])
                p['clean_title'] = clean_title
                valid_places.append(p)
            
            if valid_places:
                # 네이버는 '신상' 키워드로 검색했으므로 상위 결과가 이미 신상/핫플임
                picks = random.sample(valid_places, min(3, len(valid_places)))
                return picks, region_name, query, moved_km
    
    return [], None, None, 0

# --- 5. UI 구성 ---
st.title("📍 소희야 어디갈까 (Final)")

# 네이버 키 확인
if 'NAVER_CLIENT_ID' not in st.secrets:
    st.error("🚨 네이버 API 키가 없습니다! secrets.toml을 확인해주세요.")
    st.stop()

loc = get_geolocation()

if loc:
    cur_lat = loc['coords']['latitude']
    cur_lng = loc['coords']['longitude']
    
    st.success("📍 GPS 연결 성공!")
    
    tab1, tab2 = st.tabs(["🍽️ 맛집 (카카오)", "☕ 카페 (네이버)"])
    
    # [식당 탭]
    with tab1:
        st.info("랜덤 동네의 **'찐맛집'**을 카카오맵으로 찾아줄게!")
        # 카카오 스타일 노란 버튼
        st.markdown('<style>div.stButton > button:first-child {background-color: #FEE500; color: black;}</style>', unsafe_allow_html=True)
        
        if st.button("맛집 찾아줘!", key="btn_food"):
            with st.spinner("소희가 맛집 스캔 중... 😋"):
                picks, region, query, km = recommend_logic_final(cur_lat, cur_lng, "식당")
            
            if picks:
                st.success(f"🚀 **{region}** ({km:.1f}km 이동) 도착!")
                
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

    # [카페 탭]
    with tab2:
        st.info("랜덤 동네의 **'신상 카페'**를 네이버 검색으로 찾아줄게!")
        # 네이버 스타일 초록 버튼 (기본 스타일)
        
        if st.button("신상 카페 찾아줘!", key="btn_cafe"):
            with st.spinner("소희가 네이버에 '신상 카페' 검색 중... ✨"):
                picks, region, query, km = recommend_logic_final(cur_lat, cur_lng, "카페")
            
            if picks:
                st.success(f"🚀 **{region}** ({km:.1f}km 이동) 도착!")
                st.caption(f"🔍 네이버 검색어: '{query}'")
                
                for p in picks:
                    name = p['clean_title']
                    addr = p['roadAddress']
                    # [핵심] 네이버 지도 검색결과 URL 생성
                    # 모바일 네이버 지도에서 쿼리로 바로 검색
                    naver_map_url = f"https://m.map.naver.com/search2/search.naver?query={name}"
                    
                    st.markdown(f"""
                    <div class="result-card">
                        <span class="tag">☕ 신상/감성</span>
                        <h3 style="margin:0;">{name}</h3>
                        <p style="color:gray; margin-top:5px;">📍 {addr}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    st.link_button(f"👉 네이버 지도로 보기", naver_map_url)
            else:
                st.error("신상 카페가 안 보여.. 다시 찾아볼까?")

else:
    st.info("👆 [내 위치 찾기] 버튼을 눌러주세요.")

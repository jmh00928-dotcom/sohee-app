import streamlit as st
import random
import requests
from streamlit_js_eval import get_geolocation # GPS 도구 가져오기

# --- 1. 페이지 설정 ---
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
</style>
""", unsafe_allow_html=True)

# --- 2. 카카오 API 함수 (좌표 기반 검색) ---
def search_places_by_coords(lat, lng, category_code, radius_meter):
    """
    내 좌표(lat, lng)를 기준으로 반경(radius) 내의 카테고리 장소를 검색함
    """
    url = "https://dapi.kakao.com/v2/local/search/category.json"
    headers = {"Authorization": f"KakaoAK {st.secrets['KAKAO_API_KEY']}"}
    params = {
        "category_group_code": category_code, # FD6(식당), CE7(카페)
        "x": lng, # 경도 (Longitude)
        "y": lat, # 위도 (Latitude)
        "radius": radius_meter, # 반경 (미터 단위)
        "sort": "distance" # 거리순 정렬 (가까운 곳 우선) or accuracy
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        data = response.json()
        return data.get('documents', [])
    except Exception as e:
        st.error(f"API 오류: {e}")
        return []

# --- 3. 추천 로직 ---
def recommend_places(lat, lng, category_type, radius_km):
    
    radius_meter = int(radius_km * 1000) # km를 m로 변환
    
    if category_type == "식당":
        code = "FD6"
    else:
        code = "CE7"

    # 1. API 호출
    places = search_places_by_coords(lat, lng, code, radius_meter)

    if not places:
        return []

    # 2. 랜덤 추천 (데이터가 많으면 3개 뽑기)
    # 거리순으로 가져왔으니, 너무 가까운 곳만 나오지 않게 
    # 상위 10개 중에서 3개를 랜덤으로 뽑는 식으로 섞어줌
    candidates = places[:15] # 상위 15개 후보군
    num_to_pick = min(3, len(candidates))
    picks = random.sample(candidates, num_to_pick)
    
    return picks

# --- 4. 앱 UI ---
st.title("📍 소희야 어디갈까 (GPS Ver.)")
st.write("내 위치 기준으로 맛집/카페를 찾아줄게!")

# [GPS 버튼]
# 이 버튼을 누르면 브라우저에서 '위치 권한 허용' 팝업이 뜹니다.
loc = get_geolocation()

if loc:
    # 좌표 획득 성공 시
    lat = loc['coords']['latitude']
    lng = loc['coords']['longitude']
    
    st.success(f"📍 현재 위치 확인 완료! (위도: {lat:.4f}, 경도: {lng:.4f})")
    
    # 탭 메뉴
    tab1, tab2 = st.tabs(["🍚 배고파 (식당)", "☕ 카페갈래 (카페)"])

    # --- 식당 탭 ---
    with tab1:
        st.info("내 주변 맛집을 찾아볼까?")
        radius_food = st.slider("몇 km 까지 갈 수 있어?", 0.5, 3.0, 1.0, key="r_food")
        
        if st.button("내 주변 맛집 추천해줘 (3곳)", key="btn_food"):
            with st.spinner("소희가 주변 스캔 중... 📡"):
                results = recommend_places(lat, lng, "식당", radius_food)
            
            if results:
                for place in results:
                    # 거리 계산 (API가 주는 distance는 미터 단위)
                    dist = int(place['distance'])
                    dist_str = f"{dist}m" if dist < 1000 else f"{dist/1000:.1f}km"
                    
                    with st.container():
                        st.markdown(f"""
                        <div class="result-card">
                            <h3 style="margin:0; color:#333;">{place['place_name']}</h3>
                            <p style="color:#FF6F61; font-weight:bold; margin:5px 0;">
                                {place['category_name'].split('>')[-1].strip()} 
                                <span style="color:gray; font-weight:normal;">({dist_str} 거리)</span>
                            </p>
                            <p style="font-size:14px; color:gray; margin:0;">📍 {place['road_address_name']}</p>
                        </div>
                        """, unsafe_allow_html=True)
                        st.link_button("👉 상세정보 & 길찾기", place['place_url'])
            else:
                st.warning("설정한 거리 안에는 식당이 없나 봐 ㅠㅠ 거리를 좀 늘려볼까?")

    # --- 카페 탭 ---
    with tab2:
        st.info("내 주변 예쁜 카페를 찾아볼까?")
        radius_cafe = st.slider("몇 km 까지 갈 수 있어?", 0.5, 3.0, 1.0, key="r_cafe")
        
        if st.button("내 주변 카페 추천해줘 (3곳)", key="btn_cafe"):
            with st.spinner("소희가 카페 찾는 중... ☕"):
                results = recommend_places(lat, lng, "카페", radius_cafe)
            
            if results:
                for place in results:
                    dist = int(place['distance'])
                    dist_str = f"{dist}m" if dist < 1000 else f"{dist/1000:.1f}km"
                    
                    with st.container():
                        st.markdown(f"""
                        <div class="result-card">
                            <h3 style="margin:0; color:#333;">{place['place_name']}</h3>
                            <p style="font-size:14px; color:gray; margin:5px 0;">
                                📍 {place['road_address_name']} ({dist_str})
                            </p>
                        </div>
                        """, unsafe_allow_html=True)
                        st.link_button("👉 사진 보러가기", place['place_url'])
            else:
                st.warning("이 근처엔 카페가 안 보여... 😭")

else:
    # GPS를 못 잡았거나 아직 버튼 안 눌렀을 때
    st.info("👆 위에 있는 **[내 위치 찾기]** 버튼을 눌러줘!")
    st.caption("※ 모바일에서는 '위치 권한 허용'을 꼭 해줘야 해!")

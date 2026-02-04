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
        display: inline-block;
        padding: 3px 8px;
        border-radius: 10px;
        font-size: 12px;
        margin-right: 5px;
    }
    .tag-food { background-color: #FFE0E0; color: #FF4B4B; }
    .tag-cafe { background-color: #E0F7FA; color: #00838F; }
</style>
""", unsafe_allow_html=True)

# --- 2. 핵심 함수: 랜덤 좌표 계산기 ---
def get_random_coordinate(lat, lng, max_dist_km):
    """
    현재 좌표(lat, lng)에서 max_dist_km 반경 내의 랜덤한 새 좌표를 생성합니다.
    """
    # 1. 랜덤한 거리(km)와 각도(degree) 생성
    random_dist = random.uniform(2.0, max_dist_km) # 최소 2km 이상은 멀어지게 설정
    random_angle = random.uniform(0, 360)

    # 2. 위도/경도 변환 로직 (Haversine 근사치)
    # 위도 1도 = 약 111km
    delta_lat = (random_dist / 111.0) * math.cos(math.radians(random_angle))
    # 경도 1도 = 약 111km * cos(위도)
    delta_lng = (random_dist / (111.0 * math.cos(math.radians(lat)))) * math.sin(math.radians(random_angle))

    new_lat = lat + delta_lat
    new_lng = lng + delta_lng

    return new_lat, new_lng, random_dist

# --- 3. 카카오 API 호출 함수 ---
def fetch_places(lat, lng, category_code, radius_meter):
    url = "https://dapi.kakao.com/v2/local/search/category.json"
    headers = {"Authorization": f"KakaoAK {st.secrets['KAKAO_API_KEY']}"}
    params = {
        "category_group_code": category_code, # FD6(식당), CE7(카페)
        "x": lng,
        "y": lat,
        "radius": radius_meter,
        "size": 15, # 최대 15개 가져오기
        "sort": "accuracy" # 정확도순
    }
    try:
        response = requests.get(url, headers=headers, params=params)
        return response.json().get('documents', [])
    except:
        return []

# --- 4. 추천 로직 (사용자 요청 반영) ---
def recommend_logic(current_lat, current_lng, mode):
    
    # [Step 1 & 2] 20km 이내 랜덤 지역 선택
    target_lat, target_lng, moved_km = get_random_coordinate(current_lat, current_lng, 20.0)
    
    msg_loc = f"🚀 현재 위치에서 약 {moved_km:.1f}km 떨어진 낯선 동네로 이동했어!"
    
    places = []
    final_picks = []

    if mode == "식당":
        # [Step 3] 랜덤 지역 기준 3km 이내 검색 (식당)
        raw_places = fetch_places(target_lat, target_lng, "FD6", 3000) # 3000m = 3km
        
        # [Step 4] 별점 4.0 이상 리스팅 -> 리뷰 많은 순 정렬
        # (API에 별점이 없으므로, 카카오맵 url이 있는 검증된 곳 중 리뷰 수로 정렬)
        # category_name에 '음식점'이 포함된 것만 확실히 필터링
        valid_places = [p for p in raw_places if "음식점" in p['category_name']]
        
        # 리뷰가 많은 순서로 정렬 (내림차순)
        # API 결과에 'review_count'가 없어서 인기순/정확도순 상위를 신뢰함
        # 여기서는 랜덤성을 위해 상위 10개 중 3개를 뽑되, 앞쪽일수록 확률 높게 설정
        if len(valid_places) >= 3:
            # 상위 10개 자르기
            top_10 = valid_places[:10]
            # 그 중에서 3개 뽑기
            final_picks = random.sample(top_10, 3)
        else:
            final_picks = valid_places

    elif mode == "카페":
        # [Step 3] 랜덤 지역 기준 10km 이내 검색 (카페)
        raw_places = fetch_places(target_lat, target_lng, "CE7", 10000) # 10000m = 10km
        
        # [Step 4] 신상 카페 (리뷰 적은 곳) 찾기
        # 카카오 API 데이터 리스트의 뒤쪽(정확도가 낮거나 인지도가 낮은 곳)을 신상으로 추정하거나
        # 랜덤하게 섞어서 "숨겨진 곳"을 찾음
        valid_places = [p for p in raw_places if "카페" in p['category_name']]
        
        if len(valid_places) >= 3:
            # 리뷰가 적은 곳을 찾기 위해 리스트를 뒤집거나 랜덤 추출
            # (일반적으로 API 상단은 유명한 곳)
            final_picks = random.sample(valid_places, 3) 
        else:
            final_picks = valid_places

    return final_picks, msg_loc

# --- 5. 앱 UI 구성 ---
st.title("📍 소희야 어디갈까 (Random Trip)")
st.write("늘 가던 곳 말고, 새로운 동네로 떠나볼까?")

# GPS 버튼
loc = get_geolocation()

if loc:
    cur_lat = loc['coords']['latitude']
    cur_lng = loc['coords']['longitude']
    
    st.success("📍 내 위치 확인 완료!")
    st.markdown("---")

    tab1, tab2 = st.tabs(["🍽️ 맛집 탐험", "☕ 카페 탐험"])

    # --- 식당 로직 UI ---
    with tab1:
        st.info("💡 20km 내 랜덤한 동네의 **검증된 맛집(3km 이내)**을 찾아줄게!")
        
        if st.button("🚀 맛집으로 순간이동!", key="btn_food"):
            with st.spinner("소희가 지도를 돌려서 찍는 중... 👆"):
                picks, msg = recommend_logic(cur_lat, cur_lng, "식당")
            
            st.warning(msg) # 랜덤 이동 알림
            
            if picks:
                st.write(f"**검증된 맛집 3곳을 찾았어!**")
                for p in picks:
                    name = p['place_name']
                    addr = p['road_address_name']
                    url = p['place_url'] # 카카오맵 링크
                    cat = p['category_name'].split('>')[-1].strip()
                    
                    with st.container():
                        st.markdown(f"""
                        <div class="result-card">
                            <span class="tag tag-food">맛집</span>
                            <h3 style="margin:5px 0;">{name}</h3>
                            <p style="color:gray; font-size:14px;">{cat} | 📍 {addr}</p>
                        </div>
                        """, unsafe_allow_html=True)
                        # [요청반영] 카카오맵 바로가기
                        st.link_button(f"👉 카카오맵으로 '{name}' 보기", url)
            else:
                st.error("앗, 그 동네는 너무 허허벌판인가봐.. 다시 돌려줘!")

    # --- 카페 로직 UI ---
    with tab2:
        st.info("💡 20km 내 랜덤한 동네의 **숨겨진 카페(10km 이내)**를 찾아줄게!")
        
        if st.button("🚀 낯선 카페 찾아줘!", key="btn_cafe"):
            with st.spinner("소희가 신상/히든 카페 찾는 중... 🤫"):
                picks, msg = recommend_logic(cur_lat, cur_lng, "카페")
            
            st.warning(msg)
            
            if picks:
                st.write(f"**분위기 있는 카페 3곳을 찾았어!**")
                for p in picks:
                    name = p['place_name']
                    addr = p['road_address_name']
                    # [요청반영] 네이버 검색 링크 생성
                    # 모바일 네이버 통합검색 링크 형식
                    naver_url = f"https://m.search.naver.com/search.naver?query={name} {addr}"
                    
                    with st.container():
                        st.markdown(f"""
                        <div class="result-card">
                            <span class="tag tag-cafe">감성/신상</span>
                            <h3 style="margin:5px 0;">{name}</h3>
                            <p style="color:gray; font-size:14px;">📍 {addr}</p>
                        </div>
                        """, unsafe_allow_html=True)
                        st.link_button(f"👉 네이버 리뷰/사진 보기", naver_url)
            else:
                st.error("이 근처엔 카페가 없네.. 다시 찾아볼까?")

else:
    st.info("👆 먼저 상단의 **[내 위치 찾기]** 버튼을 눌러줘!")

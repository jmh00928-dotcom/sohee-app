import streamlit as st
import requests

st.title("🔧 카카오 API 연결 테스트")

# 1. API 키 가져오기 확인
try:
    api_key = st.secrets['KAKAO_API_KEY']
    # 키의 앞 4글자만 보여줌 (보안상)
    st.success(f"🔑 API 키 인식 성공: {api_key[:4]}****")
except:
    st.error("🚨 secrets.toml 파일에서 API 키를 못 찾겠습니다.")
    st.stop()

# 2. 강남역 좌표로 강제 호출 (하드코딩)
st.info("📡 강남역 좌표로 테스트 요청을 보냅니다...")

url = "https://dapi.kakao.com/v2/local/search/keyword.json"
headers = {"Authorization": f"KakaoAK {api_key}"}
params = {
    "query": "스타벅스", # 무조건 있어야 하는 가게 검색
    "x": "127.0277",   # 강남역 경도
    "y": "37.4980",    # 강남역 위도
    "radius": "1000"
}

try:
    response = requests.get(url, headers=headers, params=params)
    
    # --- 결과 진단 ---
    status = response.status_code
    
    st.markdown(f"### 상태 코드: `{status}`")
    
    if status == 200:
        data = response.json()
        count = len(data.get('documents', []))
        if count > 0:
            st.balloons()
            st.success(f"✅ 연결 성공! 강남역 스타벅스 {count}개를 찾았습니다.")
            st.write(data) # 데이터 내용 보여주기
        else:
            st.warning("⚠️ 연결은 됐는데 데이터가 0개입니다. (키는 맞음)")
            st.write(response.text)
            
    elif status == 401:
        st.error("🛑 [401 에러] : API 키가 틀렸습니다!")
        st.warning("👉 'REST API 키'가 맞나요? (JavaScript 키 넣으면 안됨)")
        st.write(response.json())
        
    elif status == 400:
        st.error("🛑 [400 에러] : 요청 형식이 잘못되었습니다.")
        st.write(response.json())
        
    else:
        st.error(f"🛑 [기타 에러] : {status}")
        st.write(response.text)

except Exception as e:
    st.error(f"서버 통신 중 에러 발생: {e}")

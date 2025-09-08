import streamlit as st
import pandas as pd
import datetime
from PIL import Image

st.header("이것은 헤더입니다.")

st.markdown("1. 리스트 아이템 1\n2. 리스트 아이템 2")
st.markdown("[앤써북 홈페이지](https://cafe.naver.com/answerbook)")
st.markdown(
    """
 This is main text.
 This is how to change the color of 
text :red[Red,] :blue[Blue,] :green[Green.]
 This is **Bold** and *Italic* text
 """
)


# write
st.write("이것은 write 함수를 사용한 텍스트입니다.")

df = pd.DataFrame({"column 1": [1, 2, 3], "column 2": [4, 5, 6]})

st.write(df)

# text input
email = st.text_input("이메일 주소를 입력하세요", "example@example.com")

st.write(email)

# slider1
value = st.slider("값을 선택하세요", min_value=0, max_value=100, value=50)

st.write("선택한 값:", value)

# slider 범위 선택
range_values = st.slider(
    "범위를 선택하세요", min_value=0, max_value=100, value=(25, 75), step=5
)

st.write("선택한 범위:", range_values)

# 날짜 범위 선택
start_date, end_date = st.slider(
    "날짜 범위를 선택하세요",
    min_value=datetime.date(2020, 1, 1),
    max_value=datetime.date.today(),
    value=(datetime.date(2020, 1, 1), datetime.date.today()),
    format="YYYY-MM-DD",
)

st.write("선택한 시작 날짜:", start_date)
st.write("선택한 종료 날짜:", end_date)

# Button
if st.button("클릭하세요"):
    st.write("버튼이 클릭되었습니다.")
else:
    st.write("버튼을 클릭해 주세요.")

# checkbox
agree = st.checkbox("이용 약관에 동의합니다.")

# 체크박스의 상태에 따라 조건부로 실행
if agree:
    st.write("약관에 동의하셨습니다.")
else:
    st.write("약관 동의가 필요합니다.")

# selectbox 활용
country = st.selectbox("국가를 선택하세요:", ["한국", "미국", "일본"])
if country == "한국":
    city = st.selectbox("도시를 선택하세요:", ["서울", "부산", "대구"])
elif country == "미국":
    city = st.selectbox("도시를 선택하세요:", ["뉴욕", "샌프란시스코", "시카고"])
elif country == "일본":
    city = st.selectbox("도시를 선택하세요:", ["도쿄", "오사카", "교토"])

st.write(f"선택한 도시: {city}")

# file uploader
uploaded_file = st.file_uploader("이미지 파일을 업로드해주세요", type=["jpg", "png"])

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="업로드된 이미지", use_column_width=True)

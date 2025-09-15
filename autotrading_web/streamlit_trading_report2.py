import streamlit as st
from pykrx import stock
from datetime import datetime, timedelta
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px

# 스트림릿 페이지 설정
# st.set_page_config(page_title="주식 변동성 돌파 전략 백테스팅", layout="wide")

# 사이드바 설정
st.sidebar.title("입력 설정")

# 주식 종목 코드 입력
codes_input = st.sidebar.text_input("주식 종목 코드 (콤마로 구분)", "005930,000660")

# K값 입력
k_value_input = st.sidebar.text_input("K 값", "0.5")

# 파일 업로더 위젯
uploaded_file = st.sidebar.file_uploader("Choose a file")

# 데이터 가져오기 버튼
if st.sidebar.button("데이터 가져오기"):
    # K 값 및 종목 코드 처리
    k_value = float(k_value_input)
    codes = codes_input.split(",")

    # 날짜 계산
    end_date = datetime.today()
    start_date = end_date - timedelta(days=15)

    st.header("종목별 OHLC 차트와 매수목표가격")

    # 데이터 및 탭 컨테이너 준비
    tab_container = st.tabs([code.strip() for code in codes])

    for i, code in enumerate(codes):
        code = code.strip()
        with tab_container[i]:
            # 주식 데이터 가져오기
            df = stock.get_market_ohlcv_by_date(
                start_date.strftime("%Y%m%d"), end_date.strftime("%Y%m%d"), code
            )

            # 매수 목표가 계산을 위해 직전 날짜 데이터로 이동
            df["전일 고가"] = df["고가"].shift(1)
            df["전일 저가"] = df["저가"].shift(1)
            df["전일 종가"] = df["종가"].shift(1)
            df["목표가"] = (df["전일 고가"] - df["전일 저가"]) * k_value + df[
                "전일 종가"
            ]

            # Plotly 그래프 생성
            fig = go.Figure()

            # OHLC 차트 추가
            fig.add_trace(
                go.Candlestick(
                    x=df.index,
                    open=df["시가"],
                    high=df["고가"],
                    low=df["저가"],
                    close=df["종가"],
                    name="OHLC",
                )
            )

            # 매수 목표가 꺾은선 그래프 추가
            fig.add_trace(
                go.Scatter(
                    x=df.index,
                    y=df["목표가"],
                    mode="lines+markers",
                    name="목표가",
                    yaxis="y2",
                )
            )

            # 레이아웃 설정
            fig.update_layout(
                title=f"{code} 주식 데이터 및 매수 목표가",
                xaxis_title="날짜",
                yaxis_title="가격",
                yaxis=dict(
                    title="OHLC",
                    side="left",
                ),
                yaxis2=dict(title="목표가", overlaying="y", side="right"),
                xaxis=dict(rangeslider=dict(visible=False)),
            )

            st.plotly_chart(fig, use_container_width=True)

    st.divider()
    st.header("일별 종목 수익 차트")  # 임의추가
    st.write(
        """
        일별로 매매한 종목의 수익률과 손익금액에 대한 그래프를 한 차트에 그립니다.
        수익률은 꺾은선 그래프로 왼쪽 y축 값으로 확인할 수 있으며,
        손익금액은 막대 그래프로 오른쪽 y축에서 값을 확인할 수 있습니다.
        오른쪽의 범례를 클릭하면 특정 그래프를 숨기거나 보이게 할 수 있습니다.
        """
    )

    if uploaded_file is not None:
        # 파일 읽기
        df = pd.read_csv(uploaded_file)

        # NaN 값 제거
        df = df.dropna()

        # 기준날짜를 datetime 형식으로 변환
        df["기준날짜"] = pd.to_datetime(df["기준날짜"], format="%Y%m%d")

        # 그래프 생성을 위한 subplot 설정
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        unique_stocks = df["종목명"].unique()
        colors = px.colors.qualitative.Plotly

        # 종목별로 데이터를 처리하여 그래프에 추가
        for idx, stock in enumerate(unique_stocks):
            stock_data = df[df["종목명"] == stock]

            # 수익률 꺾은선 그래프
            fig.add_trace(
                go.Scatter(
                    x=stock_data["기준날짜"],
                    y=stock_data["수익률"],
                    name=f"{stock} 수익률",
                    line=dict(color=colors[idx % len(colors)]),
                ),
                secondary_y=False,
            )

            # 손익금액 막대 그래프
            fig.add_trace(
                go.Bar(
                    x=stock_data["기준날짜"],
                    y=stock_data["손익금액"],
                    name=f"{stock} 손익금액",
                    marker=dict(color=colors[idx % len(colors)]),
                ),
                secondary_y=True,
            )

        # 그래프 타이틀 및 축 제목 설정
        fig.update_layout(title_text="일별 수익률과 손익금액")
        fig.update_xaxes(title_text="기준 날짜")
        fig.update_yaxes(title_text="수익률 (%)", secondary_y=False)
        fig.update_yaxes(title_text="손익금액 (KRW)", secondary_y=True)

        # 그래프 표시
        st.plotly_chart(fig)

    else:
        st.write("파일을 업로드하면 분석을 시작합니다.")

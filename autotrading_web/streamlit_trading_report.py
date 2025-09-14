# streamlit_trading_dashboard.py
import streamlit as st
import pandas as pd
import datetime
from pykrx import stock
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(layout="wide", page_title="변동성 돌파 대시보드")

st.title("변동성 돌파 백테스트 대시보드 (pykrx + Streamlit)")

# ---------------------------
# Sidebar: 사용자 입력
# ---------------------------
with st.sidebar:
    st.header("데이터 입력")
    codes_input = st.text_input(
        "종목코드(콤마로 구분, 예: 005930,005380)", value="005930"
    )
    k_input = st.text_input("K 값 (예: 0.5)", value="0.5")
    fetch_button = st.button("데이터 가져오기")


# 유틸: 입력값 정리
def parse_codes(codes_str: str):
    return [c.strip() for c in codes_str.split(",") if c.strip()]


def parse_k(k_str: str):
    try:
        return float(k_str)
    except:
        return None


# ---------------------------
# 데이터 가져오기 함수 (캐시)
# ---------------------------
@st.cache_data(ttl=60 * 30)  # 30분 캐시(필요 시 변경)
def fetch_ohlcv_for_code(code: str, start_date: str, end_date: str) -> pd.DataFrame:
    """
    pykrx에서 지정 날짜 범위의 OHLCV를 받아와서 인덱스를 날짜로 하고 반환.
    start_date, end_date 포맷: 'YYYYMMDD'
    """
    df = stock.get_market_ohlcv_by_date(start_date, end_date, code)
    if df is None or df.empty:
        return pd.DataFrame()
    # 컬럼은 '시가','고가','저가','종가','거래량' 등
    df = df.reset_index()
    df.rename(columns={"index": "날짜"}, inplace=True)
    # 날짜를 datetime으로
    df["날짜"] = pd.to_datetime(df["날짜"])
    return df


# ---------------------------
# 메인 동작: 버튼 클릭 시 데이터 조회 및 출력
# ---------------------------
if fetch_button:
    codes = parse_codes(codes_input)
    k_value = parse_k(k_input)
    if not codes:
        st.sidebar.error("종목코드를 하나 이상 입력하세요.")
        st.stop()
    if k_value is None:
        st.sidebar.error("올바른 K 값을 입력하세요 (예: 0.5)")
        st.stop()

    # 날짜 범위 설정: today 기준으로 과거 15거래일을 확보하기 위해 calendar 16일 전부터 조회
    today = datetime.datetime.now().date()
    start_calendar = today - datetime.timedelta(days=16)  # 안전 마진으로 16일 전
    start_str = start_calendar.strftime("%Y%m%d")
    end_str = today.strftime("%Y%m%d")

    st.sidebar.info(f"{start_str} ~ {end_str} 기간의 데이터 요청을 시작합니다.")

    # 데이터 수집: 종목별로 데이터프레임 생성 및 목표가격 계산
    results = {}
    progress_text = st.sidebar.empty()
    progress_bar = st.sidebar.progress(0)

    for idx, code in enumerate(codes):
        progress_text.text(f"조회중: {code} ({idx+1}/{len(codes)})")
        df = fetch_ohlcv_for_code(code, start_str, end_str)

        if df.empty:
            st.warning(
                f"{code} 데이터가 없습니다. (거래일이 아니거나 종목코드 오류 가능)"
            )
            results[code] = pd.DataFrame()
            progress_bar.progress((idx + 1) / len(codes))
            continue

        # 목표가격 계산: X일의 목표가는 전일(X-1)의 데이터로 계산
        df = df.sort_values("날짜").reset_index(drop=True)

        # 전일 데이터 준비
        df["전일고가"] = df["고가"].shift(1)
        df["전일저가"] = df["저가"].shift(1)
        df["전일종가"] = df["종가"].shift(1)

        # 목표가 계산: ((전일고가 - 전일저가) * K + 전일종가)
        df["목표가"] = (df["전일고가"] - df["전일저가"]) * k_value + df["전일종가"]

        # 첫 행(shift로 인해 NaN)이 생기므로 필요시 제거하거나 NaN 허용
        # 우리는 시각화에서 NaN은 끊김으로 보여도 되므로 그대로 둠

        results[code] = df
        progress_bar.progress((idx + 1) / len(codes))

    progress_text.text("데이터 불러오기 완료")
    st.sidebar.success("데이터 로드 완료")

    # ---------------------------
    # 메인: 탭 레이아웃 (종목별)
    # ---------------------------
    tabs = st.tabs([f"{c}" for c in codes])

    for tab, code in zip(tabs, codes):
        df = results.get(code)
        with tab:
            st.subheader(f"{code} - 변동성 돌파 차트 (K={k_value})")
            if df is None or df.empty:
                st.write("데이터가 없습니다.")
                continue

            # 간단한 정보 표시
            st.write(
                f"데이터 기간: {df['날짜'].dt.date.min()} ~ {df['날짜'].dt.date.max()}"
            )
            st.dataframe(
                df[["날짜", "시가", "고가", "저가", "종가", "거래량", "목표가"]].tail(
                    10
                )
            )

            # Plotly: OHLC 캔들 + 목표가 라인 (y축 2개)
            fig = make_subplots(specs=[[{"secondary_y": True}]])
            # Candlestick 추가 (왼쪽 y축)
            fig.add_trace(
                go.Candlestick(
                    x=df["날짜"],
                    open=df["시가"],
                    high=df["고가"],
                    low=df["저가"],
                    close=df["종가"],
                    name="OHLC",
                ),
                secondary_y=False,
            )

            # 목표가 선 (오른쪽 y축) - 목표가가 NaN인 행은 자동으로 끊김
            fig.add_trace(
                go.Scatter(
                    x=df["날짜"],
                    y=df["목표가"],
                    mode="lines+markers",
                    name="목표가 (전일 기준)",
                    hovertemplate="%{x|%Y-%m-%d}: %{y:.0f}<extra></extra>",
                ),
                secondary_y=True,
            )

            # 레이아웃 조정
            fig.update_layout(
                height=600,
                xaxis_title="날짜",
                legend=dict(
                    orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
                ),
                margin=dict(l=10, r=10, t=40, b=40),
            )
            fig.update_xaxes(rangeslider_visible=False)

            # y축 제목 설정
            fig.update_yaxes(title_text="가격 (OHLC)", secondary_y=False)
            fig.update_yaxes(title_text="목표가", secondary_y=True)

            st.plotly_chart(fig, use_container_width=True)

else:
    st.info(
        "사이드바에서 종목코드와 K값을 입력하고 '데이터 가져오기' 버튼을 눌러주세요."
    )

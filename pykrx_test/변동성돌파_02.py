from pykrx import stock
import pandas as pd

# 삼성전자 주식 데이터 로드 (2025년 1월 1일부터 2025년 08월 12일까지)
df = stock.get_market_ohlcv_by_date(
    fromdate="20250101", todate="20250817", ticker="005930"
)


# 변동성 돌파 전략 구현
def volatility_breakout_strategy(df, k=0.5):
    df["range"] = df["고가"] - df["저가"]  # 전일 변동폭
    df["target"] = df["시가"] + (df["range"].shift(1) * k)  # 매수 목표가

    # 매수 시그널: 당일 고가가 목표가 이상이면 매수
    df["buy_signal"] = df["고가"] > df["target"]

    # 매도 시그널: 당일 종가에 매도
    df["sell_price"] = df["종가"]

    # 수익률 계산
    df["returns"] = 0
    df.loc[df["buy_signal"], "returns"] = df["sell_price"] / df["target"] - 1

    # 누적 수익률 계산
    df["cumulative_returns"] = (1 + df["returns"]).cumprod() - 1

    return df


result = volatility_breakout_strategy(df)
print(result)

# 누적 수익률 출력
print(f"누적 수익률: {result['cumulative_returns'].iloc[-1]}")

# import matplotlib.pyplot as plt

# # 누적 수익률 시각화
# plt.figure(figsize=(14, 7))
# result['cumulative_returns'].plot()
# plt.title('누적 수익률')
# plt.xlabel('날짜')
# plt.ylabel('누적 수익률 (%)')
# plt.grid(True)
# plt.show()

import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# 일별 수익률 시각화
plt.figure(figsize=(14, 7))

# 매수 신호가 있는 날짜만 필터링
buy_signals = result[result["buy_signal"]]

# 막대 그래프로 표현
plt.bar(buy_signals.index, buy_signals["returns"] * 100, color="green")

# 날짜 포맷 설정
plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
plt.gca().xaxis.set_major_locator(mdates.MonthLocator())

# 라벨, 제목, 그리드 설정
plt.xlabel("날짜")
plt.ylabel("일별 수익률 (%)")
plt.title("일별 수익률")
plt.xticks(rotation=45)
plt.grid(True)

plt.tight_layout()
plt.show()

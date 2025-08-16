import pandas as pd
from pykrx import stock
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt
from datetime import datetime

# 삼성전자 주식 데이터 불러오기
start_date = "2025-01-01"
end_date = "2025-08-01"
stock_code = "005930"  # 삼성전자
df = stock.get_market_ohlcv_by_date(
    fromdate=start_date, todate=end_date, ticker=stock_code
)

# 다음날 고가를 예측하기 위해 하루씩 미룬 고가 컬럼을 새로 생성
df["Next_High"] = df["고가"].shift(-1)

# 마지막 행은 다음날 데이터가 없으므로 제거
df = df[:-1]

# 특성과 타깃 분리
X = df.drop("Next_High", axis=1)
y = df["Next_High"]

# 훈련 세트와 테스트 세트 분리를 위한 날짜 변환
train_end = datetime(2025, 1, 15)
test_start = datetime(2025, 1, 16)

X_train = X.loc[:train_end]
y_train = y.loc[:train_end]
X_test = X.loc[test_start:]
y_test = y.loc[test_start:]

# 모델 학습
model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# 예측
predictions = model.predict(X_test)

# 실제 데이터와 예측 데이터 시각화
plt.figure(figsize=(14, 7))
plt.plot(
    df.index[df.index <= train_end],
    df.loc[df.index <= train_end, "고가"],
    label="Actual High Price",
    color="blue",
)
plt.plot(
    df.index[df.index >= test_start], y_test, "gx-", label="Actual High Price (Test)"
)
plt.plot(
    df.index[df.index >= test_start], predictions, "rx-", label="Predicted High Price"
)
plt.xlabel("Date")
plt.ylabel("High Price")
plt.title("Samsung Electronics Stock Price Prediction")
plt.legend()
plt.show()

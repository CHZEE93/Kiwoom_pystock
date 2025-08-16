import pandas as pd
from pykrx import stock
import numpy as np

# 1. 데이터 불러오기 (삼성전자: 005930)
start_date = "20250101"
end_date = "20250831"
ticker = "005930"

df = stock.get_market_ohlcv_by_date(fromdate=start_date, todate=end_date, ticker=ticker)
# 시가, 고가, 저가, 종가, 거래량 데이터 확보
# adjusted option 적용 가능하지만 기본은 수정주가 :contentReference[oaicite:0]{index=0}

# 2. 변동성 돌파 전략 변수 설정
# 이전일 범위 (고가 - 저가) * k 값을 기준으로 당일 돌파 여부 판단
k = 0.5

df['range'] = df['고가'] - df['저가']
df['target'] = df['시가'] + df['range'].shift(1) * k

# 3. 매수/매도 조건 정의
df['position'] = np.where(df['고가'] > df['target'], 1, 0)
df['returns'] = np.where(df['position'] == 1,
                         (df['종가'] / df['target']) - 1,
                         0)

# 4. 누적 수익률 계산
df['cum_returns'] = (1 + df['returns']).cumprod() - 1

# 출력
print(df[['시가','고가','저가','종가','target','position','returns','cum_returns']].tail())

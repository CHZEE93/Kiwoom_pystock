import sys
from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import QTimer, QTime
from pykiwoom.kiwoom import Kiwoom
from pykrx import stock
import datetime

# Qt Designer로 생성한 gui 파일 로드
form_class = uic.loadUiType(r"gui.ui")[0]


class MyWindow(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        # Kiwoom 로그인
        self.kiwoom = Kiwoom()
        self.kiwoom.CommConnect(block=True)

        # 버튼 연결
        self.button_start.clicked.connect(self.start_trading)
        self.button_stop.clicked.connect(self.stop_trading)

        # 타이머 설정
        self.timer = QTimer(self)  # 장 마감 체크용
        self.timer.timeout.connect(self.check_market_time)

        self.trade_timer = QTimer(self)  # 주식 현재가 조회용
        self.trade_timer.timeout.connect(self.trade_stocks)

    def start_trading(self):
        self.timer.start(1000 * 60)  # 1분마다 check_market_time 호출
        self.trade_timer.start(1000 * 17)  # 17초마다 trade_stocks 호출

    def stop_trading(self):
        self.timer.stop()
        self.trade_timer.stop()

    def check_market_time(self):
        now = QTime.currentTime()
        if now.toString("HHmm") >= "1500":  # 15시가 되면 매도
            self.timer.stop()
            self.trade_timer.stop()
            self.sell_all_stocks()

    def trade_stocks(self):
        codes = self.code_list.text().split(",")  # 종목 코드 분리
        k_value = float(self.k_value.text())  # K 값 입력 받기

        for code in codes:
            code = code.strip()
            if code:
                try:
                    # 현재가 및 종목명 조회
                    data = self.kiwoom.block_request(
                        "opt10001", 종목코드=code, output="주식기본정보", next=0
                    )
                    name = data["종목명"][0]
                    current_price = int(data["현재가"][0].replace(",", ""))

                    # === 현재가 로그 출력 ===
                    now = datetime.datetime.now().strftime("%H:%M:%S")
                    self.textboard.append(
                        f"[{now}] [{code}] [{name}] [{current_price}]"
                    )

                    # 직전 거래일 데이터 조회
                    yesterday_data = get_yesterday_ohlcv(code)
                    if yesterday_data is not None:
                        high = yesterday_data["고가"]
                        low = yesterday_data["저가"]
                        close = yesterday_data["종가"]
                        target_price = close + (high - low) * k_value

                        if current_price > target_price:
                            self.buy_stock(code, current_price, 1)

                except Exception as e:
                    self.textboard.append(f"[Error] {code}: {e}")

    def buy_stock(self, code, price, quantity):
        # 매수 로직 (현재는 로그만 출력)
        name = self.kiwoom.block_request(
            "opt10001", 종목코드=code, output="주식기본정보", next=0
        )["종목명"][0]
        self.buysell_log.append(
            f"[매수] [{code}] [{name}] [가격: {price}] [수량: {quantity}]"
        )

    def sell_all_stocks(self):
        self.buysell_log.append("15시가 되어 모든 주식을 매도합니다.")


def get_yesterday_ohlcv(code):
    today = datetime.datetime.now().strftime("%Y%m%d")
    # 최근 5영업일 데이터 조회
    df = stock.get_market_ohlcv_by_date("20240101", today, code)

    if df.empty:
        return None

    # 마지막 행이 오늘일 수 있으므로 직전 거래일은 -2번째 인덱스
    if len(df) >= 2:
        return df.iloc[-2]  # 직전 거래일
    else:
        return df.iloc[-1]  # 데이터가 하루뿐일 경우 예외 처리


if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindow = MyWindow()
    myWindow.show()
    sys.exit(app.exec_())

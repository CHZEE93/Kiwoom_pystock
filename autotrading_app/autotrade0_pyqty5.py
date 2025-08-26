import sys
from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import QTimer, QTime
from pykiwoom.kiwoom import Kiwoom
from pykrx import stock
import datetime
import time

# Qt Designer로 생성한 gui 파일 로드
form_class = uic.loadUiType(r"gui.ui")[0]


class MyWindow(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        # Kiwoom 로그인
        self.kiwoom = Kiwoom()
        self.kiwoom.CommConnect(block=True)

        # 매수 기록 저장용 딕셔너리
        self.bought_stocks = {}

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
        self.trade_timer.start(1000 * 5)  # 5초마다 trade_stocks 호출

    def stop_trading(self):
        self.timer.stop()
        self.trade_timer.stop()

    def check_market_time(self):
        now = QTime.currentTime()
        if now.toString("HHmm") >= "1500":  # 15시가 되면 매도 및 정지
            self.timer.stop()
            self.trade_timer.stop()
            self.sell_all_stocks()
            self.textboard.append(
                f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 장 마감: 매도 실행 및 현재가 조회 중지"
            )

    def trade_stocks(self):
        # 장 마감 이후에는 현재가 조회 및 매수 중단
        now = QTime.currentTime()
        if now.toString("HHmm") >= "1500":
            self.textboard.append(
                f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 장 마감: 현재가 조회 중지"
            )
            return

        # 오늘 날짜
        today = datetime.datetime.now().strftime("%Y%m%d")

        # 직전 거래일 조회
        yesterday = stock.get_nearest_business_day_in_a_week(today)
        codes = self.code_list.text().split(",")  # 종목 코드 분리
        k_value = float(self.k_value.text())  # K 값 입력 받기

        for code in codes:
            code = code.strip()
            if code:
                try:
                    # 이미 오늘 매수한 종목이면 건너뛰기
                    if code in self.bought_stocks and self.bought_stocks[code] == today:
                        continue

                    # 현재가 조회
                    data = self.kiwoom.block_request(
                        "opt10001", 종목코드=code, output="주식기본정보", next=0
                    )
                    current_price = int(data["현재가"][0].replace(",", ""))

                    # 현재가가 음수이면 양수로 변환
                    if current_price < 0:
                        current_price = abs(current_price)

                    name = data["종목명"][0]
                    self.textboard.append(
                        f"[{datetime.datetime.now().strftime('%H:%M:%S')}] "
                        f"[{code}] [{name}] [현재가: {current_price}]"
                    )

                    # 직전 거래일 데이터 조회
                    yesterday_data = stock.get_market_ohlcv_by_date(
                        yesterday, yesterday, code
                    )
                    if not yesterday_data.empty:
                        high = yesterday_data["고가"][0]
                        low = yesterday_data["저가"][0]
                        close = yesterday_data["종가"][0]
                        target_price = close + (high - low) * k_value

                        # 변동성 돌파 전략 실행
                        if current_price > target_price:
                            # 매수 주문
                            self.buy_stock(code, current_price, 1)

                            # 매수 성공 시 오늘 날짜 기록
                            self.bought_stocks[code] = today

                except Exception as e:
                    self.textboard.append(f"[Error] {code}: {e}")

    def buy_stock(self, code, price, quantity, market=False):
        """
        market=True  -> 시장가(호가구분 '03', price=0)
        market=False -> 지정가(호가구분 '00', price=지정가)
        """
        # 계좌번호 (여러 계좌가 반환되면 첫 번째 사용)
        acc_list = self.kiwoom.GetLoginInfo("ACCNO")
        account = acc_list[0] if isinstance(acc_list, list) else acc_list.split(";")[0]

        # 호가구분/가격
        hoga_gb = "03" if market else "00"
        order_price = 0 if market else int(price)

        # 위치 인자로 호출!
        ret = self.kiwoom.SendOrder(
            "신규매수",  # rqname
            "0101",  # screen_no (임의 4자리 문자열)
            account,  # acc_no
            1,  # order_type: 1 신규매수
            code,  # code
            int(quantity),  # qty
            int(order_price),  # price
            hoga_gb,  # hoga_gb
            "",  # org_order_no (신규주문은 빈 문자열)
        )

        # 결과 로그
        if ret == 0:
            self.buysell_log.append(
                f"[매수주문성공] [{code}] [가격:{order_price}] [수량:{quantity}] [시장가:{market}]"
            )
        else:
            self.buysell_log.append(f"[매수주문실패] [{code}] ret={ret}")

    def sell_all_stocks(self, market=True):
        """
        보유 종목 전량 매도
        market=True  -> 시장가
        market=False -> 지정가(현재가 기준)
        """
        acc_list = self.kiwoom.GetLoginInfo("ACCNO")
        account = acc_list[0] if isinstance(acc_list, list) else acc_list.split(";")[0]

        # 잔고 조회 (opw00018: 계좌평가잔고내역요청)
        # output 이름은 '계좌평가잔고개별합산'이 일반적입니다.
        df = self.kiwoom.block_request(
            "opw00018",
            계좌번호=account,
            비밀번호="",  # 비밀번호 저장 설정 시 공란 가능
            비밀번호입력매체구분="00",
            조회구분="2",  # 1: 합산, 2: 개별
            output="계좌평가잔고개별합산",
            next=0,
        )

        if df is None or df.empty:
            self.buysell_log.append("[INFO] 매도 대상 잔고가 없습니다.")
            return

        for i in range(len(df)):
            # 종목코드 컬럼명이 환경마다 다를 수 있어 안전하게 가져오기
            code_col = (
                "종목코드"
                if "종목코드" in df.columns
                else ("종목번호" if "종목번호" in df.columns else None)
            )
            if code_col is None:
                continue

            code = str(df.iloc[i][code_col]).strip().lstrip("A")
            qty_raw = str(df.iloc[i].get("보유수량", "0")).replace(",", "").strip()
            qty = int(qty_raw) if qty_raw.isdigit() else 0
            if qty <= 0:
                continue

            # 지정가 매도 가격: 현재가(양수화)
            if not market:
                cur = self.kiwoom.block_request(
                    "opt10001", 종목코드=code, output="주식기본정보", next=0
                )
                cur_price = abs(int(str(cur["현재가"][0]).replace(",", "")))
                price_to_sell = cur_price
                hoga_gb = "00"  # 지정가
            else:
                price_to_sell = 0
                hoga_gb = "03"  # 시장가

            # 위치 인자로 호출!
            ret = self.kiwoom.SendOrder(
                "신규매도",  # rqname
                "0102",  # screen_no
                account,  # acc_no
                2,  # order_type: 2 신규매도
                code,  # code
                int(qty),  # qty
                int(price_to_sell),  # price
                hoga_gb,  # hoga_gb
                "",  # org_order_no
            )

            if ret == 0:
                self.buysell_log.append(
                    f"[매도주문성공] [{code}] [수량:{qty}] [시장가:{market}] [가격:{price_to_sell}]"
                )
            else:
                self.buysell_log.append(f"[매도주문실패] [{code}] ret={ret}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindow = MyWindow()
    myWindow.show()
    sys.exit(app.exec_())

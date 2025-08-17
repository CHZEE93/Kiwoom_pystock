import sys
import time
import os

from datetime import datetime

from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import QTimer

from pykiwoom.kiwoom import Kiwoom


class StockApp(QMainWindow):
    def __init__(self):
        super().__init__()
        # QtDesigner에서 만든 UI 불러오기
        uic.loadUi("gui.ui", self)

        # Kiwoom 연결
        self.kiwoom = Kiwoom()
        self.kiwoom.CommConnect(block=True)

        # 타이머 준비
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_prices)

        # 버튼 연결
        self.button_start.clicked.connect(self.start_fetching)
        self.button_stop.clicked.connect(self.stop_fetching)

        # 상태 변수
        self.codes = []

    def start_fetching(self):
        """시작 버튼 클릭 시 동작"""
        input_text = self.code_list.text().strip()
        if not input_text:
            self.textboard.append("[Error] 종목코드를 입력하세요.")
            return

        # 입력받은 종목코드 (콤마로 구분)
        self.codes = [code.strip() for code in input_text.split(",") if code.strip()]

        if not self.codes:
            self.textboard.append("[Error] 올바른 종목코드를 입력하세요.")
            return

        self.textboard.append("[INFO] 조회 시작")
        self.timer.start(1000)  # 1초마다 update_prices 실행

    def stop_fetching(self):
        """중단 버튼 클릭 시 동작"""
        if self.timer.isActive():
            self.timer.stop()
            self.textboard.append("[INFO] 조회 중단")

    def update_prices(self):
        """1초마다 종목별 현재가 업데이트"""
        now = datetime.now().strftime("%H:%M:%S")

        for code in self.codes:
            try:
                # TR 요청 (opt10001: 주식기본정보요청)
                data = self.kiwoom.block_request(
                    "opt10001", 종목코드=code, output="주식기본정보", next=0
                )

                if not data.empty:
                    name = data["종목명"][0]
                    price = data["현재가"][0]
                    log = f"[{now}] [{code}] [{name}] [{price}]"
                    self.textboard.append(log)

            except Exception as e:
                self.textboard.append(f"[Error] {code}: {e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = StockApp()
    window.show()
    sys.exit(app.exec_())

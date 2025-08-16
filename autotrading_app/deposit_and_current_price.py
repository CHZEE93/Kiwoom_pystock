from pykiwoom.kiwoom import Kiwoom
import time

# Kiwoom 인스턴스 생성 및 로그인
kiwoom = Kiwoom()
kiwoom.CommConnect(block=True)  # 로그인 창 실행 (block=True 이면 로그인 완료까지 대기)

# 계좌 목록 가져오기
accounts = kiwoom.GetLoginInfo("ACCNO")
account_num = accounts[0]  # 여러 계좌가 있으면 첫 번째 계좌 선택co

print("계좌번호:", account_num)

# 예수금 조회
# SetInputValue: TR 입력값 설정
kiwoom.SetInputValue("계좌번호", account_num)
kiwoom.SetInputValue("비밀번호", "")  # 공란 가능 (사전 설정 필요)
kiwoom.SetInputValue("비밀번호입력매체구분", "00")
kiwoom.SetInputValue("조회구분", "2")  # 1: 합산, 2: 개별계좌

# TR 요청 (opw00001: 예수금상세현황요청)
kiwoom.CommRqData("예수금상세현황요청", "opw00001", 0, "2000")

# 데이터 가져오기 (CommGetData 대신 GetCommData 사용)
deposit = kiwoom.GetCommData("opw00001", "예수금상세현황요청", 0, "예수금")
print("예수금:", deposit.strip())

# 종목코드 리스트
codes = ["005930", "005380"]  # 삼성전자, 현대자동차

for code in codes:
    # block_request로 TR 요청
    data = kiwoom.block_request(
        "opt10001", 종목코드=code, output="주식기본정보", next=0  # 주식기본정보요청
    )

    # 현재가 가져오기
    current_price = data["현재가"][0]
    print(f"{code} 현재가: {current_price}")

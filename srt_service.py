"""
SRT 예매 백그라운드 Keep-Alive 서비스.
startForeground()를 통해 OS의 프로세스 강제 종료를 방지합니다.
예매 시작 시 활성화, 예매 종료 시 중단됩니다.
"""
import time

# p4a가 이 스크립트를 foreground 서비스로 실행하면서 startForeground()를 자동 호출.
# 루프만 유지하면 OS가 프로세스를 종료하지 않음.
while True:
    time.sleep(30)

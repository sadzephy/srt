# test_srt_limit.py - 1워커 장시간 안정성 테스트
import time
import random
from datetime import datetime
from SRT import SRT

MEMBER_NO = "2582560569"
PASSWORD  = "ys2love^^"

def make_srt():
    return SRT(MEMBER_NO, PASSWORD)

def ts():
    return f"{datetime.now().strftime('%H:%M:%S')} | {time.time()-start:.1f}초"

srt         = make_srt()
count       = 0
session_req = 0
new_session = 0
start       = time.time()

while True:
    try:
        srt.search_train("수서", "부산", "20260403", "0700", available_only=False)
        count       += 1
        session_req += 1
        print(f"[총{count} / 세션{session_req}] OK  |  {ts()}")
    except Exception as e:
        count       += 1
        session_req += 1
        err = str(e)
        print(f"[총{count} / 세션{session_req}] 오류: {err[:60]}  |  {ts()}")
        if "Blocked" in err or "abnormal" in err:
            delay = random.uniform(0, 2)
            print(f"  → 세션 차단. {delay:.1f}초 후 새 세션 생성...")
            time.sleep(delay)
            try:
                srt = make_srt()
                new_session += 1
                session_req  = 0
                print(f"  → 새 세션 완료 (누적 {new_session}회)")
            except Exception as se:
                print(f"  → 새 세션 실패: {se}")
    time.sleep(0)

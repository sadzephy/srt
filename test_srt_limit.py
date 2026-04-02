# test_srt_limit.py
import time
import threading
from datetime import datetime
from SRT import SRT

MEMBER_NO  = "2582560569"
PASSWORD   = "ys2love^^"
N_WORKERS  = 3  # 동시 실행 워커 수

def make_srt():
    return SRT(MEMBER_NO, PASSWORD)

lock        = threading.Lock()
total_count = [0]
start       = time.time()

def ts():
    return f"{datetime.now().strftime('%H:%M:%S')} | {time.time()-start:.1f}초"

def worker(worker_id):
    srt         = make_srt()
    session_req = 0
    new_session = 0

    while True:
        try:
            srt.search_train("수서", "부산", "20260403", "0700", available_only=False)
            session_req += 1
            with lock:
                total_count[0] += 1
                total = total_count[0]
            print(f"[W{worker_id}] 세션{session_req} / 총{total} OK  |  {ts()}")
        except Exception as e:
            session_req += 1
            with lock:
                total_count[0] += 1
                total = total_count[0]
            err = str(e)
            print(f"[W{worker_id}] 세션{session_req} / 총{total} 오류: {err[:50]}  |  {ts()}")
            if "Blocked" in err or "abnormal" in err:
                print(f"  [W{worker_id}] → 세션 차단. 새 SRT 객체 생성...")
                try:
                    srt = make_srt()
                    new_session += 1
                    session_req = 0
                    print(f"  [W{worker_id}] → 새 세션 완료 (누적 {new_session}회)")
                except Exception as se:
                    print(f"  [W{worker_id}] → 새 세션 실패: {se}")
        time.sleep(0)

threads = []
for i in range(N_WORKERS):
    t = threading.Thread(target=worker, args=(i+1,), daemon=True)
    threads.append(t)
    t.start()
    time.sleep(0.5)  # 워커 시작 간격

for t in threads:
    t.join()

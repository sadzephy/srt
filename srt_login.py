import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
import threading
import time
from SRT import SRT


STATIONS = [
    "수서", "동탄", "평택지제", "천안아산", "오송", "대전", "김천구미",
    "동대구", "서대구", "경주", "울산(통도사)", "부산", "포항",
    "광명", "서울", "공주", "익산", "정읍", "광주송정", "나주",
    "목포", "전주", "순천", "여수EXPO",
]
HOURS   = [f"{h:02d}" for h in range(24)]
MINUTES = ["00", "10", "20", "30", "40", "50"]



class SRTApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SRT 열차 예매")
        self.resizable(False, False)
        self._running  = False
        self._srt      = None
        self._trains   = []   # 조회된 열차 목록
        self._build_ui()

    # ── UI 구성 ────────────────────────────────────────────
    def _build_ui(self):
        pad = {"padx": 10, "pady": 5}

        # 로그인 정보
        tk.Label(self, text="회원번호").grid(row=0, column=0, **pad, sticky="e")
        self.member_no = ttk.Entry(self, width=20)
        self.member_no.insert(0, "2582560569")
        self.member_no.grid(row=0, column=1, **pad)

        tk.Label(self, text="비밀번호").grid(row=1, column=0, **pad, sticky="e")
        self.password = ttk.Entry(self, width=20, show="*")
        self.password.insert(0, "ys2love^^")
        self.password.grid(row=1, column=1, **pad)

        ttk.Separator(self, orient="horizontal").grid(
            row=2, column=0, columnspan=2, sticky="ew", padx=10, pady=4
        )

        # 검색 조건
        tk.Label(self, text="출발역").grid(row=3, column=0, **pad, sticky="e")
        self.dep = ttk.Combobox(self, values=STATIONS, state="readonly", width=18)
        self.dep.set("수서"); self.dep.grid(row=3, column=1, **pad)

        tk.Label(self, text="도착역").grid(row=4, column=0, **pad, sticky="e")
        self.arr = ttk.Combobox(self, values=STATIONS, state="readonly", width=18)
        self.arr.set("부산"); self.arr.grid(row=4, column=1, **pad)

        tk.Label(self, text="출발일").grid(row=5, column=0, **pad, sticky="e")
        dates = [(datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(30)]
        self.date = ttk.Combobox(self, values=dates, state="readonly", width=18)
        self.date.set(dates[1]); self.date.grid(row=5, column=1, **pad)

        tk.Label(self, text="출발시간").grid(row=6, column=0, **pad, sticky="e")
        tf = tk.Frame(self); tf.grid(row=6, column=1, **pad, sticky="w")
        self.hour = ttk.Combobox(tf, values=HOURS, state="readonly", width=4)
        self.hour.set("17"); self.hour.pack(side="left")
        tk.Label(tf, text=":").pack(side="left")
        self.minute = ttk.Combobox(tf, values=MINUTES, state="readonly", width=4)
        self.minute.set("00"); self.minute.pack(side="left")

        tk.Label(self, text="좌석").grid(row=7, column=0, **pad, sticky="e")
        self.seat = ttk.Combobox(self, values=["아무거나", "일반실", "특실"], state="readonly", width=18)
        self.seat.set("아무거나"); self.seat.grid(row=7, column=1, **pad)

        tk.Label(self, text="초당 호출").grid(row=8, column=0, **pad, sticky="e")
        rf = tk.Frame(self); rf.grid(row=8, column=1, **pad, sticky="w")
        self.rate = ttk.Spinbox(rf, from_=0.1, to=10.0, increment=0.1, width=5, format="%.1f")
        self.rate.set("2.0"); self.rate.pack(side="left")
        tk.Label(rf, text="회/초").pack(side="left", padx=(4, 0))

        # 조회 버튼
        tk.Button(
            self, text="열차 조회", command=self.search,
            bg="#333", fg="white", width=20, pady=5
        ).grid(row=9, column=0, columnspan=2, pady=(10, 4))

        # 열차 목록 (Treeview)
        tk.Label(self, text="조회 결과 - 예매할 열차를 선택하세요").grid(
            row=10, column=0, columnspan=2, sticky="w", padx=10
        )
        cols = ("열차번호", "출발", "도착", "일반실", "특실")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=6, selectmode="browse")
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=90, anchor="center")
        self.tree.grid(row=11, column=0, columnspan=2, padx=10, pady=4)

        # 예매 시작 / 중지 버튼
        bf = tk.Frame(self); bf.grid(row=12, column=0, columnspan=2, pady=8)
        self.start_btn = tk.Button(
            bf, text="예매 시작", command=self.start,
            bg="#6B0F3A", fg="white", width=14, pady=5, state="disabled"
        )
        self.start_btn.pack(side="left", padx=5)
        self.stop_btn = tk.Button(
            bf, text="중지", command=self.stop,
            bg="#555", fg="white", width=8, pady=5, state="disabled"
        )
        self.stop_btn.pack(side="left", padx=5)

        # 상태 / 로그
        self.status_var = tk.StringVar(value="대기 중")
        tk.Label(self, textvariable=self.status_var, fg="#6B0F3A").grid(
            row=13, column=0, columnspan=2
        )
        self.log_box = tk.Text(self, height=6, width=50, state="disabled")
        self.log_box.grid(row=14, column=0, columnspan=2, padx=10, pady=(2, 10))

    # ── 공통 유틸 ──────────────────────────────────────────
    def log(self, msg: str):
        self.log_box.config(state="normal")
        self.log_box.insert("end", msg + "\n")
        self.log_box.see("end")
        self.log_box.config(state="disabled")

    def _get_params(self):
        date_str = self.date.get().replace("-", "")
        hh, mm   = self.hour.get(), self.minute.get()
        api_hour = int(hh) if int(hh) % 2 == 0 else int(hh) - 1
        time_val = f"{api_hour:02d}0000"
        sel_dt   = datetime.strptime(f"{date_str}{hh}{mm}", "%Y%m%d%H%M")
        end_dt   = sel_dt + timedelta(hours=1)
        return date_str, hh, mm, time_val, sel_dt, end_dt

    def _in_range(self, train, date_str, sel_dt, end_dt) -> bool:
        try:
            t_dt = datetime.strptime(f"{date_str}{train.dep_time}", "%Y%m%d%H%M%S")
            return sel_dt <= t_dt < end_dt
        except Exception:
            return True

    def _login(self):
        if self._srt is None:
            member_no = self.member_no.get().strip()
            password  = self.password.get().strip()
            if not member_no or not password:
                raise ValueError("회원번호와 비밀번호를 입력하세요.")
            self.log("로그인 중...")
            self._srt = SRT(member_no, password)
            self.log("✅ 로그인 성공")

    # ── 열차 조회 ──────────────────────────────────────────
    def search(self):
        self.tree.delete(*self.tree.get_children())
        self._trains = []
        self.start_btn.config(state="disabled")

        try:
            self._login()
        except Exception as e:
            messagebox.showerror("로그인 실패", str(e)); return

        date_str, hh, mm, time_val, sel_dt, end_dt = self._get_params()
        dep, arr = self.dep.get(), self.arr.get()

        self.log(f"조회: {dep}→{arr} {hh}:{mm}~{end_dt.strftime('%H:%M')}")
        try:
            trains = self._srt.search_train(dep, arr, date_str, time_val, available_only=False)
        except Exception as e:
            err = str(e)
            if "Blocked" in err or "blocked" in err:
                messagebox.showwarning("IP 차단 중", "현재 IP가 차단되어 있습니다.\n잠시 후 다시 시도해 주세요.")
                return
            # 세션 만료(NetFunnel 등) 시 재로그인 후 재시도
            self.log("세션 만료 → 재로그인 후 재시도...")
            self._srt = None
            try:
                self._login()
                trains = self._srt.search_train(dep, arr, date_str, time_val, available_only=False)
            except Exception as e2:
                messagebox.showerror("조회 실패", str(e2)); return

        filtered = [t for t in trains if self._in_range(t, date_str, sel_dt, end_dt)]
        self._trains = filtered
        self.log(f"총 {len(filtered)}건 조회됨")

        for t in filtered:
            general = "예약가능" if t.general_seat_available() else "매진"
            special = "예약가능" if t.special_seat_available() else "매진"
            dep_t   = f"{t.dep_time[:2]}:{t.dep_time[2:4]}"
            arr_t   = f"{t.arr_time[:2]}:{t.arr_time[2:4]}"
            self.tree.insert("", "end", values=(t.train_number, dep_t, arr_t, general, special))

        if filtered:
            self.tree.selection_set(self.tree.get_children()[0])
            self.start_btn.config(state="normal")

    # ── 예매 시작/중지 ─────────────────────────────────────
    def start(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("선택 필요", "예매할 열차를 선택하세요."); return

        idx = self.tree.index(sel[0])
        self._target_train = self._trains[idx]
        self.log(f"\n▶ 예매 대상: {self._target_train.train_number}호 "
                 f"{self._target_train.dep_time[:2]}:{self._target_train.dep_time[2:4]} 출발")

        self._running = True
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        threading.Thread(target=self._reserve_loop, daemon=True).start()

    def stop(self):
        self._running = False
        self.status_var.set("중지됨")
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")

    # ── 세션 차단 시 재로그인 ──────────────────────────────
    def _relogin(self):
        self.log("⛔ 세션 차단 감지 → 재로그인 시도...")
        self._srt = None
        try:
            self._login()
            self.log("✅ 재로그인 성공 → 예매 재개")
        except Exception as e:
            self.log(f"재로그인 실패: {e}")

    # ── 예매 반복 루프 ─────────────────────────────────────
    def _reserve_loop(self):
        date_str, hh, mm, time_val, sel_dt, end_dt = self._get_params()
        dep, arr, seat = self.dep.get(), self.arr.get(), self.seat.get()
        attempt  = 0
        sec_start = time.time()
        sec_count = 0   # 현재 초 내 호출 횟수

        while self._running:
            attempt  += 1
            sec_count += 1

            # 1초마다 실제 호출 속도 표시
            elapsed = time.time() - sec_start
            if elapsed >= 1.0:
                self.status_var.set(f"예매 시도 {attempt}회 | 초당 {sec_count / elapsed:.1f}회")
                sec_start = time.time()
                sec_count = 0

            t0 = time.time()
            try:
                trains = self._srt.search_train(dep, arr, date_str, time_val, available_only=False)
                target = next(
                    (t for t in trains if t.train_number == self._target_train.train_number),
                    None
                )
                api_ms = int((time.time() - t0) * 1000)

                if target is None:
                    self.log(f"[{attempt}] 열차 정보 없음 ({api_ms}ms)")
                elif not (target.general_seat_available() or target.special_seat_available()):
                    self.log(f"[{attempt}] 매진 ({api_ms}ms)")
                else:
                    if seat == "아무거나":
                        special = target.special_seat_available()
                    else:
                        special = (seat == "특실")
                    rsv = self._srt.reserve(target, special_seat=special)
                    self.log(f"✅ 예매 성공! ({attempt}회 시도)\n{rsv}")
                    self.status_var.set("✅ 예매 완료!")
                    messagebox.showinfo("예매 완료", f"예매 완료!\n{rsv}")
                    self.stop()
                    return
            except Exception as e:
                err = str(e)
                if "Blocked" in err or "blocked" in err:
                    self._relogin()
                    sec_start = time.time()
                    sec_count = 0
                else:
                    self.log(f"[{attempt}] 오류: {e}")

            if not self._running:
                return
            try:
                rate = float(self.rate.get())
                sleep_sec = max(0.01, 1.0 / rate - 0.43)
            except ValueError:
                sleep_sec = 0.07
            time.sleep(sleep_sec)


if __name__ == "__main__":
    app = SRTApp()
    app.mainloop()

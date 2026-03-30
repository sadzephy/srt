import os
os.environ["KIVY_NO_CONSOLELOG"] = "1"
import logging
logging.getLogger("kivy").setLevel(logging.WARNING)
from kivy.logger import Logger
Logger.setLevel(logging.WARNING)

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.effects.scroll import ScrollEffect
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.widget import Widget
from kivy.uix.modalview import ModalView
from kivy.uix.image import Image as KvImage
from kivy.clock import mainthread, Clock
from kivy.metrics import dp
from kivy.graphics import Color, RoundedRectangle, Rectangle, Ellipse
from kivy.core.text import LabelBase
from kivy.resources import resource_add_path, resource_find
from datetime import datetime, timedelta
import calendar as cal_module
import threading
import time
from SRT import SRT

# ── 폰트 ──────────────────────────────────────────────────
for _p in [
    os.path.dirname(os.path.abspath(__file__)),
    os.environ.get("ANDROID_ARGUMENT", ""),
    os.environ.get("ANDROID_PRIVATE", ""),
]:
    if _p:
        resource_add_path(_p)

for _fp in [
    resource_find("NanumSquareRoundEB.ttf"),
    resource_find("NanumGothic.ttf"),
    "/system/fonts/NotoSansCJK-Regular.ttc",
    "/system/fonts/DroidSansFallback.ttf",
    "C:/Windows/Fonts/malgun.ttf",
    "C:/Windows/Fonts/gulim.ttc",
]:
    if _fp and os.path.exists(_fp):
        try:
            LabelBase.register(name="Roboto", fn_regular=_fp)
            break
        except Exception:
            pass

# ── 데이터 ─────────────────────────────────────────────────
STATIONS = [
    "수서", "동탄", "평택지제", "천안아산", "오송", "대전", "김천구미",
    "동대구", "서대구", "경주", "울산(통도사)", "부산", "포항",
    "광명", "서울", "공주", "익산", "정읍", "광주송정", "나주",
    "목포", "전주", "순천", "여수EXPO",
]
HOURS = [f"{h:02d}" for h in range(24)]

# ── 팔레트 ─────────────────────────────────────────────────
BG       = (0.91, 0.88, 0.97, 1)
WHITE    = (1,    1,    1,    1)
PRIMARY  = (0.38, 0.18, 0.62, 1)
ACCENT_B = (0.80, 0.88, 1.0,  1)
ACCENT_G = (0.82, 0.95, 0.86, 1)
ACCENT_Y = (1.0,  0.94, 0.78, 1)
ACCENT_P = (0.88, 0.82, 1.0,  1)
GRAY1    = (0.45, 0.40, 0.55, 1)
GRAY2    = (0.85, 0.83, 0.92, 1)
DARK     = (0.12, 0.08, 0.20, 1)
LIGHT_BG = (0.96, 0.94, 0.99, 1)


# ── 공통 헬퍼 ──────────────────────────────────────────────
class RoundBox(BoxLayout):
    def __init__(self, radius=16, bg=WHITE, shadow=True, **kw):
        super().__init__(**kw)
        self._r = radius; self._bg = bg; self._sh = shadow
        self.bind(pos=self._draw, size=self._draw)

    def _draw(self, *_):
        self.canvas.before.clear()
        with self.canvas.before:
            if self._sh:
                Color(0, 0, 0, 0.06)
                RoundedRectangle(pos=(self.x+dp(2), self.y-dp(3)),
                                 size=(self.width-dp(4), self.height), radius=[dp(self._r)])
            Color(*self._bg)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(self._r)])


def lbl(text, size=14, color=DARK, bold=False, halign="left", **kw):
    l = Label(text=text, font_size=dp(size), color=color, bold=bold,
              halign=halign, valign="middle", **kw)
    l.bind(size=l.setter("text_size"))
    return l


class PillButton(Button):
    def __init__(self, text, bg=DARK, fg=WHITE, **kw):
        kw.setdefault("height", dp(56))
        kw.setdefault("font_size", dp(18))
        kw.setdefault("bold", True)
        super().__init__(text=text, background_normal="",
                         background_color=(0,0,0,0), color=fg,
                         disabled_color=(0.6, 0.6, 0.6, 1),
                         size_hint_y=None, **kw)
        self._bg  = bg
        self._fg  = fg
        self.bind(pos=self._draw, size=self._draw,
                  disabled=self._on_disabled)

    def _on_disabled(self, *_):
        self.color = (0.8, 0.8, 0.8, 1) if self.disabled else self._fg
        Clock.schedule_once(self._draw, 0)

    def _draw(self, *_):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*((0.38, 0.36, 0.48, 1) if self.disabled else self._bg))
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(28)])


class FieldBtn(Button):
    """탭하면 팝업이 열리는 필드"""
    def __init__(self, text, **kw):
        super().__init__(text=text, background_normal="",
                         background_color=(0,0,0,0), color=DARK,
                         font_size=dp(16), bold=True,
                         size_hint_y=None, height=dp(36),
                         halign="center", **kw)


class FieldCard(RoundBox):
    def __init__(self, label_text, widget, **kw):
        super().__init__(orientation="vertical",
                         padding=[dp(12), dp(6), dp(12), dp(6)],
                         spacing=dp(2), size_hint_y=None, height=dp(62),
                         radius=14, bg=WHITE, **kw)
        self.add_widget(lbl(label_text, size=11, color=GRAY1, bold=True,
                            size_hint_y=None, height=dp(16)))
        self.add_widget(widget)


class TrainRow(ToggleButton):
    def __init__(self, text, index, accent=ACCENT_B, **kw):
        super().__init__(text=text, group="trains",
                         background_normal="", background_down="",
                         background_color=(0,0,0,0), color=DARK,
                         font_size=dp(14), bold=True,
                         size_hint_y=None, height=dp(54), **kw)
        self.train_index = index
        self._accent = accent
        self._sel = False
        self.bind(pos=self._draw, size=self._draw, state=self._on_state)

    def _on_state(self, *_):
        self._sel = (self.state == "down"); self._draw()

    def _draw(self, *_):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*(self._accent if self._sel else WHITE))
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(14)])


# ── 역 선택 팝업 ────────────────────────────────────────────
class StationPickerPopup(ModalView):
    def __init__(self, dep, arr, callback, **kw):
        super().__init__(background_color=(0,0,0,0.45),
                         size_hint=(1,1), **kw)
        self._dep = dep
        self._arr = arr
        self._mode = "dep"   # "dep" or "arr"
        self._callback = callback
        self._build()

    def _build(self):
        outer = BoxLayout(orientation="vertical", size_hint=(0.95, 0.88),
                          pos_hint={"center_x": 0.5, "center_y": 0.54})
        with outer.canvas.before:
            Color(*WHITE)
            self._bg = RoundedRectangle(radius=[dp(20)])
        outer.bind(pos=lambda *_: setattr(self._bg, "pos", outer.pos),
                   size=lambda *_: setattr(self._bg, "size", outer.size))

        # 타이틀
        title_row = BoxLayout(size_hint_y=None, height=dp(54), padding=[dp(16),0,dp(8),0])
        title_row.add_widget(lbl("역선택", size=18, bold=True, halign="center"))
        x_btn = Button(text="✕", size_hint=(None,None), size=(dp(44),dp(44)),
                       background_normal="", background_color=(0,0,0,0),
                       color=GRAY1, font_size=dp(20))
        x_btn.bind(on_press=lambda _: self.dismiss())
        title_row.add_widget(x_btn)
        outer.add_widget(title_row)

        # 출발/도착 탭
        tab = BoxLayout(size_hint_y=None, height=dp(64),
                        padding=[dp(12),dp(8),dp(12),dp(8)], spacing=dp(10))
        self._dep_btn = self._tab_btn("출발", self._dep, active=True)
        self._arr_btn = self._tab_btn("도착", self._arr, active=False)
        self._dep_btn.bind(on_press=lambda _: self._set_mode("dep"))
        self._arr_btn.bind(on_press=lambda _: self._set_mode("arr"))
        tab.add_widget(self._dep_btn)
        tab.add_widget(Widget(size_hint_x=None, width=dp(32)))
        tab.add_widget(self._arr_btn)
        outer.add_widget(tab)

        # 역 그리드
        scroll = ScrollView()
        grid = GridLayout(cols=3, size_hint_y=None, spacing=dp(4),
                          padding=[dp(10),dp(4),dp(10),dp(4)])
        grid.bind(minimum_height=grid.setter("height"))
        for st in STATIONS:
            btn = Button(text=st, size_hint_y=None, height=dp(52),
                         background_normal="", background_color=LIGHT_BG,
                         color=DARK, font_size=dp(16), bold=True)
            btn.bind(on_press=self._on_station)
            grid.add_widget(btn)
        scroll.add_widget(grid)
        outer.add_widget(scroll)

        # 선택하기 버튼
        sel = PillButton("선택하기", bg=PRIMARY, height=dp(60))
        sel.bind(on_press=self._confirm)
        outer.add_widget(sel)

        self.add_widget(outer)

    def _tab_btn(self, subtitle, value, active):
        box = RoundBox(orientation="vertical", radius=12,
                       bg=PRIMARY if active else LIGHT_BG,
                       shadow=False, size_hint_x=1,
                       padding=[dp(8),dp(4)])
        box.add_widget(lbl(subtitle, size=11,
                           color=WHITE if active else GRAY1,
                           halign="center", size_hint_y=None, height=dp(16)))
        box.add_widget(lbl(value, size=18, bold=True,
                           color=WHITE if active else DARK,
                           halign="center", size_hint_y=None, height=dp(28)))
        return box

    def _set_mode(self, mode):
        self._mode = mode
        # 탭 색상 전환
        for box, active in [(self._dep_btn, mode=="dep"),
                            (self._arr_btn, mode=="arr")]:
            box._bg = PRIMARY if active else LIGHT_BG
            box._draw()
            for child in box.children:
                child.color = WHITE if active else (GRAY1 if child.font_size < dp(16) else DARK)

    def _on_station(self, btn):
        if self._mode == "dep":
            self._dep = btn.text
        else:
            self._arr = btn.text
        # 탭 텍스트 갱신
        self._refresh_tab(self._dep_btn, self._dep, self._mode=="dep")
        self._refresh_tab(self._arr_btn, self._arr, self._mode=="arr")
        # 자동으로 반대편으로 전환
        self._set_mode("arr" if self._mode == "dep" else "dep")

    def _refresh_tab(self, box, value, active):
        kids = list(reversed(box.children))
        if len(kids) >= 2:
            kids[1].text = value

    def _confirm(self, *_):
        self._callback(self._dep, self._arr)
        self.dismiss()


# ── 날짜/시간 선택 팝업 ─────────────────────────────────────
class DateTimePickerPopup(ModalView):
    def __init__(self, date_str, hour, callback, **kw):
        super().__init__(background_color=(0,0,0,0.45), size_hint=(1,1), **kw)
        # date_str: "YYYY-MM-DD"
        d = datetime.strptime(date_str, "%Y-%m-%d")
        self._year  = d.year
        self._month = d.month
        self._day   = d.day
        self._hour  = int(hour)
        self._callback = callback
        self._day_btns  = {}
        self._hour_btns = {}
        self._build()

    def _build(self):
        outer = BoxLayout(orientation="vertical", size_hint=(0.95, None),
                          pos_hint={"center_x": 0.5, "center_y": 0.5})
        with outer.canvas.before:
            Color(*WHITE)
            self._bg = RoundedRectangle(radius=[dp(20)])
        outer.bind(pos=lambda *_: setattr(self._bg, "pos", outer.pos),
                   size=lambda *_: setattr(self._bg, "size", outer.size),
                   minimum_height=outer.setter("height"))

        # 타이틀
        tr = BoxLayout(size_hint_y=None, height=dp(54), padding=[dp(16),0,dp(8),0])
        tr.add_widget(lbl("출발일시", size=18, bold=True, halign="center"))
        x = Button(text="✕", size_hint=(None,None), size=(dp(44),dp(44)),
                   background_normal="", background_color=(0,0,0,0),
                   color=GRAY1, font_size=dp(20))
        x.bind(on_press=lambda _: self.dismiss())
        tr.add_widget(x)
        outer.add_widget(tr)

        # 월 네비 (스크롤 없이 전체 표시)
        self._cal_box = BoxLayout(orientation="vertical", size_hint_y=None)
        self._cal_box.bind(minimum_height=self._cal_box.setter("height"))
        self._render_calendar()
        outer.add_widget(self._cal_box)

        # 구분선
        sep = Widget(size_hint_y=None, height=dp(1))
        with sep.canvas:
            Color(*GRAY2)
            Rectangle(pos=sep.pos, size=sep.size)
        sep.bind(pos=lambda *_: None, size=lambda *_: None)
        outer.add_widget(sep)

        # 시간 선택
        time_hdr = BoxLayout(size_hint_y=None, height=dp(36),
                             padding=[dp(14),0])
        time_hdr.add_widget(lbl("⏰ 시간선택", size=14, bold=True, color=DARK))
        self._hour_lbl = lbl(f"{self._hour:02d}시 이후", size=14,
                              bold=True, color=PRIMARY, halign="right")
        time_hdr.add_widget(self._hour_lbl)
        outer.add_widget(time_hdr)

        hour_scroll = ScrollView(size_hint_y=None, height=dp(64))
        hour_row = BoxLayout(size_hint_x=None, spacing=dp(6), padding=[dp(10),dp(8)])
        hour_row.bind(minimum_width=hour_row.setter("width"))
        self._hour_btns = {}
        for h in range(24):
            hb = ToggleButton(text=f"{h:02d}시", group="hours",
                              size_hint=(None,None), size=(dp(64),dp(48)),
                              background_normal="", background_down="",
                              background_color=(0,0,0,0),
                              color=DARK, font_size=dp(15), bold=True)
            hb.hour = h
            if h == self._hour:
                hb.state = "down"
            hb.bind(on_press=self._on_hour, pos=self._draw_hour_btn,
                    size=self._draw_hour_btn, state=self._draw_hour_btn)
            self._draw_hour_btn(hb)
            hour_row.add_widget(hb)
            self._hour_btns[h] = hb
        hour_scroll.add_widget(hour_row)
        outer.add_widget(hour_scroll)

        # 선택완료 버튼
        done = PillButton("선택완료", bg=PRIMARY, height=dp(60))
        done.bind(on_press=self._confirm)
        outer.add_widget(done)

        self.add_widget(outer)

    def _render_calendar(self):
        self._cal_box.clear_widgets()
        self._day_btns = {}
        today = datetime.now().date()
        max_date = today + timedelta(days=29)

        # 월 헤더
        nav = BoxLayout(size_hint_y=None, height=dp(48), padding=[dp(8),0])
        prev = Button(text="이전월", size_hint=(None,1), width=dp(72),
                      background_normal="", background_color=LIGHT_BG,
                      color=DARK, font_size=dp(13), bold=True)
        prev.bind(on_press=lambda _: self._change_month(-1))
        nav.add_widget(prev)
        nav.add_widget(lbl(f"{self._year}.{self._month}", size=18, bold=True,
                           halign="center"))
        nxt = Button(text="다음월", size_hint=(None,1), width=dp(72),
                     background_normal="", background_color=LIGHT_BG,
                     color=DARK, font_size=dp(13), bold=True)
        nxt.bind(on_press=lambda _: self._change_month(1))
        nav.add_widget(nxt)
        self._cal_box.add_widget(nav)

        # 요일 헤더
        dow = GridLayout(cols=7, size_hint_y=None, height=dp(36))
        for i, d in enumerate(["일","월","화","수","목","금","토"]):
            c = (0.85,0.2,0.2,1) if i==0 else (0.2,0.3,0.85,1) if i==6 else GRAY1
            dow.add_widget(lbl(d, size=13, bold=True, color=c, halign="center",
                               size_hint_y=None, height=dp(36)))
        self._cal_box.add_widget(dow)

        # 날짜 그리드 (일요일 시작)
        cal = cal_module.Calendar(firstweekday=6).monthdayscalendar(self._year, self._month)
        for week in cal:
            row = GridLayout(cols=7, size_hint_y=None, height=dp(48))
            for i, day in enumerate(week):
                if day == 0:
                    row.add_widget(Widget())
                    continue
                d        = datetime(self._year, self._month, day).date()
                disabled = d < today or d > max_date
                is_today = (d == today)
                is_sel   = (day == self._day)
                base_color = (0.78, 0.76, 0.82, 1) if disabled else \
                             ((0.85, 0.2, 0.2, 1) if i == 0 else
                              (0.2, 0.3, 0.85, 1) if i == 6 else DARK)
                btn = Button(text=str(day),
                             background_normal="", background_color=(0, 0, 0, 0),
                             color=base_color,
                             font_size=dp(15), bold=(is_today or is_sel))
                btn.day            = day
                btn._is_sel        = is_sel
                btn._is_today      = is_today
                btn._base_color    = base_color
                btn._disabled_date = disabled
                if not disabled:
                    btn.bind(on_press=self._on_day)
                # pos/size 변경 시 재렌더 (초기 pos=0,0 문제 해결)
                btn.bind(
                    pos=lambda b, *_: self._draw_day_btn(b, b._is_sel, b._is_today),
                    size=lambda b, *_: self._draw_day_btn(b, b._is_sel, b._is_today),
                )
                row.add_widget(btn)
                self._day_btns[day] = (btn, is_today)
            self._cal_box.add_widget(row)

    def _draw_day_btn(self, btn, selected, is_today):
        btn.canvas.before.clear()
        inset = dp(4)
        with btn.canvas.before:
            if selected and not getattr(btn, '_disabled_date', False):
                Color(*PRIMARY)
                Ellipse(pos=(btn.x + inset, btn.y + inset),
                        size=(btn.width - inset*2, btn.height - inset*2))
                btn.color = WHITE
            elif is_today:
                Color(*ACCENT_P)
                Ellipse(pos=(btn.x + inset, btn.y + inset),
                        size=(btn.width - inset*2, btn.height - inset*2))
                btn.color = getattr(btn, '_base_color', DARK)
            else:
                btn.color = getattr(btn, '_base_color', DARK)

    def _on_day(self, btn):
        old_day = self._day
        self._day = btn.day
        if old_day in self._day_btns:
            ob, ot = self._day_btns[old_day]
            ob._is_sel = False
            self._draw_day_btn(ob, False, ot)
        btn._is_sel = True
        self._draw_day_btn(btn, True, False)

    def _change_month(self, delta):
        m = self._month + delta
        y = self._year
        if m > 12: m = 1;  y += 1
        if m < 1:  m = 12; y -= 1
        self._year = y; self._month = m
        self._render_calendar()

    def _draw_hour_btn(self, btn, *_):
        btn.canvas.before.clear()
        with btn.canvas.before:
            if btn.state == "down":
                Color(*PRIMARY)
                btn.color = WHITE
            else:
                Color(*LIGHT_BG)
                btn.color = DARK
            RoundedRectangle(pos=btn.pos, size=btn.size, radius=[dp(12)])

    def _on_hour(self, btn):
        self._hour = btn.hour
        self._hour_lbl.text = f"{self._hour:02d}시 이후"
        for hb in self._hour_btns.values():
            self._draw_hour_btn(hb)

    def _confirm(self, *_):
        date_str = f"{self._year}-{self._month:02d}-{self._day:02d}"
        self._callback(date_str, f"{self._hour:02d}")
        self.dismiss()


# ── 메인 위젯 ──────────────────────────────────────────────
class SRTWidget(BoxLayout):
    def __init__(self, **kw):
        super().__init__(orientation="vertical", padding=dp(18), spacing=dp(10), **kw)
        self._running      = False
        self._srt          = None
        self._trains       = []
        self._target_train = None
        self._selected_row = None
        self._wake_lock    = None
        self._wifi_lock    = None
        self._alarm_player    = None
        self._vibrator        = None
        self._dep = "수서"; self._arr = "부산"
        self._date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        self._hour = "17"
        self._build_ui()
        self._load_settings()

    def _spacer(self, h=8):
        return Widget(size_hint_y=None, height=dp(h))

    # ── 카드 암호화 ─────────────────────────────────────────────
    def _enc_key(self):
        import hashlib
        try:
            from jnius import autoclass
            PA     = autoclass("org.kivy.android.PythonActivity")
            Secure = autoclass("android.provider.Settings$Secure")
            aid    = Secure.getString(PA.mActivity.getContentResolver(), "android_id") or "srt"
        except Exception:
            aid = "srt_default"
        return hashlib.sha256(aid.encode()).digest()

    def _settings_path(self):
        try:
            from jnius import autoclass
            PA = autoclass("org.kivy.android.PythonActivity")
            return os.path.join(PA.mActivity.getFilesDir().getAbsolutePath(), "settings.enc")
        except Exception:
            return os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.enc")

    def _save_settings(self):
        import json, base64
        try:
            from Crypto.Cipher import AES
            from Crypto.Util.Padding import pad
            data = {
                "member_no":    self.member_no.text,
                "password":     self.password.text,
                "dep":          self._dep,
                "arr":          self._arr,
                "date":         self._date,
                "hour":         self._hour,
                "seat":         self._seat_val,
                "rate":         self.rate.text,
                "card_number":  self.card_number.text,
                "card_pw":      self.card_pw.text,
                "card_birth":   self.card_birth.text,
                "card_expire":  self.card_expire.text,
            }
            iv = os.urandom(16)
            cipher = AES.new(self._enc_key(), AES.MODE_CBC, iv)
            ct = cipher.encrypt(pad(json.dumps(data).encode(), AES.block_size))
            with open(self._settings_path(), "wb") as f:
                f.write(base64.b64encode(iv + ct))
        except ImportError:
            pass  # pycryptodome 미설치 시 무시
        except Exception as e:
            self.log(f"설정 저장 실패: {e}")

    def _load_settings(self):
        import json, base64
        try:
            from Crypto.Cipher import AES
            from Crypto.Util.Padding import unpad
            path = self._settings_path()
            if not os.path.exists(path):
                return
            with open(path, "rb") as f:
                raw = base64.b64decode(f.read())
            iv, ct = raw[:16], raw[16:]
            d = json.loads(unpad(AES.new(self._enc_key(), AES.MODE_CBC, iv)
                                 .decrypt(ct), AES.block_size).decode())
            if d.get("member_no"):   self.member_no.text    = d["member_no"]
            if d.get("password"):    self.password.text     = d["password"]
            if d.get("dep"):
                self._dep = d["dep"];  self._dep_btn.text   = d["dep"]
            if d.get("arr"):
                self._arr = d["arr"];  self._arr_btn.text   = d["arr"]
            if d.get("date"):        self._date             = d["date"]
            if d.get("hour"):        self._hour             = d["hour"]
            if d.get("date") or d.get("hour"):
                self._datetime_btn.text = f"{self._date}  {self._hour}:00"
            if d.get("seat"):
                self._seat_val = d["seat"]; self._seat_btn.text = d["seat"]
            if d.get("rate"):        self.rate.text         = d["rate"]
            if d.get("card_number"): self.card_number.text  = d["card_number"]
            if d.get("card_pw"):     self.card_pw.text      = d["card_pw"]
            if d.get("card_birth"):  self.card_birth.text   = d["card_birth"]
            if d.get("card_expire"): self.card_expire.text  = d["card_expire"]
        except Exception:
            pass

    def _save_card(self):
        self._save_settings()
        self.log("💳 카드 정보 암호화 저장 완료")

    def _load_card(self):
        return {
            "number":   self.card_number.text.strip(),
            "password": self.card_pw.text.strip(),
            "birth":    self.card_birth.text.strip(),
            "expire":   self.card_expire.text.strip(),
        }

    def _build_ui(self):
        with self.canvas.before:
            Color(*BG)
            self._bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=lambda *a: setattr(self._bg, "pos", self.pos),
                  size=lambda *a: setattr(self._bg, "size", self.size))

        # 타이틀
        tb = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(60),
                       spacing=dp(12), padding=(dp(4), 0, 0, 0))
        _icon_path = resource_find("icon.png") or os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "icon.png")
        if _icon_path and os.path.exists(_icon_path):
            _icon = KvImage(source=_icon_path, size_hint=(None, None),
                            size=(dp(52), dp(52)))
            tb.add_widget(_icon)
        tb.add_widget(lbl("파덕이의 SRT 예매", size=26, color=PRIMARY, bold=True,
                          size_hint_y=None, height=dp(60)))
        self.add_widget(tb)

        # ── 로그인 ──
        self.add_widget(lbl("로그인 정보", size=12, color=GRAY1, bold=True,
                            size_hint_y=None, height=dp(20)))
        self.member_no = TextInput(
            text="2582560569", multiline=False, font_size=dp(16),
            background_normal="", background_active="",
            background_color=(0,0,0,0), foreground_color=DARK,
            size_hint_y=None, height=dp(36),
            padding=[dp(10), dp(8), dp(10), dp(8)],
        )
        self.password = TextInput(
            text="ys2love^^", password=True, multiline=False, font_size=dp(16),
            background_normal="", background_active="",
            background_color=(0,0,0,0), foreground_color=DARK,
            size_hint_y=None, height=dp(36),
            padding=[dp(10), dp(8), dp(10), dp(8)],
        )
        self.add_widget(FieldCard("회원번호", self.member_no))
        self.add_widget(FieldCard("비밀번호", self.password))

        self.add_widget(self._spacer(4))

        # ── 결제 정보 ──
        self.add_widget(lbl("결제 정보 (자동결제용)", size=12, color=GRAY1, bold=True,
                            size_hint_y=None, height=dp(20)))

        def _cinput(hint, pw=False):
            return TextInput(
                hint_text=hint, password=pw, multiline=False, font_size=dp(15),
                background_normal="", background_active="",
                background_color=(0, 0, 0, 0), foreground_color=DARK,
                size_hint_y=None, height=dp(36),
                padding=[dp(10), dp(8), dp(10), dp(8)],
            )

        self.card_number = _cinput("카드번호 16자리")
        self.card_pw     = _cinput("비밀번호 앞 2자리", pw=True)
        self.card_birth  = _cinput("생년월일 6자리 YYMMDD")
        self.card_expire = _cinput("유효기간 4자리 MMYY")

        self.add_widget(FieldCard("카드번호", self.card_number))
        crow = BoxLayout(size_hint_y=None, height=dp(62), spacing=dp(10))
        crow.add_widget(FieldCard("비밀번호 앞2자리", self.card_pw))
        crow.add_widget(FieldCard("유효기간(MMYY)", self.card_expire))
        self.add_widget(crow)
        self.add_widget(FieldCard("생년월일(YYMMDD)", self.card_birth))
        save_btn = PillButton("💳 카드 저장 (암호화)", bg=(0.22, 0.52, 0.35, 1),
                              height=dp(44), font_size=dp(15))
        save_btn.bind(on_press=lambda _: self._save_card())
        self.add_widget(save_btn)


        self.add_widget(self._spacer(4))

        # ── 역 선택 ──
        self.add_widget(lbl("열차 검색", size=12, color=GRAY1, bold=True,
                            size_hint_y=None, height=dp(20)))

        dep_arr = BoxLayout(size_hint_y=None, height=dp(62), spacing=dp(10))
        self._dep_btn = FieldBtn(self._dep)
        self._arr_btn = FieldBtn(self._arr)
        self._dep_btn.bind(on_press=self._open_station_picker)
        self._arr_btn.bind(on_press=self._open_station_picker)
        dep_arr.add_widget(FieldCard("출발역", self._dep_btn))
        dep_arr.add_widget(FieldCard("도착역", self._arr_btn))
        self.add_widget(dep_arr)

        # ── 날짜/시간 ──
        self._datetime_btn = FieldBtn(f"{self._date}  {self._hour}:00")
        self._datetime_btn.bind(on_press=self._open_datetime_picker)
        self.add_widget(FieldCard("출발일시", self._datetime_btn))

        # ── 좌석 + 초당호출 ──
        opt = BoxLayout(size_hint_y=None, height=dp(62), spacing=dp(10))
        self._seat_val = "아무거나"
        self._seat_btn = FieldBtn(self._seat_val)
        self._seat_btn.bind(on_press=self._open_seat_picker)
        self.rate = TextInput(text="2.0", multiline=False, input_filter="float",
                              font_size=dp(16), background_normal="",
                              background_active="", background_color=(0,0,0,0),
                              foreground_color=DARK,
                              size_hint_y=None, height=dp(36))
        opt.add_widget(FieldCard("좌석", self._seat_btn))
        opt.add_widget(FieldCard("동시 요청 수", self.rate))
        self.add_widget(opt)

        self.add_widget(self._spacer(4))

        # ── 조회 버튼 ──
        sb = PillButton("열차 조회", bg=DARK)
        sb.bind(on_press=lambda _: threading.Thread(target=self._search_thread, daemon=True).start())
        self.add_widget(sb)

        self.add_widget(self._spacer(4))

        # ── 결과 ──
        self.result_label = lbl("조회 결과", size=12, color=GRAY1, bold=True,
                                size_hint_y=None, height=0)
        self.add_widget(self.result_label)
        self.train_scroll = ScrollView(size_hint_y=None, height=0,
                                       always_overscroll=False, effect_cls=ScrollEffect)
        self.train_list   = GridLayout(cols=1, size_hint_y=None, spacing=dp(6))
        self.train_list.bind(minimum_height=self._update_train_scroll_height)
        self.train_scroll.add_widget(self.train_list)
        self.add_widget(self.train_scroll)

        self.add_widget(self._spacer(4))

        # ── 예매 버튼 ──
        br = BoxLayout(size_hint_y=None, height=dp(56), spacing=dp(10))
        self.start_btn = PillButton("예매 시작", bg=(0.45, 0.20, 0.75, 1))
        self.start_btn.disabled = True
        self.start_btn.bind(on_press=lambda _: self.start())
        self.stop_btn = PillButton("중지", bg=(0.55, 0.50, 0.65, 1))
        self.stop_btn.disabled = True
        self.stop_btn.bind(on_press=lambda _: self.stop())
        br.add_widget(self.start_btn)
        br.add_widget(self.stop_btn)
        self.add_widget(br)

        # ── 상태 / 로그 ──
        self.status_label = lbl("대기 중", size=14, color=PRIMARY, bold=True,
                                halign="center", size_hint_y=None, height=dp(28))
        self.add_widget(self.status_label)

        log_card = RoundBox(orientation="vertical", radius=14, bg=WHITE,
                            size_hint_y=None, height=dp(300), padding=dp(10))
        self.log_box = TextInput(readonly=True, multiline=True,
                                 background_normal="", background_color=(0,0,0,0),
                                 foreground_color=DARK, font_size=dp(13))
        log_card.add_widget(self.log_box)
        self.add_widget(log_card)

    # ── 팝업 열기 ────────────────────────────────────────────
    def _open_station_picker(self, *_):
        popup = StationPickerPopup(self._dep, self._arr, self._on_station_selected)
        popup.open()

    def _on_station_selected(self, dep, arr):
        self._dep = dep; self._arr = arr
        self._dep_btn.text = dep
        self._arr_btn.text = arr

    def _open_datetime_picker(self, *_):
        popup = DateTimePickerPopup(self._date, self._hour, self._on_datetime_selected)
        popup.open()

    def _on_datetime_selected(self, date_str, hour):
        self._date = date_str
        self._hour = hour
        self._datetime_btn.text = f"{date_str}  {hour}:00"

    def _open_seat_picker(self, *_):
        SEATS = ["아무거나", "일반실", "특실"]
        popup = ModalView(background_color=(0,0,0,0.45), size_hint=(1,1))
        outer = BoxLayout(orientation="vertical", size_hint=(0.85, None),
                          pos_hint={"center_x":0.5, "center_y":0.55})
        with outer.canvas.before:
            Color(*WHITE)
            rr = RoundedRectangle(radius=[dp(20)])
        outer.bind(pos=lambda *_: setattr(rr,"pos",outer.pos),
                   size=lambda *_: setattr(rr,"size",outer.size))

        tr = BoxLayout(size_hint_y=None, height=dp(54), padding=[dp(16),0,dp(8),0])
        tr.add_widget(lbl("좌석 선택", size=18, bold=True, halign="center"))
        x = Button(text="✕", size_hint=(None,None), size=(dp(44),dp(44)),
                   background_normal="", background_color=(0,0,0,0),
                   color=GRAY1, font_size=dp(20))
        x.bind(on_press=lambda _: popup.dismiss())
        tr.add_widget(x)
        outer.add_widget(tr)

        for seat in SEATS:
            is_sel = (seat == self._seat_val)
            btn = Button(text=seat, size_hint_y=None, height=dp(62),
                         background_normal="", font_size=dp(18), bold=True,
                         background_color=PRIMARY if is_sel else LIGHT_BG,
                         color=WHITE if is_sel else DARK)
            def _on_seat(b, s=seat, p=popup):
                self._seat_val = s
                self._seat_btn.text = s
                p.dismiss()
            btn.bind(on_press=_on_seat)
            outer.add_widget(btn)

        outer.add_widget(Widget(size_hint_y=None, height=dp(10)))
        outer.height = dp(54) + dp(62)*len(SEATS) + dp(10)
        popup.add_widget(outer)
        popup.open()

    @property
    def seat(self):
        return type("_S", (), {"text": self._seat_val})()

    # ── 유틸 ────────────────────────────────────────────────
    @mainthread
    def log(self, msg: str):
        self.log_box.text += msg + "\n"
        self.log_box.scroll_y = 0  # 항상 최신 줄로 스크롤

    @mainthread
    def set_status(self, msg: str):
        self.status_label.text = msg

    @mainthread
    def _start_alarm(self):
        """진동 알람 시작 - 알림 버튼 또는 중지 버튼으로 중지"""
        try:
            from jnius import autoclass
            PA       = autoclass("org.kivy.android.PythonActivity")
            Vibrator = autoclass("android.os.Vibrator")
            ctx = PA.mActivity
            vib = ctx.getSystemService(ctx.VIBRATOR_SERVICE)

            # 진동 패턴: 0ms 대기 → 800ms 진동 → 400ms 휴식 → 반복
            try:
                VibrationEffect = autoclass("android.os.VibrationEffect")
                effect = VibrationEffect.createWaveform([0, 800, 400], 0)
                vib.vibrate(effect)
            except Exception:
                # API 26 미만 fallback
                vib.vibrate([0, 800, 400], 0)

            self._vibrator = vib
            self.log("📳 진동 알람 시작")
            from kivy.core.window import Window
            Window.bind(on_touch_down=self._on_touch_stop_alarm)
        except Exception as e:
            self.log(f"⚠ 알람 실패: {e}")
            self._vibrator = None

    def _stop_alarm(self, *_):
        try:
            if getattr(self, "_vibrator", None):
                self._vibrator.cancel()
                self._vibrator = None
            from kivy.core.window import Window
            Window.unbind(on_touch_down=self._on_touch_stop_alarm)
        except Exception:
            pass

    def _on_touch_stop_alarm(self, *_):
        self._stop_alarm()
        self._dismiss_notify()

    def _notify(self, title: str, text: str):
        self._start_alarm()
        try:
            from jnius import autoclass
            PA            = autoclass("org.kivy.android.PythonActivity")
            NotifBuilder  = autoclass("android.app.Notification$Builder")
            NotifMgr      = autoclass("android.app.NotificationManager")
            NotifCh       = autoclass("android.app.NotificationChannel")
            PendingIntent = autoclass("android.app.PendingIntent")
            Notification  = autoclass("android.app.Notification")
            PowerManager  = autoclass("android.os.PowerManager")
            Intent        = autoclass("android.content.Intent")
            ctx = PA.mActivity

            # 화면 강제 켜기
            pm = ctx.getSystemService(ctx.POWER_SERVICE)
            wl = pm.newWakeLock(
                PowerManager.SCREEN_BRIGHT_WAKE_LOCK |
                PowerManager.ACQUIRE_CAUSES_WAKEUP |
                PowerManager.ON_AFTER_RELEASE,
                "srt:alarm_screen")
            wl.acquire(60000)
            try:
                ctx.setShowWhenLocked(True)
                ctx.setTurnScreenOn(True)
            except Exception:
                pass

            # 알림 채널
            ch_id = "srt_alarm"
            nm = ctx.getSystemService(ctx.NOTIFICATION_SERVICE)
            if nm.getNotificationChannel(ch_id) is None:
                ch = NotifCh(ch_id, "SRT 예매 완료 알람", NotifMgr.IMPORTANCE_HIGH)
                ch.enableVibration(False)   # 진동은 Vibrator로 직접 처리
                nm.createNotificationChannel(ch)

            # 앱 실행 인텐트 (알림 본체 터치 시)
            launch_intent = ctx.getPackageManager().getLaunchIntentForPackage(ctx.getPackageName())
            launch_intent.addFlags(0x10000000)
            launch_pi = PendingIntent.getActivity(
                ctx, 0, launch_intent,
                PendingIntent.FLAG_IMMUTABLE | PendingIntent.FLAG_UPDATE_CURRENT)

            # 알림 빌드 (알람 끄기 버튼 제외 — jnius 오버로드 오류로 비활성화)
            builder = (NotifBuilder(ctx, ch_id)
                       .setContentTitle(title)
                       .setContentText(text)
                       .setSmallIcon(ctx.getApplicationInfo().icon)
                       .setContentIntent(launch_pi)
                       .setFullScreenIntent(launch_pi, True)
                       .setVisibility(Notification.VISIBILITY_PUBLIC)
                       .setPriority(Notification.PRIORITY_MAX)
                       .setOngoing(True))
            nm.notify(100, builder.build())
            self.log("🔔 알림 전송 완료")
        except Exception as e:
            self.log(f"⚠ 알림 실패: {e}")

    @mainthread
    def _dismiss_notify(self):
        """예매 완료 알림 제거"""
        try:
            from jnius import autoclass
            PA  = autoclass("org.kivy.android.PythonActivity")
            ctx = PA.mActivity
            nm  = ctx.getSystemService(ctx.NOTIFICATION_SERVICE)
            nm.cancel(100)
        except Exception:
            pass

    @mainthread
    def _update_train_scroll_height(self, *_):
        h = self.train_list.minimum_height
        self.train_scroll.height = min(h, dp(280))
        self.result_label.height = dp(20) if h > 0 else 0

    @mainthread
    def _set_start_btn(self, enabled: bool):
        self.start_btn.disabled = not enabled

    def _get_params(self):
        date_str = self._date.replace("-", "")
        hh = self._hour
        api_hour = int(hh) if int(hh) % 2 == 0 else int(hh) - 1
        time_val = f"{api_hour:02d}0000"
        sel_dt   = datetime.strptime(f"{date_str}{hh}00", "%Y%m%d%H%M")
        end_dt   = sel_dt + timedelta(hours=1)
        return date_str, hh, time_val, sel_dt, end_dt

    def _in_range(self, train, date_str, sel_dt, end_dt) -> bool:
        try:
            t_dt = datetime.strptime(f"{date_str}{train.dep_time}", "%Y%m%d%H%M%S")
            return sel_dt <= t_dt < end_dt
        except Exception:
            return True

    def _login(self):
        if self._srt is None:
            self.log("로그인 중...")
            self._srt = SRT(self.member_no.text.strip(), self.password.text.strip())
            self.log("✅ 로그인 성공")

    def _is_session_error(self, err: str) -> bool:
        return any(k in err for k in
                   ["Blocked","blocked","Wrong Server","세션","session","timeout","Timeout"])

    def _is_netfunnel_error(self, err: str) -> bool:
        return any(k in err for k in ["NetFunnel","netfunnel","대기"])

    def _relogin(self, reason="세션 오류"):
        self.log(f"⛔ {reason[:30]} → 재로그인...")
        self._srt = None
        try:
            self._login()
            self.log("✅ 재로그인 성공")
        except Exception as e:
            self.log(f"재로그인 실패: {e}")

    # ── 열차 조회 ────────────────────────────────────────────
    def _search_thread(self):
        self._save_settings()
        self._clear_train_list()
        self._trains = []
        self._set_start_btn(False)
        try:
            self._login()
        except Exception as e:
            self.log(f"로그인 실패: {e}"); return

        date_str, hh, time_val, sel_dt, end_dt = self._get_params()
        dep, arr = self._dep, self._arr
        self.log(f"조회: {dep}→{arr} {hh}:00~{end_dt.strftime('%H:%M')}")

        try:
            trains = self._srt.search_train(dep, arr, date_str, time_val, available_only=False)
        except Exception as e:
            err = str(e)
            if self._is_session_error(err):
                self._srt = None
                try:
                    self._login()
                    trains = self._srt.search_train(dep, arr, date_str, time_val, available_only=False)
                except Exception as e2:
                    self.log(f"조회 실패: {e2}"); return
            else:
                self.log(f"조회 실패: {err}"); return

        accents = [ACCENT_B, ACCENT_G, ACCENT_Y, ACCENT_P]
        filtered = [t for t in trains if self._in_range(t, date_str, sel_dt, end_dt)]
        self._trains = filtered
        self.log(f"총 {len(filtered)}건 조회됨")
        self._populate_train_list(filtered, accents)
        if filtered:
            self._set_start_btn(True)

    @mainthread
    def _clear_train_list(self):
        self.train_list.clear_widgets()
        self._selected_row = None
        Clock.schedule_once(self._update_train_scroll_height, 0)

    @mainthread
    def _populate_train_list(self, trains, accents):
        for i, t in enumerate(trains):
            g   = "O" if t.general_seat_available() else "X"
            sp  = "O" if t.special_seat_available() else "X"
            dep = f"{t.dep_time[:2]}:{t.dep_time[2:4]}"
            arr = f"{t.arr_time[:2]}:{t.arr_time[2:4]}"
            txt = f"{t.train_number}  {dep}→{arr}   일반:{g}  특실:{sp}"
            row = TrainRow(txt, i, accent=accents[i % len(accents)])
            row.bind(on_press=self._on_train_select)
            self.train_list.add_widget(row)
        if self.train_list.children:
            first = self.train_list.children[-1]
            first.state = "down"
            self._selected_row = first
        Clock.schedule_once(self._update_train_scroll_height, 0)

    def _on_train_select(self, btn):
        self._selected_row = btn

    # ── WakeLock ────────────────────────────────────────────
    def _acquire_wake_lock(self):
        try:
            from jnius import autoclass
            PA = autoclass("org.kivy.android.PythonActivity")
            PM = autoclass("android.os.PowerManager")
            pm = PA.mActivity.getSystemService(PA.mActivity.POWER_SERVICE)
            self._wake_lock = pm.newWakeLock(PM.PARTIAL_WAKE_LOCK, "SRTApp:WakeLock")
            self._wake_lock.acquire()
            self.log("🔒 WakeLock 획득 성공")
        except Exception as e:
            self.log(f"⚠ WakeLock 실패: {e}")
            self._wake_lock = None
        # WifiLock: 화면 꺼져도 Wi-Fi 유지
        try:
            from jnius import autoclass
            PA = autoclass("org.kivy.android.PythonActivity")
            WM = autoclass("android.net.wifi.WifiManager")
            wm = PA.mActivity.getSystemService(PA.mActivity.WIFI_SERVICE)
            self._wifi_lock = wm.createWifiLock(WM.WIFI_MODE_FULL_HIGH_PERF, "SRTApp:WifiLock")
            self._wifi_lock.acquire()
            self.log("📶 WifiLock 획득 성공")
        except Exception as e:
            self.log(f"⚠ WifiLock 실패: {e}")
            self._wifi_lock = None
        # 배터리 최적화 무시 요청
        try:
            from jnius import autoclass
            PA       = autoclass("org.kivy.android.PythonActivity")
            Settings = autoclass("android.provider.Settings")
            Uri      = autoclass("android.net.Uri")
            Intent   = autoclass("android.content.Intent")
            ctx = PA.mActivity
            pkg = ctx.getPackageName()
            pm2 = ctx.getSystemService(ctx.POWER_SERVICE)
            if not pm2.isIgnoringBatteryOptimizations(pkg):
                intent = Intent(Settings.ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS)
                intent.setData(Uri.parse(f"package:{pkg}"))
                ctx.startActivity(intent)
                self.log("⚡ 배터리 최적화 무시 요청")
        except Exception as e:
            self.log(f"⚠ 배터리 최적화 설정 실패: {e}")

    def _release_wake_lock(self):
        try:
            if self._wake_lock and self._wake_lock.isHeld():
                self._wake_lock.release()
        except Exception:
            pass
        try:
            if self._wifi_lock and self._wifi_lock.isHeld():
                self._wifi_lock.release()
        except Exception:
            pass

    # ── 예매 시작/중지 ───────────────────────────────────────
    def start(self):
        if self._selected_row is None:
            self.log("열차를 선택하세요."); return
        self._target_train = self._trains[self._selected_row.train_index]
        self.log(f"\n▶ {self._target_train.train_number}호 "
                 f"{self._target_train.dep_time[:2]}:{self._target_train.dep_time[2:4]} 예매 시작")
        self._running = True
        self.start_btn.disabled = True
        self.stop_btn.disabled  = False
        self._acquire_wake_lock()
        threading.Thread(target=self._reserve_loop, daemon=True).start()

    def stop(self):
        self._running = False
        self._release_wake_lock()
        self._stop_alarm()
        self._dismiss_notify()
        self.set_status("중지됨")
        self.start_btn.disabled = False
        self.stop_btn.disabled  = True

    # ── 예매 루프 ────────────────────────────────────────────
    def _reserve_loop(self):
        date_str, hh, time_val, sel_dt, end_dt = self._get_params()
        dep, arr, seat = self._dep, self._arr, self.seat.text

        try:
            n_workers = max(1, min(5, int(float(self.rate.text))))
        except ValueError:
            n_workers = 2

        # 공유 카운터 / 예매 완료 플래그 / 뮤텍스
        lock             = threading.Lock()
        attempt_count    = [0]
        reserved         = [False]
        stat_count       = [0]
        loop_start       = time.time()
        stat_start       = [loop_start]
        all_sessions     = []                         # 모든 워커 세션 목록
        relogin_lock     = threading.Lock()           # 재로그인은 한 스레드만 수행
        relogin_event    = threading.Event()          # 재로그인 완료 신호
        relogin_event.set()
        last_relogin_t   = [0.0]                      # 마지막 재로그인 시각
        relogin_fail_cnt = [0]                        # 연속 재로그인 실패 횟수
        MAX_RELOGIN_FAIL = 5                          # N회 연속 실패 시 전체 중지
        TARGET_RPS       = n_workers                  # 목표 초당 요청 수 = 동시 요청 수
        slot_lock        = threading.Lock()           # 요청 슬롯 제어
        next_slot_t      = [time.time()]              # 다음 요청 허용 시각

        def _acquire_slot():
            with slot_lock:
                now  = time.time()
                wait = next_slot_t[0] - now
                if wait > 0:
                    time.sleep(wait)
                next_slot_t[0] = max(next_slot_t[0], time.time()) + 1.0 / TARGET_RPS

        # 로그인 정보로 각 스레드별 독립 SRT 세션 생성
        member_no = self.member_no.text.strip()
        password  = self.password.text.strip()
        def _make_srt():
            s = SRT(member_no, password)
            # 응답 없음으로 인한 스레드 무한 대기 방지 (10초 타임아웃)
            _orig = s._session.request
            def _req(method, url, **kwargs):
                kwargs.setdefault("timeout", 10)
                return _orig(method, url, **kwargs)
            s._session.request = _req
            return s

        def _worker(worker_srt):
            while self._running and not reserved[0]:
                relogin_event.wait()  # 재로그인 중이면 완료될 때까지 요청 차단
                _acquire_slot()
                t0 = time.time()
                try:
                    trains = worker_srt.search_train(
                        dep, arr, date_str, time_val, available_only=False)
                    target = next((t for t in trains
                                   if t.train_number == self._target_train.train_number), None)
                    ms = int((time.time() - t0) * 1000)

                    with lock:
                        attempt_count[0] += 1
                        stat_count[0]    += 1
                        cnt = attempt_count[0]
                        elapsed = time.time() - stat_start[0]
                        if elapsed >= 1.0:
                            secs = int(time.time() - loop_start)
                            self.log(
                                f"[시도 {cnt}회 | {stat_count[0]/elapsed:.1f}회/초 | {secs}초 경과]")
                            stat_start[0] = time.time(); stat_count[0] = 0
                        do_log_100 = (cnt % 100 == 0)

                    if target is None:
                        if do_log_100:
                            self.log(f"[{cnt}회] 조회 중...")
                    elif not (target.general_seat_available() or target.special_seat_available()):
                        if do_log_100:
                            self.log(f"[{cnt}회] 매진 중...")
                    else:
                        with lock:
                            if reserved[0]:
                                return   # 다른 스레드가 이미 예매 완료
                            reserved[0] = True
                        special = (target.special_seat_available()
                                   if seat == "아무거나" else (seat == "특실"))
                        rsv = worker_srt.reserve(target, special_seat=special)
                        self.log(f"✅ 예매 성공! ({cnt}회)\n{rsv}")
                        # 자동 결제
                        card = self._load_card()
                        if all(card.get(k) for k in ("number", "password", "birth", "expire")):
                            try:
                                ok = worker_srt.pay_with_card(
                                    rsv,
                                    number=card["number"],
                                    password=card["password"],
                                    validation_number=card["birth"],
                                    expire_date=card["expire"][2:]+card["expire"][:2],
                                )
                                self.log(f"💳 결제 {'성공!' if ok else '실패'}")
                            except Exception as pe:
                                self.log(f"💳 결제 오류: {pe}")
                        else:
                            self.log("💳 카드 미등록 - 앱에서 20분 내 수동 결제 필요")
                        self.set_status("✅ 예매 완료!")
                        self._notify("🎉 SRT 예매 완료!", f"열차 {target.train_number}호 예매 성공!")
                        self._release_wake_lock()
                        self.stop(); return

                except Exception as e:
                    err = str(e)
                    with lock:
                        attempt_count[0] += 1
                        stat_count[0]    += 1
                        cnt = attempt_count[0]
                        elapsed = time.time() - stat_start[0]
                        if elapsed >= 1.0:
                            secs = int(time.time() - loop_start)
                            self.log(
                                f"[시도 {cnt}회 | {stat_count[0]/elapsed:.1f}회/초 | {secs}초 경과]")
                            stat_start[0] = time.time(); stat_count[0] = 0
                    if self._is_netfunnel_error(err):
                        self.log(f"[{cnt}] 대기열 진입 → 5초 후 재시도")
                        time.sleep(5)
                    elif self._is_session_error(err):
                        relogin_event.wait()          # 다른 스레드가 재로그인 중이면 대기
                        with relogin_lock:
                            # 다른 스레드가 방금 재로그인 완료 → 그냥 재시도
                            if time.time() - last_relogin_t[0] < 5.0:
                                pass
                            else:
                                relogin_event.clear()
                                self.log(f"[{cnt}] 세션 오류 → 전체 세션 재로그인")
                                try:
                                    for s in all_sessions:
                                        s.login(member_no, password)
                                    relogin_fail_cnt[0] = 0
                                    last_relogin_t[0] = time.time()
                                    next_slot_t[0] = time.time()  # 재로그인 후 슬롯 리셋 → 버스트 방지
                                    self.log("✅ 전체 세션 재로그인 성공")
                                except Exception as le:
                                    relogin_fail_cnt[0] += 1
                                    fail = relogin_fail_cnt[0]
                                    wait = min(3 * (2 ** (fail - 1)), 60)
                                    self.log(f"재로그인 실패({fail}회): {le} → {wait}초 대기")
                                    if fail >= MAX_RELOGIN_FAIL:
                                        self.log("⛔ 재로그인 반복 실패 → 예매 중지")
                                        self._running = False
                                        Clock.schedule_once(lambda dt: self.stop(), 0)
                                        relogin_event.set()
                                        return
                                    time.sleep(wait)
                                finally:
                                    relogin_event.set()
                    else:
                        self.log(f"[{cnt}] 오류: {e}")

                if not self._running or reserved[0]:
                    return

        # 선제적 재로그인 스케줄러 — 5초마다 세션 만료 전에 재로그인
        RELOGIN_INTERVAL = 5

        def _scheduled_relogin():
            time.sleep(3)  # 초기 대기 (워커 안정화)
            while self._running and not reserved[0]:
                # 재로그인 수행
                relogin_event.wait()
                with relogin_lock:
                    if time.time() - last_relogin_t[0] < 4.0:
                        pass  # 최근 재로그인 완료 → 스킵
                    else:
                        relogin_event.clear()
                        try:
                            self.log("🔁 선제 재로그인 시작")
                            for s in all_sessions:
                                s.login(member_no, password)
                            last_relogin_t[0] = time.time()
                            next_slot_t[0] = time.time()
                            self.log("✅ 선제 재로그인 성공")
                        except Exception as e:
                            self.log(f"❌ 선제 재로그인 실패: {e}")
                        finally:
                            relogin_event.set()
                # 재로그인 후 5초 대기
                if not self._running or reserved[0]:
                    return
                time.sleep(RELOGIN_INTERVAL)

        # n_workers 개 스레드 동시 실행
        self.log(f"🔄 {n_workers}개 스레드 병렬 요청 시작")
        workers = []
        for i in range(n_workers):
            try:
                s = _make_srt()
                all_sessions.append(s)
                t = threading.Thread(target=_worker, args=(s,), daemon=True)
                workers.append(t)
                t.start()
                time.sleep(0.1)   # 로그인 요청 분산
            except Exception as e:
                self.log(f"스레드 {i+1} 생성 실패: {e}")

        ka = threading.Thread(target=_scheduled_relogin, daemon=True)
        ka.start()

        for t in workers:
            t.join()


class SRTApp(App):
    def build(self):
        from kivy.core.window import Window
        Window.clearcolor = BG
        scroll = ScrollView(always_overscroll=False, effect_cls=ScrollEffect)
        self._widget = SRTWidget(size_hint_y=None)
        self._widget.bind(minimum_height=self._widget.setter("height"))
        scroll.add_widget(self._widget)
        return scroll

    def on_pause(self):
        if self._widget:
            self._widget._save_settings()
        return True

    def on_resume(self):
        from kivy.core.window import Window
        from kivy.clock import Clock
        Window.clearcolor = BG

        def _full_redraw(dt):
            if not self._widget:
                return
            # 최상위 + 모든 자식 위젯 캔버스 강제 갱신
            try:
                for w in self._widget.walk():
                    try:
                        w.canvas.ask_update()
                    except Exception:
                        pass
            except Exception:
                pass
            self._widget.canvas.ask_update()

        # OpenGL 컨텍스트 복구 타이밍이 불규칙해서 여러 번 시도
        Clock.schedule_once(_full_redraw, 0)
        Clock.schedule_once(_full_redraw, 0.3)
        Clock.schedule_once(_full_redraw, 1.0)
        Clock.schedule_once(_full_redraw, 2.5)

        # 알람 끄기 버튼으로 복귀한 경우 자동 중지
        try:
            from jnius import autoclass
            PA     = autoclass("org.kivy.android.PythonActivity")
            intent = PA.mActivity.getIntent()
            if intent.getBooleanExtra("stop_alarm", False):
                intent.removeExtra("stop_alarm")
                if self._widget:
                    self._widget._stop_alarm()
                    self._widget._dismiss_notify()
        except Exception:
            pass


if __name__ == "__main__":
    SRTApp().run()

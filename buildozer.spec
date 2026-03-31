[app]
title = 파덕이의 SRT
package.name = srtbooking
package.domain = org.srt

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf

version = 1.0

icon.filename = %(source.dir)s/icon.png
presplash.filename = %(source.dir)s/presplash.png

# SRT 라이브러리 소스 폴더(SRT/)를 프로젝트에 복사해야 합니다
requirements = python3,kivy==2.3.0,requests,chardet,urllib3,certifi,idna,pycryptodome

orientation = portrait
fullscreen = 0

android.permissions = INTERNET, WAKE_LOCK, FOREGROUND_SERVICE, ACCESS_WIFI_STATE, CHANGE_WIFI_STATE, REQUEST_IGNORE_BATTERY_OPTIMIZATIONS, POST_NOTIFICATIONS, VIBRATE, ACCESS_NOTIFICATION_POLICY, USE_FULL_SCREEN_INTENT
android.api = 33
android.minapi = 21
android.ndk = 25b
android.archs = arm64-v8a

# 한글 폰트 (NanumGothic.ttf 를 프로젝트 폴더에 복사 후 아래 경로 사용)
# android.add_assets = NanumGothic.ttf:fonts/NanumGothic.ttf

[buildozer]
log_level = 2
warn_on_root = 1

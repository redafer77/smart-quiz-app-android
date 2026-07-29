[app]
title = تطبيق الاختبارات الذكي
package.name = smartquizapp
package.domain = org.quizapp

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,txt,ttf,json
source.include_patterns = fonts/*.ttf,data/*.json,assets/*.png
source.exclude_dirs = tests,bin,.buildozer,.github,.git,tools,data/source

version = 1.4

# لا حاجة لأي حزمة خارجية لدعم العربية: التشكيل والـ RTL مكتوبان في arabic_support.py
requirements = python3,kivy,cython==3.0.11

icon.filename = %(source.dir)s/assets/icon.png
presplash.filename = %(source.dir)s/assets/presplash.png
android.presplash_color = #0C1E37

orientation = portrait
fullscreen = 0

# التطبيق يخزّن بياناته في مجلده الخاص، فلا يحتاج أي أذونات
android.api = 33
android.minapi = 21
android.ndk = 25b
android.archs = arm64-v8a
android.accept_sdk_license = True
android.allow_backup = True

[buildozer]
log_level = 2
warn_on_root = 1

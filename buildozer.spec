[app]
title = تطبيق الاختبارات الذكي
package.name = smartquizapp
package.domain = org.quizapp
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,txt
version = 1.0
requirements = python3,kivy==2.2.1,cython==0.29.33
orientation = portrait
fullscreen = 0
android.permissions = WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE
android.api = 31
android.minapi = 21
android.ndk = 23b
android.arch = arm64-v8a
[buildozer]
log_level = 2
warn_on_root = 1

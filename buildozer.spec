[app]
title = CyberGram
package.name = cybergram
package.domain = org.cyber.gram
source.dir = .
source.include_exts = py,kv,png,jpg,jpeg,json,atlas,ttf,otf,mp3,wav,mp4
source.exclude_dirs = bin,.github,.venv
version = 3.0
requirements = python3,kivy==2.3.0,certifi
orientation = sensor
fullscreen = 0
android.permissions = INTERNET,CAMERA,RECORD_AUDIO,VIBRATE,READ_MEDIA_IMAGES,READ_MEDIA_VIDEO
android.api = 33
android.minapi = 23
android.ndk = 25b
android.archs = arm64-v8a,armeabi-v7a
android.accept_sdk_license = True
p4a.branch = v2024.01.21
android.allow_backup = True
android.presplash_color = #101010

[buildozer]
log_level = 2
warn_on_root = 1

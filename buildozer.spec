[app]

title = BLE RC Car
package.name = rc_car
package.domain = org.example

source.dir = .
source.include_exts = py,png,jpg,jpeg,ttf,wav,mp3,json,txt,kv
source.include_patterns = assets/**

version = 1.0.0
version.code = 5

requirements = python3,kivy==2.1.0,pyjnius,setuptools,plyer

icon.filename = assets/icon.png
presplash.filename = assets/presplash.jpg

orientation = landscape
fullscreen = 1

android.wakelock = True
android.pause_min_size = 1

android.permissions = BLUETOOTH,BLUETOOTH_ADMIN,ACCESS_FINE_LOCATION,BLUETOOTH_SCAN,BLUETOOTH_CONNECT,VIBRATE

android.features = android.hardware.bluetooth_le

# تغییر: API 33 به 31 (پایدارتر برای pyjnius)
android.api = 31
android.target_sdk_version = 31
android.minapi = 21

android.ndk = 25c
android.ndk_api = 21

android.archs = arm64-v8a

android.enable_androidx = True
android.accept_sdk_license = True

android.gradle_dependencies = androidx.appcompat:appcompat:1.6.1

android.allow_backup = False
android.logcat_filters = *:S python:D

android.release_artifact = apk

android.numeric_version = 10005

[buildozer]

log_level = 2
warn_on_root = 1
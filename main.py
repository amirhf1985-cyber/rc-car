import traceback, os
def _write_startup_error(exc):
    try:
        paths=[
            "/sdcard/error.txt",
            "/storage/emulated/0/error.txt",
            "error.txt"
        ]
        msg=traceback.format_exc()
        for p in paths:
            try:
                with open(p,"w",encoding="utf-8") as f:
                    f.write(msg)
            except Exception:
                pass
    except Exception:
        pass

# ==================== IMPORTS ====================
from kivy.resources import resource_add_path, resource_find
from kivy.logger import Logger
from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.popup import Popup
from kivy.uix.button import Button
from kivy.uix.slider import Slider
from kivy.uix.spinner import Spinner
from kivy.uix.progressbar import ProgressBar
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.widget import Widget
from kivy.properties import (
    StringProperty, NumericProperty, ObjectProperty, 
    ListProperty, BooleanProperty, DictProperty
)
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle, Rotate, PushMatrix, PopMatrix
from kivy.core.window import Window
from kivy.config import Config
from kivy.storage.jsonstore import JsonStore
from kivy.core.audio import SoundLoader
from abc import ABC, abstractmethod
from typing import Callable, Optional, Dict, Any, List
import os
import threading
import time
import math
import random
import socket
import json
import sys
import traceback
import subprocess
import ipaddress
from datetime import datetime
import re
import functools
import gc
from queue import Queue, Empty
import weakref
from kivy.utils import platform

# ==================== ANDROID PERMISSION IMPORTS ====================
try:
    from android.permissions import request_permissions, Permission, check_permission
    from android.storage import primary_external_storage_path, app_storage_path
    from jnius import autoclass, cast, PythonJavaClass, java_method
    HAS_ANDROID = True
    print("Android components loaded successfully")
    
    try:
        Build_VERSION = autoclass('android.os.Build$VERSION')
        SDK_INT = Build_VERSION.SDK_INT
        print(f"Android SDK version: {SDK_INT}")
    except:
        SDK_INT = 0
        print("Could not get Android SDK version")
        
except Exception as e:
    HAS_ANDROID = False
    SDK_INT = 0
    print(f"Android components not available: {e}")

# ==================== FIXED ASSET FUNCTION ====================
def asset(filename):
    """
    Reliable asset loader - مخصوص Buildozer + Android
    """
    try:
        from kivy.resources import resource_find
        import os

        # روش اصلی Kivy برای APK
        for prefix in ['', 'assets/']:
            path = resource_find(f'{prefix}{filename}')
            if path and os.path.exists(path):
                return path

        # Fallback
        base = os.path.dirname(os.path.abspath(__file__))
        paths = [
            f'assets/{filename}',
            filename,
            os.path.join(base, 'assets', filename),
            os.path.join(base, filename),
            os.path.join(os.getcwd(), 'assets', filename),
        ]
        for p in paths:
            if os.path.exists(p):
                return p

        print(f"⚠️ Asset not found: {filename}")
        return filename
    except Exception as e:
        print(f"Asset error {filename}: {e}")
        return filename

# ==================== GLOBAL EXCEPTION HANDLER ====================
def global_exception_hook(exc_type, exc_value, exc_traceback):
    try:
        error_str = str(exc_value)
        
        if any(keyword in error_str for keyword in 
               ["'����' object", "jnius_proxy", "PyLocal_Get", "JavaObject", "JNI"]):
            print("\n" + "="*60)
            print("JNIUS/JAVA RUNTIME ERROR DETECTED!")
            print(f"Error: {exc_type.__name__}")
            print("="*60 + "\n")
            return
        
        print("\n" + "="*60)
        print("CRITICAL ERROR!")
        print(f"Type: {exc_type.__name__}")
        print(f"Message: {exc_value}")
        print("\nFull Traceback:")
        traceback.print_exception(exc_type, exc_value, exc_traceback)
        print("="*60 + "\n")
        
        try:
            log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
            os.makedirs(log_dir, exist_ok=True)
            log_file = os.path.join(log_dir, "rc_car_crash.log")
            with open(log_file, "a", encoding='utf-8') as f:
                f.write(f"\n{'='*80}\n[{datetime.now()}] CRASH!\n")
                f.write(f"Type: {exc_type.__name__}\n")
                f.write(f"Message: {exc_value}\n")
                f.write("Traceback:\n")
                traceback.print_exception(exc_type, exc_value, exc_traceback, file=f)
                f.write(f"{'='*80}\n")
        except Exception as e:
            print(f"Failed to write crash log: {e}")
            
    except Exception as e:
        print(f"Error in exception handler: {e}")
    
    if not any(keyword in str(exc_value) for keyword in 
               ["'����' object", "jnius_proxy", "PyLocal_Get", "JavaObject", "JNI"]):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)

sys.excepthook = global_exception_hook

# ==================== PERMISSION MANAGER ====================
class PermissionManager:
    """Professional permission manager for Android"""
    
    @staticmethod
    def has(perms):
        if not HAS_ANDROID:
            return True
        
        if isinstance(perms, str):
            perms = [perms]
        
        try:
            return all([check_permission(p) for p in perms])
        except Exception as e:
            print(f"Permission check error: {e}")
            return False

    @staticmethod
    def request(perms, callback=None):
        if not HAS_ANDROID:
            if callback:
                callback([], [])
            return
        
        if isinstance(perms, str):
            perms = [perms]
        
        try:
            print(f"Requesting permissions: {perms}")
            
            def permission_callback(permissions, grant_results):
                print(f"Permission request result: {grant_results}")
                
                for p, g in zip(permissions, grant_results):
                    status = "GRANTED" if g else "DENIED"
                    print(f"  {p}: {status}")
                
                if callback:
                    callback(permissions, grant_results)
            
            request_permissions(perms, permission_callback)
                        
        except Exception as e:
            print(f"Permission request error: {e}")
            if callback:
                callback([], [])

    @staticmethod
    def open_settings():
        if not HAS_ANDROID:
            return
        
        try:
            from jnius import autoclass
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            Intent = autoclass('android.content.Intent')
            Settings = autoclass('android.provider.Settings')
            Uri = autoclass('android.net.Uri')
            
            intent = Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS)
            uri = Uri.fromParts("package",
                PythonActivity.mActivity.getPackageName(), None)
            intent.setData(uri)
            PythonActivity.mActivity.startActivity(intent)
            print("Opened app settings page")
        except Exception as e:
            print(f"Error opening settings: {e}")

# ==================== BLE PERMISSION REQUEST FUNCTION ====================
def request_ble_permissions(callback=None):
    if not HAS_ANDROID:
        if callback:
            callback(True)
        return

    if SDK_INT >= 31:
        if (check_permission(Permission.BLUETOOTH_SCAN) and 
            check_permission(Permission.BLUETOOTH_CONNECT) and
            check_permission(Permission.ACCESS_FINE_LOCATION)):
            print("All BLE permissions already granted")
            if callback:
                callback(True)
            return
    else:
        if (check_permission(Permission.ACCESS_FINE_LOCATION) and
            check_permission(Permission.BLUETOOTH)):
            print("All legacy permissions already granted")
            if callback:
                callback(True)
            return

    perms = []
    
    if SDK_INT >= 31:
        perms += [
            Permission.BLUETOOTH_SCAN,
            Permission.BLUETOOTH_CONNECT,
            Permission.ACCESS_FINE_LOCATION
        ]
        print("Android 12+ detected - requesting BLE_SCAN and BLE_CONNECT")
    else:
        perms += [
            Permission.ACCESS_FINE_LOCATION,
            Permission.ACCESS_COARSE_LOCATION,
            Permission.BLUETOOTH,
            Permission.BLUETOOTH_ADMIN
        ]
        print("Android <12 detected - requesting legacy permissions")
    
    perms.append(Permission.VIBRATE)

    def permission_result(permissions, grant_results):
        all_granted = all(grant_results)
        if all_granted:
            print("ALL BLE PERMISSIONS GRANTED")
        else:
            print("Some BLE permissions denied")
            for p, g in zip(permissions, grant_results):
                if not g:
                    print(f"  {p} denied")
        
        if callback:
            callback(all_granted)

    PermissionManager.request(perms, permission_result)

# ==================== SAFE JNIUS DECORATOR ====================
def safe_jnius_call(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            if not HAS_ANDROID:
                return None
            
            result = func(*args, **kwargs)
            return result
            
        except Exception as e:
            error_str = str(e)
            
            if "'����' object has no attribute 'invoke'" in error_str:
                Logger.warning(f"Jnius proxy corrupted in {func.__name__}: Skipping")
                return None
            elif "'JavaObject' object has no attribute" in error_str:
                Logger.warning(f"JavaObject attribute error in {func.__name__}: {e}")
                return None
            elif "PyLocal_Get" in error_str or "jnius_proxy" in error_str:
                Logger.warning(f"Jnius internal error in {func.__name__}: {e}")
                return None
            elif "JNI" in error_str or "Java" in error_str:
                Logger.error(f"Java/JNI error in {func.__name__}: {e}")
                return None
            else:
                raise
    
    return wrapper

# ==================== ANDROID STATE HELPER ====================
class AndroidStateHelper:
    """Helper class to check and manage Android system state"""
    
    @staticmethod
    @safe_jnius_call
    def is_bluetooth_enabled():
        if not HAS_ANDROID: 
            return True
        try:
            BluetoothAdapter = autoclass('android.bluetooth.BluetoothAdapter')
            adapter = BluetoothAdapter.getDefaultAdapter()
            return adapter is not None and adapter.isEnabled()
        except Exception as e:
            print(f"Bluetooth check error: {e}")
            return False

    @staticmethod
    @safe_jnius_call
    def is_location_enabled():
        if not HAS_ANDROID: 
            return True
        try:
            Context = autoclass('android.content.Context')
            LocationManager = autoclass('android.location.LocationManager')
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            
            activity = PythonActivity.mActivity
            location_service = activity.getSystemService(Context.LOCATION_SERVICE)
            location_manager = cast(LocationManager, location_service)
            
            if location_manager:
                gps = location_manager.isProviderEnabled(LocationManager.GPS_PROVIDER)
                network = location_manager.isProviderEnabled(LocationManager.NETWORK_PROVIDER)
                return gps or network
            return False
        except Exception as e:
            print(f"Location check error: {e}")
            return False

    @staticmethod
    @safe_jnius_call
    def open_settings(action):
        if not HAS_ANDROID: 
            return False
        try:
            Intent = autoclass('android.content.Intent')
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            
            activity = PythonActivity.mActivity
            intent = Intent(action)
            activity.startActivity(intent)
            return True
        except Exception as e:
            print(f"Error opening settings: {e}")
            return False

    @staticmethod
    def open_bluetooth_settings():
        return AndroidStateHelper.open_settings('android.settings.BLUETOOTH_SETTINGS')

    @staticmethod
    def open_location_settings():
        return AndroidStateHelper.open_settings('android.settings.LOCATION_SOURCE_SETTINGS')

# ==================== DISPLAY SETUP ====================
Config.set('graphics', 'resizable', '0')
Config.set('graphics', 'width', '1024')
Config.set('graphics', 'height', '600')
Config.set('graphics', 'fullscreen', 'auto')
Config.set('graphics', 'borderless', '1')
Window.clearcolor = (1, 1, 1, 1)

def setup_display():
    try:
        Window.fullscreen = 'auto'
        Window.borderless = True
        
        if HAS_ANDROID:
            try:
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                ActivityInfo = autoclass('android.content.pm.ActivityInfo')
                PythonActivity.mActivity.setRequestedOrientation(ActivityInfo.SCREEN_ORIENTATION_LANDSCAPE)
            except Exception as e:
                print(f"Orientation error: {e}")
        
    except Exception as e:
        print(f"Display setup error: {e}")

setup_display()

# ==================== SETTINGS MANAGER ====================
class SettingsManager:
    """Manages application settings using JSON storage"""
    
    def __init__(self):
        self.store = JsonStore('rc_car_settings.json')
        self._lock = threading.RLock()
        self._defaults = {
            'sensitivity': 1.0,
            'accelerometer_mode': False,
            'steering_sensitivity': 1.0,
            'battery_warning_level': 20,
            'last_connected_device': '',
            'vibration_enabled': True,
            'ui_scale': 1.0,
            'theme': 'light',
            'auto_reconnect': True,
            'keep_screen_on': True,
            'foreground_service_enabled': True,
            'wake_lock_enabled': True,
            'ui_build_delay': 0.8,
        }
    
    def get(self, key, default=None):
        with self._lock:
            try:
                if self.store.exists(key):
                    data = self.store.get(key)
                    
                    if isinstance(data, dict):
                        if 'value' in data:
                            return data['value']
                        if key in data:
                            return data[key]
                        if len(data) == 1:
                            return list(data.values())[0]
                        return data
                    
                    elif isinstance(data, list):
                        if data and len(data) > 0:
                            first_item = data[0]
                            if isinstance(first_item, dict) and 'value' in first_item:
                                return first_item['value']
                            if isinstance(default, dict):
                                return default
                            return first_item
                        return default
                    
                    else:
                        return data
                        
                return self._defaults.get(key, default)
                
            except Exception as e:
                print(f"Settings read error for {key}: {e}")
                return self._defaults.get(key, default)
    
    def get_dict(self, key, default=None):
        value = self.get(key, default)
        if isinstance(value, dict):
            return value
        elif isinstance(value, list) and value and isinstance(value[0], dict):
            return value[0]
        elif default is not None:
            return default
        return {}
    
    def set(self, key, value):
        with self._lock:
            try:
                data = {
                    "value": value,
                    "timestamp": time.time()
                }
                self.store.put(key, **data)
                print(f"Setting saved: {key} = {value}")
                return True
            except Exception as e:
                print(f"Settings write error for {key}: {e}")
                return False
    
    def get_all_settings(self):
        settings = {}
        try:
            if hasattr(self, 'store'):
                keys = self.store.keys()
                for key in keys:
                    try:
                        settings[key] = self.get(key)
                    except Exception:
                        settings[key] = self._defaults.get(key, None)
        except Exception:
            settings = self._defaults.copy()
        return settings
    
    def reset_to_defaults(self):
        try:
            for key, value in self._defaults.items():
                self.set(key, value)
            return True
        except Exception:
            return False

def get_setting(key, default=None):
    try:
        app = App.get_running_app()
        if app and hasattr(app, 'settings_manager'):
            return app.settings_manager.get(key, default)
        return default
    except Exception:
        return default

def set_setting(key, value):
    try:
        app = App.get_running_app()
        if app and hasattr(app, 'settings_manager'):
            return app.settings_manager.set(key, value)
        return False
    except Exception:
        return False

# ==================== VIBRATION MANAGER ====================
class VibrationManager:
    """Manages vibration feedback for the application"""
    
    def __init__(self):
        self.enabled = bool(get_setting("vibration_enabled", True))
        self.button_intensity = 0.3
        self.steering_intensity = 0.3
        self.pedal_min = 0.1
        self.pedal_max = 0.7

        self._vibrator = None
        self.has_vibrator = False
        self._vibration_queue = Queue()
        self._vibration_thread = None
        self._paused = False
        self._is_stopping = False
        self._cleanup_done = False
        
        if HAS_ANDROID:
            self.initialize_vibrator()
        
        self.start_vibration_worker()

    def start_vibration_worker(self):
        if self._vibration_thread and self._vibration_thread.is_alive():
            return
        
        def vibration_worker():
            while not self._is_stopping:
                try:
                    task = self._vibration_queue.get(timeout=1.0)
                    if task is None:
                        break
                    
                    if self._paused:
                        self._vibration_queue.task_done()
                        continue
                    
                    duration, intensity = task
                    
                    Clock.schedule_once(
                        lambda dt, d=duration, i=intensity: self._vibrate_ui_thread(d, i)
                    )
                    
                    self._vibration_queue.task_done()
                except Empty:
                    continue
                except Exception:
                    continue
        
        self._vibration_thread = threading.Thread(
            target=vibration_worker, 
            daemon=True,
            name="VibrationWorker"
        )
        self._vibration_thread.start()

    def _vibrate_ui_thread(self, ms, intensity):
        if not self.enabled or not self.has_vibrator or self._paused or self._cleanup_done:
            return
        
        try:
            if not self.has_vibrator or not self._vibrator:
                return
            
            ms = max(1, int(ms))
            
            if HAS_ANDROID and self._vibrator:
                try:
                    if SDK_INT >= 26:
                        try:
                            VibrationEffect = autoclass("android.os.VibrationEffect")
                            amplitude = int(max(1, min(255, int(intensity * 255))))
                            
                            effect = VibrationEffect.createOneShot(ms, amplitude)
                            self._vibrator.vibrate(effect)
                            return
                        except:
                            self._vibrator.vibrate(ms)
                    else:
                        self._vibrator.vibrate(ms)
                except Exception:
                    self.has_vibrator = False
            
        except Exception:
            pass

    @safe_jnius_call
    def initialize_vibrator(self):
        try:
            if not HAS_ANDROID:
                return
            
            Context = autoclass("android.content.Context")
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            activity = PythonActivity.mActivity
            if not activity:
                return
                
            vibrator_service = activity.getSystemService(Context.VIBRATOR_SERVICE)
            self._vibrator = cast("android.os.Vibrator", vibrator_service)
            
            if self._vibrator:
                if hasattr(self._vibrator, 'hasVibrator'):
                    self.has_vibrator = self._vibrator.hasVibrator()
                else:
                    self.has_vibrator = True
            else:
                self.has_vibrator = False
                
        except Exception:
            self.has_vibrator = False

    def vibrate_duration(self, ms=50, intensity=None):
        if not self.enabled or not self.has_vibrator or self._paused or self._cleanup_done:
            return
        
        if intensity is None:
            if ms <= 50:
                intensity = self.button_intensity
            elif ms <= 150:
                intensity = self.steering_intensity
            else:
                intensity = 0.5
        
        intensity = max(0.0, min(1.0, intensity))
        ms = max(1, int(ms))
        
        self._vibration_queue.put((ms, intensity))

    def button_vibrate(self):
        self.vibrate_duration(50, self.button_intensity)

    def steering_vibrate(self, angle_change):
        intensity = min(1.0, abs(angle_change) / 30.0) * self.steering_intensity
        self.vibrate_duration(150, intensity)

    def pedal_vibrate_dynamic(self, pedal_value, pedal_change):
        base_intensity = self.pedal_min + (pedal_value / 100.0) * (self.pedal_max - self.pedal_min)
        change_intensity = min(0.3, abs(pedal_change) / 50.0)
        total_intensity = min(1.0, base_intensity + change_intensity)
        duration = int(100 * total_intensity)
        self.vibrate_duration(duration, total_intensity)

    def connection_vibrate(self):
        self.vibrate_duration(300, 0.8)

    def disconnection_vibrate(self):
        self.vibrate_duration(500, 0.6)

    def signal_lost_vibrate(self):
        self.vibrate_duration(700, 0.9)
    
    def pause(self):
        self._paused = True
        while not self._vibration_queue.empty():
            try:
                self._vibration_queue.get_nowait()
            except Empty:
                break
    
    def resume(self):
        self._paused = False
    
    def cleanup(self):
        self._cleanup_done = True
        self._is_stopping = True
        self.pause()
        
        if self._vibration_thread and self._vibration_thread.is_alive():
            self._vibration_queue.put(None)
            self._vibration_thread.join(timeout=1.0)
        
        self._vibrator = None
        self.has_vibrator = False

# ==================== BATTERY INDICATOR WIDGET ====================
class BatteryIndicator(Widget):
    level = NumericProperty(85)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(pos=self._update_canvas, size=self._update_canvas, level=self._update_canvas)
        Clock.schedule_once(self._update_canvas, 0.1)

    def _update_canvas(self, *args):
        self.canvas.clear()
        try:
            with self.canvas:
                if self.width == 0 or self.height == 0:
                    return
                    
                width, height = self.size
                padding = min(width, height) * 0.1
                body_width = width - padding * 3
                body_height = height - padding * 2
                
                if body_width <= 0 or body_height <= 0:
                    return
                
                Color(0.8, 0.8, 0.8, 1)
                Rectangle(
                    pos=(self.x + padding, self.y + padding),
                    size=(body_width, body_height)
                )
                
                tip_width = padding
                tip_height = body_height * 0.4
                tip_x = self.x + padding + body_width
                tip_y = self.y + padding + (body_height - tip_height) / 2
                Rectangle(
                    pos=(tip_x, tip_y),
                    size=(tip_width, tip_height)
                )
                
                charge_width = max(2, (body_width - 4) * self.level / 100)
                charge_height = body_height - 4
                
                if self.level <= 20:
                    Color(1, 0, 0, 1)
                elif self.level <= 50:
                    Color(1, 0.5, 0, 1)
                else:
                    Color(0, 0.8, 0, 1)
                
                if charge_width > 0 and charge_height > 0:
                    Rectangle(
                        pos=(self.x + padding + 2, self.y + padding + 2),
                        size=(charge_width, charge_height)
                    )
                    
        except Exception:
            pass

# ==================== ROTATABLE IMAGE WIDGET ====================
class RotatableImage(Image):
    angle = NumericProperty(0)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(angle=self._update_rotation)
        self._rotation = None
        with self.canvas.before:
            PushMatrix()
            self._rotation = Rotate(angle=self.angle, origin=self.center)
        with self.canvas.after:
            PopMatrix()

    def _update_rotation(self, *args):
        if self._rotation:
            self._rotation.angle = -self.angle
            self._rotation.origin = self.center

    def on_size(self, *args):
        if self._rotation:
            self._rotation.origin = self.center

    def on_pos(self, *args):
        if self._rotation:
            self._rotation.origin = self.center

# ==================== IMAGE BUTTON CLASSES ====================
class ImageButton(ButtonBehavior, Image):
    
    def __init__(self, normal_source, active_source=None, **kwargs):
        super().__init__(**kwargs)
        self.normal_source = normal_source
        self.active_source = active_source or normal_source
        
        path = asset(normal_source)
        self.source = path
        
        self.is_active = False
        self.controller = None
        self.command = ""
        self.normal_color = (1, 1, 1, 1)
        self.active_color = (0.2, 0.8, 1, 1)
        self.color = self.normal_color

    def on_press(self):
        if self.controller and hasattr(self.controller, 'vibration_manager'):
            self.controller.vibration_manager.button_vibrate()
        
        super().on_press()

    def toggle(self):
        self.is_active = not self.is_active
        self.color = self.active_color if self.is_active else self.normal_color

class MomentaryImageButton(ImageButton):
    
    def __init__(self, normal_source, active_source=None, press_command=None, release_command=None, **kwargs):
        super().__init__(normal_source, active_source, **kwargs)
        self.press_command = press_command or self.command
        self.release_command = release_command or self.command

    def on_press(self):
        if self.controller and hasattr(self.controller, 'vibration_manager'):
            self.controller.vibration_manager.button_vibrate()
        
        if self.controller and self.press_command:
            self.controller.send_command(self.press_command)
            self.color = self.active_color

    def on_release(self):
        if self.controller and self.release_command:
            self.controller.send_command(self.release_command)
            self.color = self.normal_color

# ==================== STEERING WIDGET ====================
class SteeringWidget(BoxLayout):
    controller = ObjectProperty(None)
    angle = NumericProperty(0)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        
        steer_source = 'steer.png'
        path = asset(steer_source)
        
        self.steering_image = RotatableImage(
            source=path,
            allow_stretch=True, 
            keep_ratio=True
        )
        self.add_widget(self.steering_image)
        self.bind(angle=self.update_steering_angle)
        self._touch_down = False
        self._touch_id = None
        self.last_angle = 0
        self.last_vibration_angle = 0
        self.vibration_threshold = 10

    def _get_touch_id(self, touch):
        return getattr(touch, 'id', getattr(touch, 'uid', hash(touch)))

    def update_steering_angle(self, instance, value):
        self.steering_image.angle = value
        
        angle_change = abs(value - self.last_vibration_angle)
        if angle_change > self.vibration_threshold:
            if self.controller and hasattr(self.controller, 'vibration_manager'):
                self.controller.vibration_manager.steering_vibrate(angle_change)
            self.last_vibration_angle = value

    def on_touch_down(self, touch):
        touch_id = self._get_touch_id(touch)
        if self.collide_point(*touch.pos) and not getattr(self.controller, 'accelerometer_mode', False) and not self._touch_down:
            self._touch_down = True
            self._touch_id = touch_id
            return self.process_touch(touch)
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        touch_id = self._get_touch_id(touch)
        if self._touch_down and touch_id == self._touch_id and not getattr(self.controller, 'accelerometer_mode', False):
            return self.process_touch(touch)
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        touch_id = self._get_touch_id(touch)
        if self._touch_down and touch_id == self._touch_id and not getattr(self.controller, 'accelerometer_mode', False):
            self._touch_down = False
            self._touch_id = None
            self.angle = 0
            self.last_angle = 0
            if self.controller:
                self.controller.send_command("S50")
            return True
        return super().on_touch_up(touch)

    def process_touch(self, touch):
        touch_id = self._get_touch_id(touch)
        if not self._touch_down or touch_id != self._touch_id:
            return False
            
        center_x = self.center_x
        center_y = self.center_y
        
        is_bottom_half = touch.y < center_y
        
        relative_x = (touch.x - center_x) / (self.width / 2)
        relative_x = max(-1, min(1, relative_x))
        
        if is_bottom_half:
            relative_x = -relative_x
            
        new_angle = relative_x * 90
        angle_change = abs(new_angle - self.last_angle)
        self.angle = new_angle
        self.last_angle = new_angle
        
        if self.angle >= 0:
            value = 50 + int((self.angle / 90) * 50)
            value = min(100, value)
        else:
            value = 50 + int((self.angle / 90) * 50)
            value = max(0, value)
            
        command = f"S{value:02d}"
        if self.controller:
            self.controller.send_command(command)
        return True

# ==================== PEDAL WIDGET ====================
class PedalWidget(BoxLayout):
    controller = ObjectProperty(None)
    pedal_value = NumericProperty(0)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        
        pedal_source = 'pedal.png'
        path = asset(pedal_source)
            
        self.pedal_image = Image(
            source=path,
            allow_stretch=True,
            keep_ratio=True
        )
        self.add_widget(self.pedal_image)
        
        with self.canvas.after:
            self.overlay_color = Color(1, 0.2, 0.2, 0)
            self.overlay_rect = Rectangle(pos=self.pos, size=(0, 0))
            
        self.bind(pos=self.update_overlay, size=self.update_overlay, pedal_value=self.update_overlay)
        self._touch_down = False
        self._touch_id = None
        self.last_value = 0
        self.last_vibration_value = 0

    def _get_touch_id(self, touch):
        return getattr(touch, 'id', getattr(touch, 'uid', hash(touch)))

    def update_overlay(self, *args):
        if hasattr(self, 'overlay_color') and hasattr(self, 'overlay_rect'):
            if self.pedal_value > 0:
                overlay_height = self.height * (self.pedal_value / 100.0)
                
                self.overlay_rect.pos = (self.x, self.y)
                self.overlay_rect.size = (self.width, overlay_height)
                
                alpha = 0.3 + (self.pedal_value / 100.0) * 0.45
                self.overlay_color.a = alpha
            else:
                self.overlay_rect.size = (0, 0)
                self.overlay_color.a = 0

    def on_touch_down(self, touch):
        touch_id = self._get_touch_id(touch)
        if self.collide_point(*touch.pos) and not self._touch_down:
            self._touch_down = True
            self._touch_id = touch_id
            
            if self.controller and hasattr(self.controller, 'vibration_manager'):
                self.controller.vibration_manager.pedal_vibrate_dynamic(10, 10)
                
            return self.process_touch(touch)
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        touch_id = self._get_touch_id(touch)
        if self._touch_down and touch_id == self._touch_id:
            return self.process_touch(touch)
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        touch_id = self._get_touch_id(touch)
        if self._touch_down and touch_id == self._touch_id:
            self._touch_down = False
            self._touch_id = None
            self.pedal_value = 0
            self.last_value = 0
            if self.controller:
                self.controller.send_command("G00")
            return True
        return super().on_touch_up(touch)

    def process_touch(self, touch):
        touch_id = self._get_touch_id(touch)
        if not self._touch_down or touch_id != self._touch_id:
            return False
            
        relative_y = (touch.y - self.y) / self.height
        new_value = int(relative_y * 100)
        new_value = max(0, min(100, new_value))
        
        value_change = abs(new_value - self.last_value)
        self.pedal_value = new_value
        
        if self.controller and hasattr(self.controller, 'vibration_manager'):
            self.controller.vibration_manager.pedal_vibrate_dynamic(new_value, value_change)
        
        self.last_value = new_value
            
        command = f"G{self.pedal_value:02d}"
        if self.controller:
            self.controller.send_command(command)
        return True

# ==================== COMMAND LOG WIDGET ====================
class CommandLogBox(BoxLayout):
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint_y = None
        self.height = 40
        self.last_command_label = Label(text='--', halign='center', valign='middle')
        self.add_widget(Label(text='Last:', size_hint_x=0.2))
        self.add_widget(self.last_command_label)

    def update_command(self, cmd):
        self.last_command_label.text = cmd

# ==================== UI CONSTANTS ====================
FIGMA_WIDTH = 2340
FIGMA_HEIGHT = 1080

# ==================== BLE TRANSPORT ====================
class BLEScanReceiver(PythonJavaClass):
    __javainterfaces__ = ['android.content.BroadcastReceiver']
    __javacontext__ = 'app'
    __javamethods__ = [
        'onReceive(Landroid/content/Context;Landroid/content/Intent;)V'
    ]
    
    def __init__(self, scan_callback):
        super().__init__()
        self.scan_callback = scan_callback
        self.found_devices = []
        self._active = True
        self._lock = threading.RLock()
        
    @java_method('(Landroid/content/Context;Landroid/content/Intent;)V')
    def onReceive(self, context, intent):
        if not self._active:
            return
            
        try:
            action = intent.getAction()
            
            if action == 'android.bluetooth.device.action.FOUND':
                BluetoothDevice = autoclass('android.bluetooth.BluetoothDevice')
                device = intent.getParcelableExtra(BluetoothDevice.EXTRA_DEVICE)
                
                if device:
                    name = device.getName()
                    address = device.getAddress()
                    
                    if not name:
                        name = "Unknown Device"
                    
                    device_str = f"{name} ({address})"
                    
                    with self._lock:
                        if device_str not in self.found_devices:
                            self.found_devices.append(device_str)
                            
                            if self.scan_callback:
                                Clock.schedule_once(lambda dt, d=device_str: self._safe_callback(d), 0)
                            
            elif action == 'android.bluetooth.adapter.action.DISCOVERY_FINISHED':
                print("Discovery finished")
                if self.scan_callback:
                    Clock.schedule_once(lambda dt: self.scan_callback("__DISCOVERY_FINISHED__"), 0)
                    
        except Exception as e:
            print(f"Error in scan receiver: {e}")
    
    def _safe_callback(self, device_str):
        try:
            with self._lock:
                if self.scan_callback and self._active:
                    self.scan_callback(device_str)
        except:
            pass
    
    def deactivate(self):
        with self._lock:
            self._active = False
            self.scan_callback = None
            self.found_devices = []


class BLECallback(PythonJavaClass):
    __javainterfaces__ = ['android.bluetooth.BluetoothGattCallback']
    __javacontext__ = 'app'
    __javamethods__ = [
        'onConnectionStateChange(Landroid/bluetooth/BluetoothGatt;II)V',
        'onServicesDiscovered(Landroid/bluetooth/BluetoothGatt;I)V',
        'onCharacteristicWrite(Landroid/bluetooth/BluetoothGatt;Landroid/bluetooth/BluetoothGattCharacteristic;I)V'
    ]
    
    def __init__(self, transport):
        super().__init__()
        self.transport = weakref.ref(transport)
        self._active = True
        self._lock = threading.RLock()
        print("BLECallback initialized")

    @java_method('(Landroid/bluetooth/BluetoothGatt;II)V')
    def onConnectionStateChange(self, gatt, status, newState):
        if not self._active:
            return
            
        try:
            transport = self.transport()
            if not transport:
                return
                
            STATE_CONNECTED = 2
            
            if newState == STATE_CONNECTED:
                print("BLE Connected - Starting service discovery...")
                transport.connected = True
                transport.gatt = gatt
                
                gatt.discoverServices()
                print("Service discovery started")
                
                if transport.main_app:
                    Clock.schedule_once(lambda dt: transport.main_app.show_connection_message(
                        "Connected! Discovering services...", "info"
                    ))
                    
            else:
                print("BLE Disconnected")
                transport.connected = False
                transport.gatt = None
                transport.write_char = None
                
                if transport.main_app:
                    Clock.schedule_once(lambda dt: transport.main_app.play_disconnection_sound_and_vibrate())
                    
        except Exception as e:
            print(f"Error in onConnectionStateChange: {e}")

    @java_method('(Landroid/bluetooth/BluetoothGatt;I)V')
    def onServicesDiscovered(self, gatt, status):
        if not self._active:
            return
            
        try:
            transport = self.transport()
            if not transport:
                return
                
            print("Services discovered - searching for writable characteristic...")
            
            if status != 0:
                print(f"Service discovery failed with status: {status}")
                if transport.main_app:
                    Clock.schedule_once(lambda dt: transport.main_app.show_connection_message(
                        "Service discovery failed", "error"
                    ))
                return
            
            services = gatt.getServices()
            services_size = services.size()
            print(f"Found {services_size} services")
            
            PROPERTY_WRITE = 0x08
            PROPERTY_WRITE_NO_RESPONSE = 0x04
            
            found_writable = False
            
            for i in range(services_size):
                service = services.get(i)
                service_uuid = service.getUuid().toString()
                print(f"\nService {i}: {service_uuid}")
                
                characteristics = service.getCharacteristics()
                chars_size = characteristics.size()
                print(f"  Characteristics: {chars_size}")
                
                for j in range(chars_size):
                    ch = characteristics.get(j)
                    
                    uuid = ch.getUuid().toString()
                    properties = ch.getProperties()
                    
                    props_str = []
                    if properties & 0x01: props_str.append("BROADCAST")
                    if properties & 0x02: props_str.append("READ")
                    if properties & 0x04: props_str.append("WRITE_NO_RESPONSE")
                    if properties & 0x08: props_str.append("WRITE")
                    if properties & 0x10: props_str.append("NOTIFY")
                    if properties & 0x20: props_str.append("INDICATE")
                    if properties & 0x40: props_str.append("SIGNED_WRITE")
                    if properties & 0x80: props_str.append("EXTENDED_PROPS")
                    
                    print(f"    Char {j}: {uuid}")
                    print(f"      Properties: {', '.join(props_str) if props_str else 'None'}")
                    
                    if (properties & PROPERTY_WRITE) or (properties & PROPERTY_WRITE_NO_RESPONSE):
                        print(f"      FOUND WRITABLE CHARACTERISTIC!")
                        transport.write_char = ch
                        transport.gatt = gatt
                        transport.connected = True
                        found_writable = True
                        
                        if transport.main_app:
                            Clock.schedule_once(lambda dt: transport.main_app.show_connection_message(
                                "Ready to send commands!", "success"
                            ))
                        
                        Clock.schedule_once(lambda dt: transport.send("S50"), 0.5)
                        break
                
                if found_writable:
                    break
            
            if not found_writable:
                print("No writable characteristic found!")
                if transport.main_app:
                    Clock.schedule_once(lambda dt: transport.main_app.show_connection_message(
                        "No writable characteristic found", "error"
                    ))
                    
        except Exception as e:
            print(f"Error in onServicesDiscovered: {e}")

    @java_method('(Landroid/bluetooth/BluetoothGatt;Landroid/bluetooth/BluetoothGattCharacteristic;I)V')
    def onCharacteristicWrite(self, gatt, characteristic, status):
        if not self._active:
            return
            
        try:
            transport = self.transport()
            if not transport:
                return
                
            if status == 0:
                print(f"Write successful")
                transport.last_communication_time = time.time()
        except Exception as e:
            print(f"Error in onCharacteristicWrite: {e}")
    
    def deactivate(self):
        with self._lock:
            self._active = False
            self.transport = None


class BLETransport:
    """BLE transport for RC car communication"""
    
    def __init__(self):
        self.connected = False
        self.device_name = ""
        self.device_address = ""
        self.transport_type = 'ble'
        self.main_app = None
        self.last_communication_time = 0
        self.signal_check_interval = 5
        self.battery_level = 85
        self.battery_update_callback = None
        self.background_mode = False
        self._cleanup_done = False
        
        self._adapter = None
        self.gatt = None
        self.write_char = None
        self.callback = None
        self.scan_receiver = None
        self.scan_callback = None
        self.found_devices = []
        self._lock = threading.RLock()
        
        if HAS_ANDROID:
            self.initialize()
    
    @safe_jnius_call
    def initialize(self):
        try:
            BluetoothAdapter = autoclass('android.bluetooth.BluetoothAdapter')
            self._adapter = BluetoothAdapter.getDefaultAdapter()
            return True
        except Exception as e:
            print(f"BLE init error: {e}")
            return False
    
    def check_permissions(self):
        if not HAS_ANDROID:
            return True
        
        if SDK_INT >= 31:
            if not check_permission(Permission.BLUETOOTH_SCAN):
                print("BLUETOOTH_SCAN permission not granted")
                return False
            if not check_permission(Permission.BLUETOOTH_CONNECT):
                print("BLUETOOTH_CONNECT permission not granted")
                return False
        else:
            if not check_permission(Permission.ACCESS_FINE_LOCATION):
                print("ACCESS_FINE_LOCATION permission not granted")
                return False
        
        return True
    
    def scan(self, callback):
        if self._cleanup_done:
            return False
            
        if not HAS_ANDROID:
            Clock.schedule_once(lambda dt: callback([
                "BLE scanning only available on Android"
            ]))
            return False
        
        if not self.check_permissions():
            callback(["BLE permissions not granted. Please check app settings."])
            return False
        
        try:
            if not self._adapter:
                if not self.initialize():
                    callback(["Bluetooth adapter not available"])
                    return False
            
            if not self._adapter.isEnabled():
                callback(["Please enable Bluetooth in system settings"])
                return False
            
            with self._lock:
                self.found_devices = []
                self.scan_callback = callback
            
            try:
                if SDK_INT >= 31 and not check_permission(Permission.BLUETOOTH_CONNECT):
                    print("No BLUETOOTH_CONNECT permission for bonded devices")
                else:
                    paired_devices = self._adapter.getBondedDevices()
                    
                    if paired_devices and paired_devices.size() > 0:
                        self.found_devices.append("PAIRED DEVICES:")
                        for i in range(paired_devices.size()):
                            device = paired_devices.get(i)
                            name = device.getName() or "Unknown"
                            address = device.getAddress()
                            self.found_devices.append(f"  {name} ({address})")
            except Exception as e:
                print(f"Error getting bonded devices: {e}")
            
            self.found_devices.append("")
            self.found_devices.append("SCANNING FOR NEW DEVICES...")
            
            callback(self.found_devices.copy())
            
            self._start_discovery()
            
            Clock.schedule_once(lambda dt: self._stop_discovery(), 15)
            
            return True
            
        except Exception as e:
            print(f"Scan error: {e}")
            callback([f"Error: {str(e)}"])
            return False
    
    @safe_jnius_call
    def _start_discovery(self):
        if self._cleanup_done:
            return
            
        try:
            if SDK_INT >= 31 and not check_permission(Permission.BLUETOOTH_SCAN):
                print("Cannot start discovery: BLUETOOTH_SCAN permission denied")
                return
            
            self._adapter.cancelDiscovery()
            
            IntentFilter = autoclass('android.content.IntentFilter')
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            
            self.scan_receiver = BLEScanReceiver(self._on_device_found)
            
            filter = IntentFilter()
            filter.addAction('android.bluetooth.device.action.FOUND')
            filter.addAction('android.bluetooth.adapter.action.DISCOVERY_FINISHED')
            
            activity = PythonActivity.mActivity
            if not activity:
                print("No activity found")
                return
            
            context = activity.getApplicationContext()
            context.registerReceiver(self.scan_receiver, filter)
            
            success = self._adapter.startDiscovery()
            print(f"Discovery started: {success}")
            
        except Exception as e:
            print(f"Error starting discovery: {e}")
    
    @safe_jnius_call
    def _stop_discovery(self):
        if self._cleanup_done:
            return
            
        try:
            if self._adapter:
                self._adapter.cancelDiscovery()
            
            if self.scan_receiver:
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                activity = PythonActivity.mActivity
                if activity:
                    context = activity.getApplicationContext()
                    try:
                        context.unregisterReceiver(self.scan_receiver)
                    except Exception:
                        pass
                self.scan_receiver.deactivate()
                self.scan_receiver = None
            
            if self.scan_callback:
                self.scan_callback("__DISCOVERY_FINISHED__")
            
        except Exception as e:
            print(f"Error stopping discovery: {e}")
    
    def _on_device_found(self, device_str):
        if self._cleanup_done:
            return
            
        if device_str == "__DISCOVERY_FINISHED__":
            if self.scan_callback:
                with self._lock:
                    while "SCANNING FOR NEW DEVICES..." in self.found_devices:
                        self.found_devices.remove("SCANNING FOR NEW DEVICES...")
                    self.found_devices.append("Scan complete")
                    self.scan_callback(self.found_devices.copy())
            return
        
        with self._lock:
            if device_str not in self.found_devices:
                while "SCANNING FOR NEW DEVICES..." in self.found_devices:
                    self.found_devices.remove("SCANNING FOR NEW DEVICES...")
                
                self.found_devices.append(f"  NEW {device_str}")
                self.found_devices.append("SCANNING FOR NEW DEVICES...")
                
                if self.scan_callback:
                    self.scan_callback(self.found_devices.copy())
    
    def connect(self, device_info: str):
        if self._cleanup_done:
            return False
            
        try:
            print(f"Connecting to: {device_info}")
            
            if not HAS_ANDROID:
                print("BLE connection only available on Android")
                return False
            
            if SDK_INT >= 31 and not check_permission(Permission.BLUETOOTH_CONNECT):
                print("Cannot connect: BLUETOOTH_CONNECT permission denied")
                return False
            
            self._stop_discovery()
            
            if '(' in device_info and ')' in device_info:
                address = device_info.split('(')[-1].split(')')[0]
                self.device_name = device_info.split('(')[0].strip()
            else:
                address = device_info
                self.device_name = "BLE Device"
            
            self.device_address = address
            print(f"Device address: {address}")
            
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            BluetoothAdapter = autoclass('android.bluetooth.BluetoothAdapter')
            
            activity = PythonActivity.mActivity
            adapter = BluetoothAdapter.getDefaultAdapter()
            
            if not adapter:
                print("Bluetooth adapter not available")
                return False
            
            device = adapter.getRemoteDevice(address)
            if not device:
                print(f"Could not find device with address: {address}")
                return False
            
            self.callback = BLECallback(self)
            
            print("Connecting GATT...")
            self.gatt = device.connectGatt(
                activity,
                False,
                self.callback
            )
            
            if self.gatt:
                print("GATT connection initiated")
                return True
            else:
                print("Failed to initiate GATT connection")
                return False
            
        except Exception as e:
            print(f"Connect error: {e}")
            return False
    
    def send(self, data: str) -> bool:
        if self._cleanup_done:
            return False
            
        if not self.connected or not self.write_char:
            return False
        
        if not HAS_ANDROID:
            self.last_communication_time = time.time()
            return True
        
        try:
            value = bytearray(data.encode('utf-8'))
            self.write_char.setValue(value)
            result = self.gatt.writeCharacteristic(self.write_char)
            
            if result:
                self.last_communication_time = time.time()
            
            return result
            
        except Exception as e:
            print(f"Send error: {e}")
            return False
    
    def disconnect(self) -> bool:
        try:
            self.connected = False
            
            if self.gatt:
                self.gatt.disconnect()
                self.gatt.close()
                self.gatt = None
            
            self.write_char = None
            self.callback = None
            print("Disconnected")
            return True
            
        except Exception as e:
            print(f"Disconnect error: {e}")
            return False
    
    def set_background_mode(self, background: bool):
        self.background_mode = background
    
    def set_battery_callback(self, callback):
        self.battery_update_callback = callback
    
    def check_signal_strength(self) -> int:
        if not self.connected:
            return 0
            
        elapsed = time.time() - self.last_communication_time
        if elapsed > self.signal_check_interval * 3:
            return 0
        elif elapsed > self.signal_check_interval:
            return 1
        else:
            return 2
    
    def cleanup(self):
        with self._lock:
            if self._cleanup_done:
                return
                
            self._cleanup_done = True
            self.disconnect()
            self._stop_discovery()
            
            if self.callback and hasattr(self.callback, 'deactivate'):
                self.callback.deactivate()
            
            self.callback = None
            self.scan_callback = None
            self._adapter = None


class ConnectionManager:
    """Manages BLE connection only"""
    
    def __init__(self):
        self.transport = BLETransport()
        self.connected = False
        self.device_name = ""
        self.battery_level = 85
        self.main_app = None
        
        self._command_queue = Queue()
        self._command_worker_thread = None
        self._signal_check_event = None
        self._keep_alive_event = None
        self._is_background = False
        self._cleanup_done = False
        self._lock = threading.RLock()
        
        self.BACKGROUND_KEEPALIVE_INTERVAL = 15
        self.FOREGROUND_KEEPALIVE_INTERVAL = 25
        
        self.transport.main_app = self
        self.start_command_worker()
    
    def set_main_app(self, app):
        self.main_app = app
        self.transport.main_app = app
    
    def start_command_worker(self):
        if self._command_worker_thread and self._command_worker_thread.is_alive():
            return
        
        def command_worker():
            while not self._cleanup_done:
                try:
                    task = self._command_queue.get(timeout=1.0)
                    if task is None:
                        break
                    
                    self.transport.send(task)
                    self._command_queue.task_done()
                    
                except Empty:
                    continue
                except Exception:
                    continue
        
        self._command_worker_thread = threading.Thread(
            target=command_worker,
            daemon=True,
            name="ConnectionCommandWorker"
        )
        self._command_worker_thread.start()
    
    def scan(self, callback):
        if self._cleanup_done:
            return False
        return self.transport.scan(callback)
    
    def connect(self, device_info: str) -> bool:
        if self._cleanup_done:
            return False
            
        success = self.transport.connect(device_info)
        
        if success:
            self.connected = True
            self.device_name = self.transport.device_name
            
            self.transport.set_battery_callback(self._on_battery_update)
            
            self._start_signal_monitoring()
        
        return success
    
    def send(self, data: str) -> bool:
        if self._cleanup_done:
            return False
            
        if not self.connected:
            return False
        
        self._command_queue.put(data)
        return True
    
    def disconnect(self):
        try:
            with self._lock:
                self.connected = False
                self.device_name = ""
                
                self._stop_signal_monitoring()
                self._stop_keep_alive()
                
                self.transport.disconnect()
            
            return True
        except Exception:
            return False
    
    def _on_battery_update(self, level: int):
        self.battery_level = level
        if self.main_app:
            Clock.schedule_once(lambda dt: self.main_app.update_battery_level(level))
    
    def _start_signal_monitoring(self):
        if self._signal_check_event:
            self._signal_check_event.cancel()
        
        self._signal_check_event = Clock.schedule_interval(self._check_signal, 3)
    
    def _stop_signal_monitoring(self):
        if self._signal_check_event:
            self._signal_check_event.cancel()
            self._signal_check_event = None
    
    def _check_signal(self, dt):
        try:
            if self.connected and self.main_app and not self._cleanup_done:
                signal_strength = self.transport.check_signal_strength()
                
                if signal_strength == 0:
                    Clock.schedule_once(lambda dt: self.main_app.on_signal_lost())
        except Exception:
            pass
    
    def _start_keep_alive(self):
        if self._keep_alive_event:
            self._keep_alive_event.cancel()
        
        interval = self.BACKGROUND_KEEPALIVE_INTERVAL if self._is_background else self.FOREGROUND_KEEPALIVE_INTERVAL
        self._keep_alive_event = Clock.schedule_interval(self._send_keep_alive, interval)
    
    def _stop_keep_alive(self):
        if self._keep_alive_event:
            self._keep_alive_event.cancel()
            self._keep_alive_event = None
    
    def set_background_mode(self, is_background: bool):
        if self._cleanup_done:
            return
            
        self._is_background = is_background
        self.transport.set_background_mode(is_background)
        
        if self._keep_alive_event:
            self._keep_alive_event.cancel()
        
        self._start_keep_alive()
    
    def _send_keep_alive(self, dt):
        if self.connected and not self._cleanup_done:
            try:
                current_time = time.time()
                last_comm = self.transport.last_communication_time
                
                threshold = self.BACKGROUND_KEEPALIVE_INTERVAL * 2 if self._is_background else self.FOREGROUND_KEEPALIVE_INTERVAL * 2
                
                if current_time - last_comm > threshold:
                    self.send("PING")
                    
            except Exception:
                pass
    
    def cleanup(self):
        with self._lock:
            if self._cleanup_done:
                return
                
            self._cleanup_done = True
            
            self.disconnect()
            
            if self._command_worker_thread and self._command_worker_thread.is_alive():
                self._command_queue.put(None)
                self._command_worker_thread.join(timeout=2.0)
                self._command_worker_thread = None
            
            self.transport.cleanup()
            
            self._stop_signal_monitoring()
            self._stop_keep_alive()
            
            self.main_app = None


class LifecycleManager:
    """Manages application lifecycle events (pause/resume)"""
    
    def __init__(self, app_root):
        self.app_root = weakref.ref(app_root)
        self.background_mode = False
        self.connection_state = None
        self._cleanup_done = False
        
    def on_pause(self):
        print("App going to background")
        self.background_mode = True
        
        app_root = self.app_root()
        if not app_root:
            return True
        
        if hasattr(app_root, 'vibration_manager') and app_root.vibration_manager:
            app_root.vibration_manager.pause()
        
        try:
            if hasattr(app_root, 'connection_manager') and app_root.connection_manager:
                cm = app_root.connection_manager
                
                self.connection_state = {
                    'connected': getattr(cm, 'connected', False),
                    'device': getattr(cm, 'device_name', '')
                }
                
                if getattr(cm, 'connected', False):
                    cm.set_background_mode(True)
                    
        except Exception as e:
            print(f"Error saving connection state: {e}")
        
        try:
            if hasattr(app_root, 'accelerometer_manager') and app_root.accelerometer_manager:
                app_root.accelerometer_manager.stop()
        except Exception:
            pass
        
        return True
    
    def on_resume(self):
        print("App returning to foreground")
        self.background_mode = False
        
        app_root = self.app_root()
        if not app_root:
            return True
        
        if hasattr(app_root, 'vibration_manager') and app_root.vibration_manager:
            app_root.vibration_manager.resume()
        
        try:
            if hasattr(app_root, 'connection_manager') and app_root.connection_manager:
                cm = app_root.connection_manager
                cm.set_background_mode(False)
                
                if hasattr(app_root, 'update_connection_status'):
                    Clock.schedule_once(lambda dt: app_root.update_connection_status())
                
                if (self.connection_state and 
                    self.connection_state.get('connected', False) and 
                    not getattr(cm, 'connected', False)):
                    print("Attempting automatic reconnection...")
                    self._attempt_reconnection()
        except Exception as e:
            print(f"Error in on_resume: {e}")
        
        return True
    
    def _attempt_reconnection(self):
        app_root = self.app_root()
        if not app_root:
            return
            
        def reconnect_attempt(attempt=1):
            try:
                if attempt > 3:
                    print("Reconnection failed after 3 attempts")
                    if app_root:
                        Clock.schedule_once(
                            lambda dt: app_root.show_connection_message(
                                "Reconnection failed. Please connect manually.",
                                "error"
                            )
                        )
                    return
                
                if hasattr(app_root, 'connection_manager'):
                    cm = app_root.connection_manager
                    
                    if not getattr(cm, 'connected', False) and self.connection_state and self.connection_state.get('connected', False):
                        print(f"Reconnection attempt {attempt}...")
                        
                        if app_root:
                            Clock.schedule_once(
                                lambda dt: app_root.show_connection_message(
                                    f"Reconnecting...",
                                    "info"
                                )
                            )
                        
                        if attempt < 3:
                            Clock.schedule_once(
                                lambda dt: reconnect_attempt(attempt + 1),
                                2.0
                            )
                        
            except Exception as e:
                print(f"Reconnection error: {e}")
                if attempt < 3:
                    Clock.schedule_once(
                        lambda dt: reconnect_attempt(attempt + 1),
                        2.0
                    )
        
        Clock.schedule_once(lambda dt: reconnect_attempt(), 1.0)
    
    def cleanup(self):
        self._cleanup_done = True
        self.connection_state = None
        self.app_root = None


# ==================== ACCELEROMETER CLASSES (OPTIMIZED) ====================

class AccelerometerListener(PythonJavaClass):
    __javainterfaces__ = ['android.hardware.SensorEventListener']
    __javacontext__ = 'app'
    __javamethods__ = [
        'onSensorChanged(Landroid/hardware/SensorEvent;)V',
        'onAccuracyChanged(Landroid/hardware/Sensor;I)V'
    ]
    
    def __init__(self, callback):
        super().__init__()
        self.callback = callback
        self._active = True
        self._last_update_time = 0
        self._update_interval = 0.02

    @java_method('(Landroid/hardware/SensorEvent;)V')
    def onSensorChanged(self, event):
        if not self._active:
            return
        
        try:
            values = event.values
            if not values or len(values) < 3:
                return
            
            x = float(values[0])
            y = float(values[1])
            z = float(values[2])
            
            current_time = time.time()
            if current_time - self._last_update_time < self._update_interval:
                return
            self._last_update_time = current_time
            
            if self.callback and callable(self.callback):
                if abs(z) < 0.1:
                    z = 0.1 if z >= 0 else -0.1
                
                tilt = math.degrees(math.atan2(y, z))
                angle = max(-90, min(90, tilt * 1.5))
                
                if abs(angle) < 5:
                    angle = 0
                
                Clock.schedule_once(lambda dt, a=angle: self._safe_callback(a), 0)
                
        except Exception as e:
            print(f"Accelerometer sensor error: {e}")
    
    def _safe_callback(self, angle):
        try:
            if self._active and self.callback:
                self.callback(angle)
        except Exception:
            pass

    @java_method('(Landroid/hardware/Sensor;I)V')
    def onAccuracyChanged(self, sensor, accuracy):
        pass
    
    def deactivate(self):
        self._active = False
        self.callback = None


class AccelerometerManager:
    """Manages accelerometer sensor for steering control"""
    
    def __init__(self, callback=None):
        self.callback = callback
        self.sensor_manager = None
        self.sensor = None
        self._listener = None
        self.is_active = False
        self.steering_angle = 0
        self.sensitivity = 1.0
        self._is_stopping = False
        self._cleanup_done = False
        self._lock = threading.RLock()
        
        if HAS_ANDROID:
            Clock.schedule_once(self.setup_sensor, 0.8)

    def setup_sensor(self, dt=None):
        if not HAS_ANDROID:
            return False
            
        try:
            from jnius import autoclass, cast
            
            Context = autoclass('android.content.Context')
            Sensor = autoclass('android.hardware.Sensor')
            SensorManager = autoclass('android.hardware.SensorManager')
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            
            activity = PythonActivity.mActivity
            if not activity:
                return False
                
            sensor_service = activity.getSystemService(Context.SENSOR_SERVICE)
            self.sensor_manager = cast(SensorManager, sensor_service)
            
            self.sensor = self.sensor_manager.getDefaultSensor(Sensor.TYPE_ACCELEROMETER)
            
            print("✅ Accelerometer sensor found" if self.sensor else "❌ No accelerometer sensor")
            return bool(self.sensor)
            
        except Exception as e:
            print(f"Accelerometer setup error: {e}")
            return False

    def start(self):
        with self._lock:
            if self._cleanup_done or self._is_stopping:
                return False
        
        try:
            if not self.sensor or not self.sensor_manager:
                if not self.setup_sensor():
                    return False
            
            if self._listener:
                self.stop()
            
            self._listener = AccelerometerListener(self.on_sensor_changed)
            
            success = self.sensor_manager.registerListener(
                self._listener,
                self.sensor,
                1
            )
            
            if success:
                self.is_active = True
                print("✅ Accelerometer started successfully")
                return True
            else:
                print("❌ Failed to register accelerometer")
                return False
                
        except Exception as e:
            print(f"Accelerometer start error: {e}")
            return False

    def stop(self):
        with self._lock:
            if not self.is_active or self._is_stopping or self._cleanup_done:
                return True
            
            self._is_stopping = True
        
        try:
            if self.sensor_manager and self._listener:
                self.sensor_manager.unregisterListener(self._listener)
            
            if self._listener:
                self._listener.deactivate()
            
            self.is_active = False
            print("✅ Accelerometer stopped")
            return True
            
        except Exception as e:
            print(f"Accelerometer stop error: {e}")
            return False
        finally:
            self._is_stopping = False

    def on_sensor_changed(self, angle):
        if self.is_active and self.callback:
            self.steering_angle = angle
            self.callback(angle)

    def set_sensitivity(self, s):
        self.sensitivity = max(0.5, min(2.5, s))

    def set_callback(self, callback):
        self.callback = callback

    def cleanup(self):
        self._cleanup_done = True
        self.stop()
        self._listener = None
        self.sensor_manager = None
        self.sensor = None
        self.callback = None


class ThreadManager:
    _active_threads = []
    _lock = threading.RLock()
    _command_queue = Queue()
    _worker_thread = None
    _is_paused = False
    _cleanup_done = False
    
    @classmethod
    def start_command_worker(cls):
        if cls._worker_thread and cls._worker_thread.is_alive():
            return
        
        def worker():
            while not cls._cleanup_done:
                try:
                    task = cls._command_queue.get(timeout=1.0)
                    if task is None:
                        break
                    
                    if isinstance(task, tuple) and len(task) >= 2:
                        cmd = task[0]
                        
                        if cmd == 'PAUSE':
                            cls._is_paused = True
                            continue
                        elif cmd == 'RESUME':
                            cls._is_paused = False
                            continue
                        elif cmd == 'COMMAND' and len(task) >= 3:
                            if cls._is_paused:
                                func, args, kwargs = task[1], task[2][0], task[2][1]
                                Clock.schedule_once(lambda dt: func(*args, **kwargs))
                            else:
                                func, args, kwargs = task[1], task[2][0], task[2][1]
                                try:
                                    func(*args, **kwargs)
                                except Exception:
                                    pass
                    else:
                        if isinstance(task, tuple) and len(task) >= 2:
                            func, args = task[0], task[1:]
                            try:
                                func(*args)
                            except Exception:
                                pass
                    
                    cls._command_queue.task_done()
                except Empty:
                    continue
                except Exception:
                    continue
        
        cls._worker_thread = threading.Thread(target=worker, daemon=True, name="CommandWorker")
        cls._worker_thread.start()
    
    @classmethod
    def pause_all_threads(cls):
        with cls._lock:
            if cls._worker_thread and cls._worker_thread.is_alive():
                cls._command_queue.put(('PAUSE',))
    
    @classmethod
    def resume_all_threads(cls):
        with cls._lock:
            if cls._worker_thread and cls._worker_thread.is_alive():
                cls._command_queue.put(('RESUME',))
    
    @classmethod
    def queue_command(cls, func, *args, **kwargs):
        cls._command_queue.put(('COMMAND', func, (args, kwargs)))
    
    @classmethod
    def track_thread(cls, thread):
        with cls._lock:
            if thread and thread not in cls._active_threads:
                cls._active_threads.append(thread)
    
    @classmethod
    def cleanup_threads(cls):
        with cls._lock:
            cls._cleanup_done = True
            
            if cls._worker_thread and cls._worker_thread.is_alive():
                cls._command_queue.put(None)
                cls._worker_thread.join(timeout=2.0)
                cls._worker_thread = None
            
            for thread in cls._active_threads[:]:
                if thread and thread.is_alive():
                    try:
                        thread.join(timeout=1.0)
                    except:
                        pass
            
            cls._active_threads.clear()
            
            while not cls._command_queue.empty():
                try:
                    cls._command_queue.get_nowait()
                except Empty:
                    break


class JavaObjectManager:
    _java_objects = []
    _weak_refs = []
    _lock = threading.RLock()
    _cleanup_done = False
    
    @classmethod
    def track(cls, obj):
        if obj is None:
            return obj
            
        if not HAS_ANDROID:
            return obj
        
        with cls._lock:
            try:
                if hasattr(obj, '__javaclass__') or (hasattr(obj, '__javainterfaces__') and hasattr(obj, '__javacontext__')):
                    ref = weakref.ref(obj, cls._on_object_deleted)
                    cls._java_objects.append(ref)
                    
                    if hasattr(obj, '__javainterfaces__'):
                        callback_ref = weakref.ref(obj)
                        cls._weak_refs.append(callback_ref)
                    
                    return obj
                else:
                    return obj
            except Exception:
                return obj
    
    @classmethod
    def _on_object_deleted(cls, weakref):
        pass
    
    @classmethod
    def untrack(cls, obj):
        if not HAS_ANDROID or obj is None:
            return obj
            
        with cls._lock:
            try:
                for i, ref in enumerate(cls._java_objects[:]):
                    obj_ref = ref()
                    if obj_ref is not None and obj_ref is obj:
                        cls._java_objects.pop(i)
                        break
                
                for i, ref in enumerate(cls._weak_refs[:]):
                    obj_ref = ref()
                    if obj_ref is not None and obj_ref is obj:
                        cls._weak_refs.pop(i)
                        break
            except Exception:
                pass
            
            return obj
    
    @classmethod
    def cleanup(cls):
        print("JavaObjectManager cleanup started")
        
        with cls._lock:
            if cls._cleanup_done:
                return
                
            cls._cleanup_done = True
            
            cls._weak_refs.clear()
            
            java_objects_to_process = []
            for ref in cls._java_objects[:]:
                obj = ref()
                if obj is not None:
                    java_objects_to_process.append(obj)
            
            cls._java_objects.clear()
            
            for obj in java_objects_to_process:
                try:
                    if obj is not None and hasattr(obj, 'deactivate'):
                        obj.deactivate()
                except Exception:
                    pass
            
            gc.collect()
            
            print(f"JavaObjectManager cleanup completed - processed {len(java_objects_to_process)} objects")


# ==================== MAIN APPLICATION ROOT ====================
class CombinedAppRoot(FloatLayout):
    
    battery_level = StringProperty("85%")
    connected_device = StringProperty("Not Connected")
    connection_status = StringProperty("Disconnected")
    accelerometer_mode = BooleanProperty(False)
    _is_background = BooleanProperty(False)
    _menu_opening = BooleanProperty(False)
    _accelerometer_button_cooldown = BooleanProperty(False)
    _was_connected = BooleanProperty(False)
    _in_connection_menu = BooleanProperty(False)
    _permissions_checked = BooleanProperty(False)
    _scan_in_progress = BooleanProperty(False)
    _last_scan_time = NumericProperty(0)
    SCAN_COOLDOWN = 10

    RIGHT_HANDED_ITEMS = [
        ('pedal', 10, 180, 450, 950, 'pedal.png'),
        ('start', 664, 730, 170, 170, 'start.png'),
        ('r', 470, 886, 150, 150, 'r.png'),
        ('n', 470, 736, 150, 150, 'n.png'),
        ('d', 470, 587, 150, 150, 'd.png'),
        ('light', 1520, 544, 150, 150, 'light.png'),
        ('lightHorn', 1470, 721, 150, 150, 'light_horn.png'),
        ('left', 1650, 430, 150, 150, 'left.png'),
        ('hazard', 1842, 350, 150, 150, 'hazard.png'),
        ('horn', 2155, 544, 150, 150, 'horn.png'),
        ('rgb', 1520, 906, 150, 150, 'rgb.png'),
        ('right', 2035, 430, 150, 150, 'right.png'),
        ('bluetooth', 1300, 950, 120, 120, 'ble.png'),
        ('accelerometer', 2020, 200, 150, 150, 'accelerometer.png'),
        ('steer', 1650, 544, 530, 530, 'steer.png'),
        ('setting', 1865, 220, 110, 110, 'setting.png'),
        ('led', 2210, 720, 150, 150, 'led.png'),
        ('battery_title', 1215, 346, 200, 100, ''),
        ('battery_indicator', 1230, 412, 170, 80, ''),
        ('battery_percent', 1235, 412, 170, 80, ''),
        ('command_display', 886, 380, 110, 110, ''),
        ('device_display', 900, 956, 200, 80, ''),
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        Window.fullscreen = 'auto'
        Window.borderless = True
        
        sys.excepthook = global_exception_hook
        
        self.connection_manager = ConnectionManager()
        self.connection_manager.set_main_app(self)
        self.accelerometer_manager = AccelerometerManager(
            callback=self.update_steering_from_accelerometer
        )
        self.vibration_manager = VibrationManager()
        self.lifecycle_manager = LifecycleManager(self)

        self.connected_sound = None
        self.disconnected_sound = None
        self.signal_lost_sound = None
        self.load_connection_sounds()

        self.current_gear = 'N'
        self.current_turn_signal = None
        self.signal_check_event = None

        self.handedness = 'right'
        self.items = self.RIGHT_HANDED_ITEMS

        with self.canvas.before:
            Color(1, 1, 1, 1)
            self.bgrect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_bg, size=self._update_bg)

        self.command_log = CommandLogBox(pos_hint={'x': 0, 'y': 0})
        self.add_widget(self.command_log)

        Window.bind(size=self.on_window_size)

        self.loading_label = Label(
            text='Loading...\nPlease wait',
            font_size='24sp',
            color=(0.3, 0.3, 0.3, 1),
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            halign='center',
            valign='middle'
        )
        self.loading_label.bind(size=self.loading_label.setter('text_size'))
        self.add_widget(self.loading_label)
        
        ui_build_delay = get_setting('ui_build_delay', 0.8)
        print(f"Scheduling UI build with delay: {ui_build_delay}s")
        
        self._ui_built = False
        Clock.schedule_once(self._build_ui, ui_build_delay)
        
        Clock.schedule_once(self._load_saved_settings, 1.0)
        
        ThreadManager.start_command_worker()
        
        Clock.schedule_interval(self._check_background_status, 10)

    def on_pause(self):
        print("on_pause CALLED")
        self._is_background = True
        return self.lifecycle_manager.on_pause()
    
    def on_resume(self):
        print("on_resume CALLED")
        self._is_background = False
        self.lifecycle_manager.on_resume()
        return True

    def _check_background_status(self, dt):
        if self._is_background and self.connection_manager.connected:
            print(f"Background: BLE connection active")

    def _update_bg(self, *args):
        self.bgrect.pos = self.pos
        self.bgrect.size = self.size

    def on_window_size(self, instance, value):
        if not self._ui_built:
            return
            
        self._update_ui_positions()

    def load_connection_sounds(self):
        try:
            connected_path = asset('connected.mp3')
            if connected_path:
                self.connected_sound = SoundLoader.load(connected_path)
            
            disconnected_path = asset('disconnected.mp3')
            if disconnected_path:
                self.disconnected_sound = SoundLoader.load(disconnected_path)
            
            signal_lost_path = asset('signal_lost.mp3')
            if signal_lost_path:
                self.signal_lost_sound = SoundLoader.load(signal_lost_path)
                    
        except Exception as e:
            print(f"Error loading connection sounds: {e}")
    
    def play_connection_sound_and_vibrate(self):
        if self.connected_sound:
            try:
                self.connected_sound.play()
            except Exception:
                pass
        
        if hasattr(self, 'vibration_manager') and self.vibration_manager:
            try:
                self.vibration_manager.connection_vibrate()
            except Exception:
                pass
    
    def play_disconnection_sound_and_vibrate(self):
        if self.disconnected_sound:
            try:
                self.disconnected_sound.play()
            except Exception:
                pass
        
        if hasattr(self, 'vibration_manager') and self.vibration_manager:
            try:
                self.vibration_manager.disconnection_vibrate()
            except Exception:
                pass
    
    def play_signal_lost_sound_and_vibrate(self):
        if self.signal_lost_sound:
            try:
                self.signal_lost_sound.play()
            except Exception:
                pass
        
        if hasattr(self, 'vibration_manager') and self.vibration_manager:
            try:
                self.vibration_manager.signal_lost_vibrate()
            except Exception:
                pass

    def on_signal_lost(self):
        if self.connection_manager.connected:
            self.play_signal_lost_sound_and_vibrate()
            
            self.connection_status = "Signal Lost"
            self.connected_device = "Signal Lost"
            
            self.show_connection_message("Signal lost! Trying to reconnect...", "warning")
            
            self.connection_manager.disconnect()

    def _load_saved_settings(self, dt=None):
        if not self._ui_built:
            Clock.schedule_once(self._load_saved_settings, 0.2)
            return
            
        try:
            sensitivity = get_setting('sensitivity', 1.0)
            if self.accelerometer_manager:
                self.accelerometer_manager.sensitivity = sensitivity
            
            vibration_enabled = get_setting('vibration_enabled', True)
            
            if self.vibration_manager:
                self.vibration_manager.enabled = vibration_enabled
            
            self.handedness = 'right'
            self.items = self.RIGHT_HANDED_ITEMS
            
            if self._ui_built:
                self._rebuild_ui()
            
        except Exception as e:
            print(f"Error loading settings: {e}")

    def _update_ui_positions(self):
        if not self._ui_built:
            return
            
        win_w, win_h = Window.size
        
        target_ratio = FIGMA_WIDTH / FIGMA_HEIGHT
        current_ratio = win_w / win_h
        
        safe_area_top = max(0, win_h * 0.03) if HAS_ANDROID else 0
        safe_area_bottom = max(0, win_h * 0.03) if HAS_ANDROID else 0
        usable_height = win_h - safe_area_top - safe_area_bottom
        
        if current_ratio > target_ratio:
            scale = usable_height / FIGMA_HEIGHT
            margin_x = (win_w - FIGMA_WIDTH * scale) / 2
            margin_y = safe_area_bottom
        else:
            scale = win_w / FIGMA_WIDTH
            margin_x = 0
            margin_y = (win_h - FIGMA_HEIGHT * scale) / 2

        for name, x, y, w, h, src in self.items:
            if name in self.widgets:
                y_corrected = FIGMA_HEIGHT - (y + h)
                x_scaled = x * scale + margin_x
                y_scaled = y_corrected * scale + margin_y
                w_scaled = w * scale
                h_scaled = h * scale
                
                widget = self.widgets[name]
                if hasattr(widget, 'pos'):
                    widget.pos = (x_scaled, y_scaled)
                if hasattr(widget, 'size'):
                    widget.size = (w_scaled, h_scaled)

        cmd_log_width = max(180, win_w * 0.18)
        cmd_log_height = max(35, win_h * 0.045)
        self.command_log.pos = (win_w - cmd_log_width - 10, 10 + safe_area_bottom)
        self.command_log.size = (cmd_log_width, cmd_log_height)

    def update_battery_level(self, level):
        self.battery_level = f"{level}%"
        
        if 'battery_indicator' in self.widgets:
            self.widgets['battery_indicator'].level = level

    def update_connection_status(self):
        if not self._ui_built:
            return
            
        if self.connection_manager.connected:
            self.connection_status = "Connected (BLE)"
            self.connected_device = f"Connected: {self.connection_manager.device_name}"
        else:
            self.connection_status = "Disconnected"
            self.connected_device = "Not Connected"

    def _build_ui(self, dt):
        if self._ui_built:
            print("UI already built, skipping duplicate build")
            if hasattr(self, 'loading_label') and self.loading_label in self.children:
                self.remove_widget(self.loading_label)
            return
            
        if hasattr(self, 'loading_label') and self.loading_label in self.children:
            self.remove_widget(self.loading_label)
            
        win_w, win_h = Window.size
        
        target_ratio = FIGMA_WIDTH / FIGMA_HEIGHT
        current_ratio = win_w / win_h
        
        safe_area_top = 0
        safe_area_bottom = 0
        
        if HAS_ANDROID:
            safe_area_top = max(0, win_h * 0.03)
            safe_area_bottom = max(0, win_h * 0.03)
        
        usable_height = win_h - safe_area_top - safe_area_bottom
        
        if current_ratio > target_ratio:
            scale = usable_height / FIGMA_HEIGHT
            margin_x = (win_w - FIGMA_WIDTH * scale) / 2
            margin_y = safe_area_bottom
        else:
            scale = win_w / FIGMA_WIDTH
            margin_x = 0
            margin_y = (win_h - FIGMA_HEIGHT * scale) / 2

        self.widgets = {}

        for name, x, y, w, h, src in self.items:
            y_corrected = FIGMA_HEIGHT - (y + h)
            x_scaled = x * scale + margin_x
            y_scaled = y_corrected * scale + margin_y
            w_scaled = w * scale
            h_scaled = h * scale
            pos = (x_scaled, y_scaled)

            try:
                if name == 'battery_title':
                    battery_title_box = BoxLayout(
                        orientation='vertical',
                        size_hint=(None, None),
                        size=(w_scaled, h_scaled),
                        pos=pos
                    )
                    
                    battery_title = Label(
                        text='Battery',
                        size_hint_y=1,
                        font_size='14sp',
                        color=(0, 0, 0, 1),
                        halign='center',
                        valign='middle'
                    )
                    
                    battery_title_box.add_widget(battery_title)
                    self.add_widget(battery_title_box)
                    continue

                if name == 'battery_indicator':
                    battery_indicator = BatteryIndicator(
                        size_hint=(None, None),
                        size=(w_scaled, h_scaled),
                        pos=pos
                    )
                    
                    self.widgets['battery_indicator'] = battery_indicator
                    
                    def update_battery_indicator(instance, battery_text):
                        try:
                            level = int(''.join(filter(str.isdigit, battery_text)))
                            battery_indicator.level = level
                            battery_indicator._update_canvas()
                        except (ValueError, TypeError):
                            pass
                    
                    self.bind(battery_level=update_battery_indicator)
                    
                    battery_indicator.level = 85
                    
                    self.add_widget(battery_indicator)
                    continue

                if name == 'battery_percent':
                    battery_percent_box = BoxLayout(
                        orientation='vertical',
                        size_hint=(None, None),
                        size=(w_scaled, h_scaled),
                        pos=pos
                    )
                    
                    self.battery_percent_label = Label(
                        text=self.battery_level,
                        size_hint_y=1,
                        font_size='14sp',
                        color=(0, 0, 0, 1),
                        halign='center',
                        valign='middle',
                        bold=True
                    )
                    
                    battery_percent_box.add_widget(self.battery_percent_label)
                    self.add_widget(battery_percent_box)
                    
                    def update_battery_percent(instance, battery_text):
                        self.battery_percent_label.text = battery_text
                        try:
                            level = int(''.join(filter(str.isdigit, battery_text)))
                            if level <= 20:
                                self.battery_percent_label.color = (1, 0, 0, 1)
                            elif level <= 60:
                                self.battery_percent_label.color = (1, 0.5, 0, 1)
                            else:
                                self.battery_percent_label.color = (0, 0.5, 0, 1)
                        except (ValueError, TypeError):
                            pass
                    
                    self.bind(battery_level=update_battery_percent)
                    continue

                if name == 'steer':
                    size = min(w_scaled, h_scaled)
                    steer = SteeringWidget(
                        size_hint=(None, None),
                        size=(size, size),
                        pos=(x_scaled + (w_scaled - size)/2, y_scaled + (h_scaled - size)/2)
                    )
                    steer.controller = self
                    self.add_widget(steer)
                    self.widgets['steer'] = steer
                    continue

                if name == 'pedal':
                    pedal = PedalWidget(
                        size_hint=(None, None),
                        size=(w_scaled, h_scaled),
                        pos=pos
                    )
                    pedal.controller = self
                    self.add_widget(pedal)
                    self.widgets['pedal'] = pedal
                    continue

                if name in ('n', 'r', 'd'):
                    btn = ImageButton(normal_source=asset(src))
                    btn.controller = self
                    btn.command = name.upper()
                    btn.size_hint = (None, None)
                    btn.size = (w_scaled, h_scaled)
                    btn.pos = pos
                    btn.bind(on_press=self._on_gear_pressed)
                    
                    if name == 'n':
                        btn.is_active = True
                        btn.color = btn.active_color
                        self.current_gear = 'N'
                    else:
                        btn.is_active = False
                        btn.color = btn.normal_color
                        
                    self.add_widget(btn)
                    self.widgets[name] = btn
                    continue

                if name == 'bluetooth':
                    btn = ImageButton(normal_source=asset(src))
                    btn.controller = self
                    btn.command = "BLE"
                    btn.size_hint = (None, None)
                    btn.size = (w_scaled, h_scaled)
                    btn.pos = pos
                    
                    def safe_show_connection(instance):
                        try:
                            self.safe_open_connection_menu()
                        except Exception as e:
                            print(f"Bluetooth button error: {e}")
                            self.show_connection_message(f"Menu error: {str(e)[:50]}", "error")
                    
                    btn.bind(on_press=safe_show_connection)
                    self.add_widget(btn)
                    self.widgets['bluetooth'] = btn
                    continue

                if name == 'accelerometer':
                    btn = ImageButton(normal_source=asset(src))
                    btn.controller = self
                    btn.command = "ACC"
                    btn.size_hint = (None, None)
                    btn.size = (w_scaled, h_scaled)
                    btn.pos = pos
                    btn.bind(on_press=self.on_accelerometer_toggle)
                    btn.is_active = False
                    btn.color = btn.normal_color
                    self.add_widget(btn)
                    self.widgets['accelerometer'] = btn
                    continue

                if name == 'setting':
                    btn = ImageButton(normal_source=asset(src))
                    btn.controller = self
                    btn.size_hint = (None, None)
                    btn.size = (w_scaled, h_scaled)
                    btn.pos = pos
                    
                    def on_setting_click(instance):
                        self.safe_open_settings()
                    
                    btn.bind(on_press=on_setting_click)
                    self.add_widget(btn)
                    self.widgets['setting'] = btn
                    continue

                if name == 'command_display':
                    cmd_box = BoxLayout(
                        orientation='vertical',
                        size_hint=(None, None),
                        size=(w_scaled, h_scaled),
                        pos=pos
                    )
                    title_label = Label(
                        text='Last Command',
                        size_hint_y=0.3,
                        font_size='14sp',
                        color=(0, 0, 0, 1)
                    )
                    self.last_cmd_label = Label(
                        text='--',
                        size_hint_y=0.7,
                        font_size='14sp',
                        color=(0, 0.5, 0, 1)
                    )
                    
                    cmd_box.add_widget(title_label)
                    cmd_box.add_widget(self.last_cmd_label)
                    self.add_widget(cmd_box)
                    self.widgets['command_display'] = cmd_box
                    continue

                if name == 'device_display':
                    device_box = BoxLayout(
                        orientation='vertical',
                        size_hint=(None, None),
                        size=(w_scaled, h_scaled),
                        pos=pos
                    )
                    device_title = Label(
                        text='Device',
                        size_hint_y=0.3,
                        font_size='14sp',
                        color=(0, 0, 0, 1)
                    )
                    self.device_name_label = Label(
                        text='Not Connected',
                        size_hint_y=0.7,
                        font_size='14sp',
                        color=(0.2, 0.2, 0.8, 1)
                    )
                    
                    device_box.add_widget(device_title)
                    device_box.add_widget(self.device_name_label)
                    self.add_widget(device_box)
                    self.widgets['device_display'] = device_box
                    
                    self.bind(connected_device=lambda inst, val: setattr(self.device_name_label, 'text', val))
                    continue

                if name in ('left', 'right', 'hazard'):
                    cmd_map = {
                        'left': 'LTL', 'right': 'RTL', 'hazard': 'ALL'
                    }
                    cmd = cmd_map.get(name, name.upper())
                    btn = ImageButton(normal_source=asset(src))
                    btn.controller = self
                    btn.command = cmd
                    btn.size_hint = (None, None)
                    btn.size = (w_scaled, h_scaled)
                    btn.pos = pos
                    btn.bind(on_press=self._on_turn_signal_pressed)
                    self.add_widget(btn)
                    self.widgets[name] = btn
                    continue

                if name in ('light', 'led', 'rgb', 'start'):
                    cmd_map = {
                        'light': 'LIT', 'led': 'LED', 'rgb': 'RGB', 
                        'start': 'STA'
                    }
                    cmd = cmd_map.get(name, name.upper())
                    btn = ImageButton(normal_source=asset(src))
                    btn.controller = self
                    btn.command = cmd
                    btn.size_hint = (None, None)
                    btn.size = (w_scaled, h_scaled)
                    btn.pos = pos
                    btn.bind(on_press=self._on_toggle_control)
                    self.add_widget(btn)
                    self.widgets[name] = btn
                    continue

                if name == 'horn':
                    btn = MomentaryImageButton(
                        normal_source=asset(src),
                        press_command='HOR',
                        release_command='HOF'
                    )
                    btn.controller = self
                    btn.size_hint = (None, None)
                    btn.size = (w_scaled, h_scaled)
                    btn.pos = pos
                    self.add_widget(btn)
                    self.widgets[name] = btn
                    continue

                if name == 'lightHorn':
                    btn = MomentaryImageButton(
                        normal_source=asset(src),
                        press_command='LHO',
                        release_command='LHO'
                    )
                    btn.controller = self
                    btn.size_hint = (None, None)
                    btn.size = (w_scaled, h_scaled)
                    btn.pos = pos
                    self.add_widget(btn)
                    self.widgets[name] = btn
                    continue

                if src:
                    img_path = asset(src)
                    img = Image(
                        source=img_path,
                        size_hint=(None, None),
                        size=(w_scaled, h_scaled),
                        pos=pos,
                        allow_stretch=True,
                        keep_ratio=False
                    )
                    self.add_widget(img)
                    self.widgets[name] = img

            except Exception as e:
                print(f"Error placing {name}: {e}")

        cmd_log_width = max(180, win_w * 0.18)
        cmd_log_height = max(35, win_h * 0.045)
        self.command_log.pos = (win_w - cmd_log_width - 10, 10 + safe_area_bottom)
        self.command_log.size = (cmd_log_width, cmd_log_height)
        
        Clock.schedule_interval(self.check_connection_status, 2.0)
        self._was_connected = False
        
        self._ui_built = True
        print("UI build completed successfully")
        
        self.update_connection_status()

    def check_connection_status(self, dt):
        if self._in_connection_menu:
            return
        
        if hasattr(self, 'connection_manager') and self.connection_manager:
            was_connected = getattr(self, '_was_connected', False)
            is_connected = self.connection_manager.connected
            
            if was_connected and not is_connected:
                self.play_disconnection_sound_and_vibrate()
                self.connection_status = "Disconnected"
                self.connected_device = "Not Connected"
            
            self._was_connected = is_connected

    def send_command(self, command):
        if self.connection_manager:
            ok = self.connection_manager.send(command)
        else:
            ok = False
        
        self.command_log.update_command(command)
        
        if hasattr(self, 'last_cmd_label'):
            self.last_cmd_label.text = command
            
        return ok

    def _on_gear_pressed(self, instance):
        for key in ('n', 'r', 'd'):
            w = self.widgets.get(key)
            if isinstance(w, ImageButton) and w is not instance:
                w.is_active = False
                w.color = w.normal_color
                
        instance.is_active = True
        instance.color = instance.active_color
        self.current_gear = instance.command
        self.send_command(instance.command)

    def _on_turn_signal_pressed(self, instance):
        turn_signal_buttons = ['left', 'right', 'hazard']
        
        if instance.is_active:
            instance.is_active = False
            instance.color = instance.normal_color
            self.current_turn_signal = None
            self.send_command(instance.command)
        else:
            for signal_name in turn_signal_buttons:
                btn = self.widgets.get(signal_name)
                if btn and isinstance(btn, ImageButton) and btn is not instance:
                    btn.is_active = False
                    btn.color = btn.normal_color
            
            instance.is_active = True
            instance.color = instance.active_color
            self.current_turn_signal = instance.command
            self.send_command(instance.command)

    def _on_toggle_control(self, instance):
        instance.toggle()
        self.send_command(instance.command)

    def on_accelerometer_toggle(self, instance):
        if self._accelerometer_button_cooldown:
            return
            
        self._accelerometer_button_cooldown = True
        Clock.schedule_once(lambda dt: setattr(self, '_accelerometer_button_cooldown', False), 1.5)
        
        def safe_toggle(dt):
            try:
                if not self.accelerometer_mode:
                    if self.accelerometer_manager:
                        self.accelerometer_manager.set_callback(self.update_steering_from_accelerometer)
                    
                    success_start = self.accelerometer_manager.start()
                    
                    if success_start:
                        self.accelerometer_mode = True
                        instance.is_active = True
                        instance.color = instance.active_color
                        self.send_command('ACC1')
                        print("Accelerometer enabled")
                    else:
                        self.accelerometer_mode = False
                        instance.is_active = False
                        instance.color = instance.normal_color
                        print("Failed to start accelerometer")
                    
                else:
                    if self.accelerometer_manager:
                        self.send_command('ACC0')
                        
                        success = self.accelerometer_manager.stop()
                    
                        if success:
                            self.accelerometer_mode = False
                            instance.is_active = False
                            instance.color = instance.normal_color
                            
                            if hasattr(self, 'widgets') and 'steer' in self.widgets:
                                self.widgets['steer'].angle = 0
                            
                            Clock.schedule_once(lambda dt: self.send_command("S50"), 0.3)
                            print("Accelerometer disabled")
                        else:
                            self.accelerometer_mode = False
                            instance.is_active = False
                            instance.color = instance.normal_color
                            Clock.schedule_once(lambda dt: self.send_command("S50"), 0.3)
                            print("Accelerometer stop had issues")
                        
            except Exception as e:
                print(f"Accelerometer toggle error: {e}")
                self.accelerometer_mode = False
                instance.is_active = False
                instance.color = instance.normal_color
                Clock.schedule_once(lambda dt: self.send_command("S50"), 0.3)
        
        Clock.schedule_once(safe_toggle, 0.1)

    def update_steering_from_accelerometer(self, angle):
        if self.accelerometer_mode:
            self._update_steer_angle(angle)

    def _update_steer_angle(self, angle):
        w = self.widgets.get('steer')
        if w:
            w.angle = angle
            
        if angle >= 0:
            value = 50 + int((angle / 90) * 50)
            value = min(100, value)
        else:
            value = 50 + int((angle / 90) * 50)
            value = max(0, value)
            
        self.send_command(f"S{value:02d}")

    def show_connection_message(self, message, msg_type):
        try:
            content = BoxLayout(orientation='vertical', spacing=15, padding=25)
            
            color = (0, 0.7, 0, 1) if msg_type == "success" else (1, 0, 0, 1) if msg_type == "error" else (1, 0.5, 0, 1)
            
            message_label = Label(
                text=message,
                text_size=(350, None),
                halign='center',
                valign='middle',
                font_size='16sp',
                color=color
            )
            message_label.bind(size=message_label.setter('text_size'))
            content.add_widget(message_label)
            
            close_btn = Button(
                text='Close',
                size_hint=(0.6, 0.9),
                pos_hint={'center_x': 0.5},
                background_color=color,
                color=(1, 1, 1, 1),
                font_size='16sp'
            )
            
            popup = Popup(
                title='Connection Status',
                content=content,
                size_hint=(0.75, 0.4),
                auto_dismiss=False
            )
            
            close_btn.bind(on_press=popup.dismiss)
            content.add_widget(close_btn)
            
            popup.open()
        except Exception as e:
            print(f"Error showing connection message: {e}")

    def safe_open_settings(self, dt=None):
        if self._menu_opening:
            return
            
        if not self._ui_built:
            self.show_connection_message("Please wait, UI is loading...", "info")
            return
            
        if hasattr(self, 'accelerometer_manager') and self.accelerometer_manager:
            if self.accelerometer_manager._is_stopping:
                self.show_connection_message("Please wait for accelerometer to stop", "warning")
                return
        
        self._menu_opening = True
        
        def actually_open_settings(dt):
            try:
                if (hasattr(self, 'accelerometer_manager') and 
                    self.accelerometer_manager and 
                    self.accelerometer_manager._is_stopping):
                    self.show_connection_message("Accelerometer is busy, please try again", "warning")
                    self._menu_opening = False
                    return
                
                self.show_settings_menu()
            except Exception as e:
                print(f"Error in safe_open_settings: {e}")
                self.show_connection_message(f"Settings error: {str(e)}", "error")
            finally:
                self._menu_opening = False
        
        Clock.schedule_once(actually_open_settings, 0.3)

    def safe_open_connection_menu(self, dt=None):
        if self._menu_opening:
            return
            
        if not self._ui_built:
            self.show_connection_message("Please wait, UI is loading...", "info")
            return
            
        if hasattr(self, 'accelerometer_manager') and self.accelerometer_manager:
            if self.accelerometer_manager._is_stopping:
                self.show_connection_message("Please wait for accelerometer to stop", "warning")
                return
        
        self._menu_opening = True
        
        def actually_open_connection_menu(dt):
            try:
                if (hasattr(self, 'accelerometer_manager') and 
                    self.accelerometer_manager and 
                    self.accelerometer_manager._is_stopping):
                    self.show_connection_message("Accelerometer is busy, please try again", "warning")
                    self._menu_opening = False
                    return
                
                self.show_connection_manager()
            except Exception as e:
                print(f"Error in safe_open_connection_menu: {e}")
                self.show_connection_message(f"Connection menu error: {str(e)}", "error")
            finally:
                self._menu_opening = False
        
        Clock.schedule_once(actually_open_connection_menu, 0.3)

    def on_scan_results(self, devices):
        try:
            self._scan_in_progress = False
            Clock.schedule_once(lambda dt: self._update_device_list(devices))
        except Exception as e:
            print(f"Error in on_scan_results: {e}")

    def _update_device_list(self, devices):
        try:
            if not hasattr(self, 'device_list'):
                return
            
            self.device_list.clear_widgets()
            
            for child in list(self.device_list.children):
                if hasattr(child, 'unbind'):
                    child.unbind()
            
            if not devices or devices == "__DISCOVERY_FINISHED__":
                self.device_list.add_widget(Label(
                    text="No devices found. Click 'Scan Again'", 
                    size_hint_y=None, 
                    height=100, 
                    halign='center',
                    font_size='16sp',
                    color=(0.5, 0.5, 0.5, 1)
                ))
                return
            
            for dev in devices:
                if isinstance(dev, str) and any(keyword in dev.lower() for keyword in 
                    ['error', 'permission', 'missing', 'required', 'no device']):
                    self.device_list.add_widget(Label(
                        text=dev, 
                        size_hint_y=None, 
                        height=70,
                        halign='center',
                        font_size='14sp',
                        color=(1, 0, 0, 1) if 'error' in dev.lower() else (1, 0.5, 0, 1)
                    ))
                    continue
                
                btn = Button(
                    text=str(dev), 
                    size_hint_y=None, 
                    height=70,
                    halign='left', 
                    valign='middle',
                    text_size=(400, None),
                    font_size='14sp',
                    background_color=(0.9, 0.9, 1, 1) if 'car' in dev.lower() or 'RC' in dev.upper() else (0.95, 0.95, 0.95, 1)
                )
                
                btn.device_info = dev
                
                def make_callback(info):
                    return lambda x: self._on_device_selected(info)
                
                btn.bind(on_press=make_callback(dev))
                
                self.device_list.add_widget(btn)
                    
        except Exception as e:
            print(f"Error in _update_device_list: {e}")

    def _on_device_selected(self, device_info):
        try:
            if hasattr(self, 'conn_popup'):
                self.conn_popup.dismiss()
                self._in_connection_menu = False
            
            self.connection_status = f"Connecting via BLE..."
            
            success = self.connection_manager.connect(device_info)
            
            if success:
                self.connection_status = "Connected (BLE)"
                self.connected_device = f"Connected: {self.connection_manager.device_name}"
                
                self.play_connection_sound_and_vibrate()
                self.show_connection_message(
                    "Connected! Discovering services...", 
                    "info"
                )
            else:
                self.connection_status = "Connection Failed"
                self.connected_device = "Not Connected"
                self.show_connection_message(
                    "Connection failed via BLE!", 
                    "error"
                )
                
        except Exception as e:
            print(f"Error in device selection: {e}")
            self.show_connection_message(f"Connection error: {str(e)}", "error")

    def disconnect_device(self):
        if self.connection_manager.connected:
            self.play_disconnection_sound_and_vibrate()
            
            self.connection_manager.disconnect()
            
            self.connection_status = "Disconnected"
            self.connected_device = "Not Connected"
            self.battery_level = "85%"

    def show_connection_manager(self):
        try:
            self._in_connection_menu = True
            
            content = BoxLayout(orientation='vertical', spacing=10, padding=10)
            
            self.conn_title = Label(
                text='BLE Connection', 
                size_hint_y=0.06, 
                font_size='18sp',
                bold=True,
                color=(0.2, 0.4, 0.8, 1)
            )
            content.add_widget(self.conn_title)
            
            # نمایش وضعیت بلوتوث و لوکیشن داخل منو (حفظ شده)
            system_layout = BoxLayout(orientation='vertical', size_hint_y=0.25, spacing=5)
            
            bluetooth_layout = BoxLayout(orientation='horizontal', size_hint_y=0.5, spacing=10)
            self.bluetooth_status_label = Label(
                text='',
                size_hint_x=0.5,
                font_size='14sp',
                halign='left'
            )
            self.bluetooth_button = Button(
                text='Enable Bluetooth',
                size_hint_x=0.5,
                font_size='14sp',
                background_color=(0.2, 0.6, 0.9, 1),
                color=(1, 1, 1, 1)
            )
            self.bluetooth_button.bind(on_press=lambda x: AndroidStateHelper.open_bluetooth_settings())
            bluetooth_layout.add_widget(self.bluetooth_status_label)
            bluetooth_layout.add_widget(self.bluetooth_button)
            system_layout.add_widget(bluetooth_layout)
            
            location_layout = BoxLayout(orientation='horizontal', size_hint_y=0.5, spacing=10)
            self.location_status_label = Label(
                text='',
                size_hint_x=0.5,
                font_size='14sp',
                halign='left'
            )
            self.location_button = Button(
                text='Enable Location',
                size_hint_x=0.5,
                font_size='14sp',
                background_color=(0.2, 0.8, 0.4, 1),
                color=(1, 1, 1, 1)
            )
            self.location_button.bind(on_press=lambda x: AndroidStateHelper.open_location_settings())
            location_layout.add_widget(self.location_status_label)
            location_layout.add_widget(self.location_button)
            system_layout.add_widget(location_layout)
            
            content.add_widget(system_layout)
            
            self.dynamic_content = BoxLayout(orientation='vertical', size_hint_y=0.54)
            content.add_widget(self.dynamic_content)
            
            scan_again_container = BoxLayout(
                orientation='horizontal',
                size_hint_y=0.18,
                spacing=10,
                padding=(0, 5, 0, 5)
            )
            
            self.scan_again_btn = Button(
                text='Scan Again',
                size_hint_x=1,
                font_size='14sp',
                background_color=(0.2, 0.6, 0.9, 1),
                color=(1, 1, 1, 1)
            )
            
            def on_scan_again(instance):
                if self._scan_in_progress:
                    return
                
                if hasattr(self, 'device_list'):
                    self.device_list.clear_widgets()
                
                loading_label = Label(
                    text='Scanning for BLE devices...', 
                    size_hint_y=None, 
                    height=80,
                    font_size='14sp',
                    color=(0.2, 0.5, 0.8, 1)
                )
                
                if hasattr(self, 'device_list'):
                    self.device_list.add_widget(loading_label)
                
                self.scan_again_btn.disabled = True
                
                def run_scan():
                    try:
                        self.connection_manager.scan(self.on_scan_results)
                        Clock.schedule_once(lambda dt: self._enable_scan_button(), 15)
                    except Exception as e:
                        print(f"Scan again error: {e}")
                        self._update_device_list([f"Scan error: {str(e)}"])
                        self.scan_again_btn.disabled = False
                
                Clock.schedule_once(lambda dt: threading.Thread(target=run_scan, daemon=True).start(), 0.1)
            
            self.scan_again_btn.bind(on_press=on_scan_again)
            scan_again_container.add_widget(self.scan_again_btn)
            content.add_widget(scan_again_container)
            
            bottom_layout = BoxLayout(orientation='vertical', size_hint_y=0.17, spacing=5)
            
            row_btns = BoxLayout(size_hint_y=0.5, spacing=10)
            
            disconnect_btn = Button(
                text='Disconnect',
                background_color=(0.9, 0.3, 0.3, 1),
                font_size='14sp',
                color=(1, 1, 1, 1)
            )
            
            def safe_disconnect(instance):
                if self.connection_manager.connected:
                    self.disconnect_device()
                    self.show_connection_message("Device disconnected", "info")
                else:
                    self.show_connection_message("No device connected", "warning")
            
            disconnect_btn.bind(on_press=safe_disconnect)
            
            close_btn = Button(
                text='Close',
                font_size='14sp',
                background_color=(0.6, 0.6, 0.6, 1),
                color=(1, 1, 1, 1)
            )
            
            row_btns.add_widget(disconnect_btn)
            row_btns.add_widget(close_btn)
            bottom_layout.add_widget(row_btns)
            
            content.add_widget(bottom_layout)

            self.conn_popup = Popup(
                title='BLE Connection Manager', 
                content=content, 
                size_hint=(0.95, 0.9),
                auto_dismiss=False,
                title_size='18sp'
            )
            
            def close_popup(instance):
                self.conn_popup.dismiss()
                self._in_connection_menu = False
                Clock.unschedule(self._update_system_status)
            
            close_btn.bind(on_press=close_popup)
            self.conn_popup.open()
            
            Clock.schedule_interval(self._update_system_status, 1.0)
            
            self._check_and_scan()
            
        except Exception as e:
            print(f"Error showing connection manager: {e}")
            self._in_connection_menu = False

    def _update_system_status(self, dt):
        if not hasattr(self, 'conn_popup') or not self.conn_popup:
            return Clock.unschedule(self._update_system_status)
        
        try:
            bluetooth_enabled = AndroidStateHelper.is_bluetooth_enabled() if HAS_ANDROID else True
            
            if bluetooth_enabled:
                self.bluetooth_status_label.text = 'Bluetooth: ON'
                self.bluetooth_status_label.color = (0, 0.8, 0, 1)
                self.bluetooth_button.opacity = 0
                self.bluetooth_button.disabled = True
            else:
                self.bluetooth_status_label.text = 'Bluetooth: OFF'
                self.bluetooth_status_label.color = (1, 0, 0, 1)
                self.bluetooth_button.opacity = 1
                self.bluetooth_button.disabled = False
            
            location_enabled = AndroidStateHelper.is_location_enabled() if HAS_ANDROID else True
            
            if location_enabled:
                self.location_status_label.text = 'Location: ON'
                self.location_status_label.color = (0, 0.8, 0, 1)
                self.location_button.opacity = 0
                self.location_button.disabled = True
            else:
                self.location_status_label.text = 'Location: OFF'
                self.location_status_label.color = (1, 0, 0, 1)
                self.location_button.opacity = 1
                self.location_button.disabled = False
            
            if bluetooth_enabled and location_enabled:
                if not hasattr(self, '_scanned') or not self._scanned:
                    self._check_and_scan()
                    
        except Exception as e:
            print(f"Error updating system status: {e}")

    def _check_and_scan(self):
        if not HAS_ANDROID:
            self._start_scanning()
            return
        
        current_time = time.time()
        if current_time - self._last_scan_time < self.SCAN_COOLDOWN:
            return
        
        bluetooth_enabled = AndroidStateHelper.is_bluetooth_enabled()
        location_enabled = AndroidStateHelper.is_location_enabled()
        
        if bluetooth_enabled and location_enabled and not self._scan_in_progress:
            self._start_scanning()

    def _start_scanning(self):
        if self._scan_in_progress:
            return
            
        self._scan_in_progress = True
        self._scanned = True
        self._last_scan_time = time.time()
        
        if hasattr(self, 'dynamic_content'):
            self.dynamic_content.clear_widgets()
            gc.collect()
        
        self.device_list = BoxLayout(orientation='vertical', size_hint_y=None, spacing=5)
        self.device_list.bind(minimum_height=self.device_list.setter('height'))
        
        scroll = ScrollView(size_hint=(1, 1))
        scroll.add_widget(self.device_list)
        self.dynamic_content.add_widget(scroll)
        
        loading_label = Label(
            text='Scanning for BLE devices...', 
            size_hint_y=None, 
            height=80,
            font_size='14sp',
            color=(0.2, 0.5, 0.8, 1)
        )
        self.device_list.add_widget(loading_label)
        
        def run_scan():
            try:
                self.connection_manager.scan(self.on_scan_results)
            except Exception as e:
                print(f"Scan error: {e}")
                Clock.schedule_once(
                    lambda dt: self._update_device_list([f"Scan error: {str(e)}"]), 
                    0
                )
            finally:
                Clock.schedule_once(lambda dt: self._reset_scan_flag(), 15)
        
        Clock.schedule_once(lambda dt: threading.Thread(target=run_scan, daemon=True).start(), 0.1)

    def _reset_scan_flag(self):
        self._scan_in_progress = False
        if hasattr(self, 'scan_again_btn'):
            self.scan_again_btn.disabled = False

    def _enable_scan_button(self):
        if hasattr(self, 'scan_again_btn'):
            self.scan_again_btn.disabled = False

    def show_settings_menu(self):
        if not self._ui_built:
            self.show_connection_message("Please wait, UI is loading...", "info")
            return
            
        try:
            current_sensitivity = self.accelerometer_manager.sensitivity if self.accelerometer_manager else 1.0
            vibration_enabled = self.vibration_manager.enabled if self.vibration_manager else True
            
            content = BoxLayout(orientation='vertical', spacing=12, padding=15)
            content.add_widget(Label(text='Settings', size_hint_y=0.1, font_size='20sp', bold=True))
            
            main_layout = BoxLayout(orientation='vertical', spacing=15, size_hint_y=0.8)
            
            vibration_toggle_layout = BoxLayout(orientation='horizontal', size_hint_y=0.2, spacing=10)
            vibration_toggle_label = Label(
                text='Vibration Enabled:', 
                size_hint_x=0.6, 
                font_size='16sp'
            )
            vibration_toggle = ToggleButton(
                text='ON' if vibration_enabled else 'OFF',
                state='down' if vibration_enabled else 'normal',
                size_hint_x=0.4,
                background_color=(0.2, 0.8, 0.2, 1) if vibration_enabled else (0.8, 0.2, 0.2, 1)
            )
            
            def on_vibration_toggle(instance):
                enabled = instance.state == 'down'
                instance.text = 'ON' if enabled else 'OFF'
                instance.background_color = (0.2, 0.8, 0.2, 1) if enabled else (0.8, 0.2, 0.2, 1)
                if self.vibration_manager:
                    self.vibration_manager.enabled = enabled
                set_setting('vibration_enabled', enabled)
            
            vibration_toggle.bind(on_press=on_vibration_toggle)
            vibration_toggle_layout.add_widget(vibration_toggle_label)
            vibration_toggle_layout.add_widget(vibration_toggle)
            main_layout.add_widget(vibration_toggle_layout)
            
            sens_layout = BoxLayout(orientation='vertical', size_hint_y=0.3, spacing=5)
            sens_label = Label(
                text=f'Accelerometer Sensitivity: {current_sensitivity:.1f}', 
                size_hint_y=0.3, 
                font_size='16sp'
            )
            sens_layout.add_widget(sens_label)
            
            slider = Slider(
                min=0.5,
                max=2.5,
                value=current_sensitivity,
                size_hint_y=0.7
            )
            
            def on_sensitivity_change(instance, value):
                if self.accelerometer_manager:
                    self.accelerometer_manager.set_sensitivity(value)
                sens_label.text = f'Accelerometer Sensitivity: {value:.1f}'
                set_setting('sensitivity', value)
                
            slider.bind(value=on_sensitivity_change)
            sens_layout.add_widget(slider)
            main_layout.add_widget(sens_layout)
            
            content.add_widget(main_layout)
            
            btns = BoxLayout(size_hint_y=0.4, spacing=15, padding=(10, 0))
            
            close_btn = Button(
                text='Close', 
                size_hint_x=1,
                font_size='16sp',
                background_color=(0.2, 0.6, 0.9, 1)
            )
            
            popup = Popup(
                title='Settings', 
                content=content, 
                size_hint=(0.8, 0.5),
                title_size='18sp'
            )
            close_btn.bind(on_press=lambda x: popup.dismiss())
            
            btns.add_widget(close_btn)
            content.add_widget(btns)
            
            popup.open()
        except Exception as e:
            print(f"Error in show_settings_menu: {e}")
            self.show_connection_message(f"Settings error: {str(e)}", "error")

    def set_handedness(self, handedness):
        return True
    
    def _rebuild_ui(self):
        try:
            if hasattr(self, 'widgets'):
                for widget in self.widgets.values():
                    if widget and widget in self.children:
                        self.remove_widget(widget)
            
            if hasattr(self, 'command_log') and self.command_log in self.children:
                self.remove_widget(self.command_log)
            
            self.widgets = {}
            
            self.command_log = CommandLogBox(pos_hint={'x': 0, 'y': 0})
            self.add_widget(self.command_log)
            
            self._ui_built = False
            Clock.schedule_once(self._build_ui, 0.1)
            
        except Exception as e:
            print(f"Error rebuilding UI: {e}")

    def cleanup(self):
        print("Cleaning up resources...")
        
        if hasattr(self, 'accelerometer_manager') and self.accelerometer_manager:
            self.accelerometer_manager.cleanup()
        
        if hasattr(self, 'connection_manager') and self.connection_manager:
            self.connection_manager.cleanup()
        
        if hasattr(self, 'vibration_manager') and self.vibration_manager:
            self.vibration_manager.cleanup()
        
        if hasattr(self, 'lifecycle_manager') and self.lifecycle_manager:
            self.lifecycle_manager.cleanup()
        
        sound_attrs = ['connected_sound', 'disconnected_sound', 'signal_lost_sound']
        for attr in sound_attrs:
            if hasattr(self, attr):
                sound = getattr(self, attr)
                if sound:
                    try:
                        sound.unload()
                    except:
                        pass
        
        ThreadManager.cleanup_threads()
        JavaObjectManager.cleanup()
        
        print("All resources cleaned up")


# ==================== MAIN APPLICATION CLASS ====================
class BluetoothRC(App):
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.settings_manager = SettingsManager()
        sys.excepthook = global_exception_hook
        self._is_running = True
        self._on_start_called = False
        self._permissions_granted = False
        self._cleanup_done = False
        
        import atexit
        atexit.register(self._cleanup_resources)

    def _cleanup_resources(self):
        try:
            if self._cleanup_done:
                return
                
            self._cleanup_done = True
            
            if hasattr(self, 'root') and self.root:
                self.root.cleanup()
            
            ThreadManager.cleanup_threads()
            JavaObjectManager.cleanup()
            gc.collect()
            
        except Exception as e:
            print(f"Cleanup error: {e}")

    def build(self):
        self.title = "BLE RC Car Controller"
        
        test_files = ["right.png", "steer.png", "ble.png", "pedal.png", "connected.mp3"]
        for test_file in test_files:
            path = asset(test_file)
            if path and os.path.exists(path):
                print(f"Asset found: {test_file} -> {path}")
            else:
                print(f"Asset not found: {test_file}")
        
        Window.fullscreen = 'auto'
        Window.borderless = True
        
        return CombinedAppRoot()

    def on_start(self):
        if self._on_start_called:
            return
            
        self._on_start_called = True
        print("App on_start() called - Requesting BLE permissions...")
        
        if HAS_ANDROID:
            request_ble_permissions(self.on_permissions_result)
        else:
            print("Desktop mode - no permissions required")
            self._permissions_granted = True
            if hasattr(self, 'root') and self.root:
                self.root._permissions_checked = True

    def on_permissions_result(self, granted):
        if granted:
            print("Permissions granted - initializing BLE")
            self._permissions_granted = True
            
            if hasattr(self, 'root') and self.root:
                self.root._permissions_checked = True
                
            if HAS_ANDROID:
                Clock.schedule_once(lambda dt: self.check_system_status(), 0.5)
        else:
            print("Permissions denied - BLE features disabled")
            # هشدار ابتدایی مجوز حذف شد - بدون نمایش پاپ‌آپ

    def check_system_status(self):
        if not HAS_ANDROID:
            return
        
        try:
            bluetooth_enabled = AndroidStateHelper.is_bluetooth_enabled()
            if not bluetooth_enabled:
                print("Bluetooth is OFF")  # فقط لاگ، بدون نمایش هشدار
            
            location_enabled = AndroidStateHelper.is_location_enabled()
            if not location_enabled:
                print("Location is OFF")  # فقط لاگ، بدون نمایش هشدار
        except Exception as e:
            print(f"Error checking system status: {e}")

    def show_permission_warning(self):
        # هشدار ابتدایی مجوز حذف شد
        pass

    def show_bluetooth_warning(self):
        # هشدار بلوتوث ابتدایی حذف شد
        pass

    def show_location_warning(self):
        # هشدار لوکیشن ابتدایی حذف شد
        pass

    def on_stop(self):
        print("App on_stop() called - cleaning up...")
        self._is_running = False
        
        try:
            if hasattr(self, 'root') and self.root:
                if hasattr(self.root, 'signal_check_event') and self.root.signal_check_event:
                    Clock.unschedule(self.root.signal_check_event)
                
                try:
                    self.root.cleanup()
                except Exception as e:
                    print(f"Root cleanup error: {e}")
            
        except Exception as e:
            print(f"Error during app stop: {e}")
        
        try:
            ThreadManager.cleanup_threads()
            JavaObjectManager.cleanup()
            gc.collect()
        except Exception as e:
            print(f"Final cleanup error: {e}")
        
        print("App stopped cleanly")
        return True

# ==================== MAIN ENTRY POINT ====================
if __name__ == '__main__':
    try:
        import signal
        
        def signal_handler(sig, frame):
            print("\nApplication interrupted by user (Ctrl+C)")
            try:
                ThreadManager.cleanup_threads()
                JavaObjectManager.cleanup()
            except Exception as e:
                print(f"Cleanup error (non-critical): {e}")
            finally:
                import os
                os._exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        
        sys.excepthook = global_exception_hook
        
        if platform == "android":
            print("Android detected - running on mobile device")
            print(f"Android SDK Version: {SDK_INT}")
        
        print("Starting BLE RC Car Controller...")
        try:
            app = BluetoothRC()
            app.run()
        except KeyboardInterrupt:
            print("\nApp stopped by user")
        except Exception as app_error:
            print(f"Application runtime error: {app_error}")
            traceback.print_exc()
        finally:
            print("Final cleanup...")
            try:
                ThreadManager.cleanup_threads()
                JavaObjectManager.cleanup()
                gc.collect()
            except Exception as e:
                print(f"Final cleanup error: {e}")
            
    except KeyboardInterrupt:
        print("\nApp stopped by user")
    except Exception as e:
        print(f"Application failed to start: {e}")
        traceback.print_exc()
    finally:
        print("Goodbye!")
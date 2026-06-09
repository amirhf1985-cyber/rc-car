import threading
import time
import traceback
import os

from kivy.storage.jsonstore import JsonStore
from kivy.app import App


class SettingsManager:
    """
    Professional settings manager with robust error handling.
    Thread-safe and Android-friendly version.
    """

    def __init__(self):
        self._lock = threading.RLock()

        app = App.get_running_app()

        if app and hasattr(app, "user_data_dir"):
            settings_path = os.path.join(
                app.user_data_dir,
                "rc_car_settings.json"
            )
        else:
            settings_path = "rc_car_settings.json"

        self.store = JsonStore(settings_path)

        self._defaults = {
            'sensitivity': 1.0,
            'accelerometer_mode': False,
            'steering_sensitivity': 1.0,
            'battery_warning_level': 20,
            'last_connected_device': '',
            'connection_type': 'ble',
            'vibration_enabled': True,
            'ui_scale': 1.0,
            'theme': 'light',
            'auto_reconnect': True,
            'keep_screen_on': True,
            'foreground_service_enabled': True,
            'wake_lock_enabled': True,

            # RC Car specific settings
            'max_speed': 100,
            'steering_deadzone': 0.05,
            'throttle_deadzone': 0.05,
            'last_ble_address': '',
            'failsafe_timeout': 2.0,
        }

        self._initialize_defaults()

    def _initialize_defaults(self):
        """Initialize default settings if they don't exist."""
        with self._lock:
            for key, value in self._defaults.items():
                if not self.store.exists(key):
                    self._set_with_timestamp(key, value)

    def _sync_store(self):
        """Force write to disk if supported."""
        try:
            if hasattr(self.store, "store_sync"):
                self.store.store_sync()
        except Exception:
            pass

    def _set_with_timestamp(self, key, value):
        """Save value with timestamp."""
        try:
            data = {
                "value": value,
                "timestamp": time.time()
            }

            self.store.put(key, **data)
            self._sync_store()

            print(f"✅ Setting saved: {key} = {value}")
            return True

        except Exception as e:
            print(f"❌ Settings write error for {key}: {e}")
            traceback.print_exc()
            return False

    def get(self, key, default=None):
        """Get setting value safely."""
        with self._lock:
            try:
                if self.store.exists(key):
                    data = self.store.get(key)

                    if isinstance(data, dict):
                        return data.get(
                            "value",
                            self._defaults.get(key, default)
                        )

                    return data

                return self._defaults.get(key, default)

            except Exception as e:
                print(f"❌ Settings read error for {key}: {e}")
                traceback.print_exc()
                return self._defaults.get(key, default)

    def get_float(self, key, default=0.0):
        try:
            value = self.get(key, default)
            return float(value)
        except (TypeError, ValueError):
            return float(default)

    def get_bool(self, key, default=False):
        try:
            value = self.get(key, default)

            if isinstance(value, bool):
                return value

            if isinstance(value, str):
                return value.lower() in (
                    "true",
                    "1",
                    "yes",
                    "on"
                )

            return bool(value)

        except Exception:
            return bool(default)

    def get_string(self, key, default=''):
        try:
            value = self.get(key, default)
            return str(value)
        except Exception:
            return str(default)

    def set(self, key, value):
        """Save setting only if changed."""
        with self._lock:
            try:
                current = self.get(key, None)

                if current == value:
                    return True

                return self._set_with_timestamp(key, value)

            except Exception as e:
                print(f"❌ Error saving setting {key}: {e}")
                return False

    def get_all_settings(self):
        """Return all settings."""
        with self._lock:
            settings = {}

            try:
                for key in self.store.keys():
                    settings[key] = self.get(key)

                return settings

            except Exception as e:
                print(f"❌ Error loading settings: {e}")
                return self._defaults.copy()

    def reset_to_defaults(self):
        """Reset all settings to defaults."""
        with self._lock:
            try:
                for key, value in self._defaults.items():
                    self._set_with_timestamp(key, value)

                return True

            except Exception as e:
                print(f"❌ Error resetting settings: {e}")
                return False

    def delete_setting(self, key):
        """Delete one setting."""
        with self._lock:
            try:
                if self.store.exists(key):
                    self.store.delete(key)
                    self._sync_store()

                return True

            except Exception as e:
                print(f"❌ Error deleting {key}: {e}")
                return False

    def clear_all_settings(self):
        """Delete all settings and restore defaults."""
        with self._lock:
            try:
                keys = list(self.store.keys())

                for key in keys:
                    try:
                        self.store.delete(key)
                    except Exception:
                        pass

                self._sync_store()
                self._initialize_defaults()

                return True

            except Exception as e:
                print(f"❌ Error clearing settings: {e}")
                return False


# Helper Functions

def get_setting(key, default=None):
    try:
        app = App.get_running_app()

        if app and hasattr(app, "settings_manager"):
            return app.settings_manager.get(key, default)

        return default

    except Exception as e:
        print(f"❌ get_setting error ({key}): {e}")
        return default


def set_setting(key, value):
    try:
        app = App.get_running_app()

        if app and hasattr(app, "settings_manager"):
            return app.settings_manager.set(key, value)

        return False

    except Exception as e:
        print(f"❌ set_setting error ({key}): {e}")
        return False


def get_setting_float(key, default=0.0):
    try:
        app = App.get_running_app()

        if app and hasattr(app, "settings_manager"):
            return app.settings_manager.get_float(key, default)

        return float(default)

    except Exception:
        return float(default)


def get_setting_bool(key, default=False):
    try:
        app = App.get_running_app()

        if app and hasattr(app, "settings_manager"):
            return app.settings_manager.get_bool(key, default)

        return bool(default)

    except Exception:
        return bool(default)


def get_setting_string(key, default=''):
    try:
        app = App.get_running_app()

        if app and hasattr(app, "settings_manager"):
            return app.settings_manager.get_string(key, default)

        return str(default)

    except Exception:
        return str(default)
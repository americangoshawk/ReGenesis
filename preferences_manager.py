"""Preferences manager for ReGenesis application."""
import json
import os
from pathlib import Path


class PreferencesManager:
    """Manages application preferences stored in ~/.regenesis/preferences.json"""

    def __init__(self):
        self.prefs_dir = Path.home() / '.regenesis'
        self.prefs_file = self.prefs_dir / 'preferences.json'
        self.preferences = self._load_preferences()

    def _get_default_preferences(self):
        """Return default preferences structure."""
        return {
            "location": {
                "latitude": None,
                "longitude": None
            },
            "theme": "flatly",
            "development_mode": False
        }

    def _load_preferences(self):
        """Load preferences from file, create if doesn't exist."""
        # Create directory if it doesn't exist
        if not self.prefs_dir.exists():
            self.prefs_dir.mkdir(parents=True, exist_ok=True)

        # Load or create preferences file
        if self.prefs_file.exists():
            try:
                with open(self.prefs_file, 'r') as f:
                    prefs = json.load(f)
                # Merge with defaults to ensure all keys exist
                defaults = self._get_default_preferences()
                return self._merge_preferences(defaults, prefs)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading preferences: {e}")
                return self._get_default_preferences()
        else:
            # Create default preferences file
            defaults = self._get_default_preferences()
            self._save_preferences(defaults)
            return defaults

    def _merge_preferences(self, defaults, loaded):
        """Merge loaded preferences with defaults to ensure all keys exist."""
        result = defaults.copy()
        for key, value in loaded.items():
            if key in result:
                if isinstance(value, dict) and isinstance(result[key], dict):
                    result[key].update(value)
                else:
                    result[key] = value
        return result

    def _save_preferences(self, prefs):
        """Save preferences to file."""
        try:
            with open(self.prefs_file, 'w') as f:
                json.dump(prefs, f, indent=2)
        except IOError as e:
            print(f"Error saving preferences: {e}")

    def get(self, key, default=None):
        """Get a preference value."""
        keys = key.split('.')
        value = self.preferences
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
        return value if value is not None else default

    def set(self, key, value):
        """Set a preference value."""
        keys = key.split('.')
        prefs = self.preferences

        # Navigate to the correct nested location
        for k in keys[:-1]:
            if k not in prefs:
                prefs[k] = {}
            prefs = prefs[k]

        # Set the value
        prefs[keys[-1]] = value

        # Save to file
        self._save_preferences(self.preferences)

    def get_location(self):
        """Get location coordinates as tuple (latitude, longitude)."""
        lat = self.get('location.latitude')
        lon = self.get('location.longitude')
        return (lat, lon) if lat is not None and lon is not None else None

    def set_location(self, latitude, longitude):
        """Set location coordinates."""
        self.set('location.latitude', latitude)
        self.set('location.longitude', longitude)

    def get_theme(self):
        """Get current theme."""
        return self.get('theme', 'flatly')

    def set_theme(self, theme):
        """Set theme."""
        self.set('theme', theme)

    def is_development_mode(self):
        """Check if development mode is enabled."""
        return self.get('development_mode', False)

    def set_development_mode(self, enabled):
        """Enable or disable development mode."""
        self.set('development_mode', enabled)

import os
import json
from src.core.logger import console
from src.core.types import Settings

class SettingsManager:
    def __init__(self, setting_file_path: str = "./config/settings.json"):
        self.settings: Settings = None
        self.setting_file_path: str = setting_file_path

        self.load_settings()

    def load_settings(self):
        if os.path.isfile(self.setting_file_path):
            console.info("Loading settings configuration")
            with open(self.setting_file_path, "r") as File:
                try:
                    settings_raw_data = File.read()
                    settings_json_data = json.loads(settings_raw_data)
                    self.parse_settings_data(settings_json_data)
                except json.JSONDecodeError:
                    console.error("Error decoding the settings configuration file. Please check your configuration")
                    console.exit()
                except ValueError:
                    console.error("Invalid value found in the settings configuration file. Please check your configuration")
                    console.exit()

    def parse_settings_data(self, settings_data: dict):
        try:
            self.settings = Settings(**settings_data)
            console.info("Settings data parsed successfully")
        except Exception as e:
            console.error(f"Error parsing settings data: {e}")
            console.exit()
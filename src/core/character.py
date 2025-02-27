import os
import json
from src.core.logger import console
from src.core.types import Character

class CharacterManager:
    def __init__(self, character_file: str = "./config/character.json"):
        self.character: Character = None
        self.character_file_path: str = character_file

        self.load_character()
        
    def load_character(self):
        if os.path.isfile(self.character_file_path):
            console.info("Loading a character configuration...")
            with open(self.character_file_path, "r") as File:
                try:
                    character_raw_data = File.read()
                    character_json_data = json.loads(character_raw_data)
                    self.parse_character_data(character_json_data)
                    self.print_informative_character()
                except json.JSONDecodeError:
                    console.error("Error decoding the character configuration file. Please check your configuration")
                    console.exit()
                except ValueError:
                    console.error("Invalid value found in the character configuration file. Please check your configuration")
                    console.exit()
        else:
            console.error("Sorry, character configuration not found. Please check your configuration")
            console.exit()
    
    def parse_character_data(self, character_data: dict):
        try:
            self.character = Character(**character_data)
            console.info("Character data parsed successfully")
        except Exception as e:
            console.error(f"Error parsing character data: {e}")
            console.exit()

    def print_informative_character(self):
        if self.character is None:
            console.error("Character data is not loaded. Please load the character data first.")
            console.exit()
        console.divide()
        console.info(f"Character name: {self.character.name}")
        console.info(f"Character gender: {self.character.gender}")
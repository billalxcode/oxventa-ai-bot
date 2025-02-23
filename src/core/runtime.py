from uuid import UUID
from src.core.character import Character
from src.core.settings import Settings
from src.adapters.mongodb import MongoAdapter

class AgentRuntime:
    def __init__(
        self,
        character: Character,
        settings: Settings
    ):
        self.character: Character = character
        self.settings: Settings = settings
        self.database_adapter: MongoAdapter = None
        
    def set_database_adapter(self, adapter: MongoAdapter):
        self.database_adapter = adapter
    
    def get_setting(self, key: str):
        return self.settings.model_dump()[key]
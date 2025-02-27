from dotenv import load_dotenv
from pymongo import MongoClient
from src.core.agent import Agent
from src.core.runtime import AgentRuntime
from src.core.character import CharacterManager
from src.core.settings import SettingsManager
from src.adapters.mongodb import MongoAdapter

load_dotenv()

character_manager = CharacterManager()
settings_manager = SettingsManager()

runtime = AgentRuntime(
    character=character_manager.character,
    settings=settings_manager.settings
)

agent = Agent(runtime=runtime)
agent.init()

runtime.set_agent(agent=agent)
runtime.init()

database_client = MongoClient(uuidRepresentation="standard")
database_adapter = MongoAdapter(runtime, database_client)
database_adapter.init()

runtime.set_database_adapter(database_adapter)

database = runtime.get_setting("database.mongodb")
runtime.start()
import binascii
import threading
from uuid import UUID
from typing import Literal
from typing import Callable
from pydantic import BaseModel
from pymongo import MongoClient
from pymongo.synchronous.database import Database
from src.core.worker import WorkerThread
from src.crypto.aes import AESCipher

# Database Types
class MongoDatabase(BaseModel):
    url: str
    database: str

# Settings Types
class SettingDatabase(BaseModel):
    mongodb: MongoDatabase

class SettingTelegramClient(BaseModel):
    key: str
    is_activate: bool
    parse_mode: str
    
class SettingClient(BaseModel):
    telegram: SettingTelegramClient

class SettingAgent(BaseModel):
    name: str
    author: str
    environment: dict

class Settings(BaseModel):
    agent: SettingAgent
    character: str
    database: SettingDatabase
    client: SettingClient
    plugins: list[str]
    secret_key: str

# Character Types
class CharacterBio(BaseModel):
    role: str
    personality: list[str]
    skills: list[str]
    unique_traits: list[str]

class CharacterStyle(BaseModel):
    tone: str
    communication: str
    emphasis: str
    emotion: str
    attitude: str

class CharacterLore(BaseModel):
    background: str
    mission: str
    current_role: str

class CharacterConversation(BaseModel):
    user: str
    content: str

class CharacterConversationsGroup(BaseModel):
    conversations: list[CharacterConversation]

class Character(BaseModel):
    name: str
    gender: str
    bio: CharacterBio
    lore: CharacterLore
    style: CharacterStyle
    knowledge: dict[str, list[str]] | None
    conversations: list[CharacterConversationsGroup] | None

class ConversationMessages(BaseModel):
    content: str
    timestamp: str
    is_user: bool

class Conversations(BaseModel):
    uuid: UUID
    user_id: UUID
    messages: list[ConversationMessages]
    created_at: str
    updated_at: str

    def to_string_id(self):
        if isinstance(self.uuid, UUID):
            return str(self.uuid)
        return self.uuid

class PluginMetadata(BaseModel):
    name: str
    author: str
    version: float | str
    license: str

# Wallet Types
class Wallet(BaseModel):
    uuid: UUID
    address: str
    encrypted_private_key: str = ""
    wallet_type: Literal["evm", "solana", "other"]

    def unlock_private_key(self, encryption_key: str):
        encryption_key_bytes = binascii.unhexlify(encryption_key)
        aes = AESCipher(encryption_key_bytes)
        private_key = aes.decrypt(self.encrypted_private_key)
        return private_key
    
    def lock_private_key(self, encryption_key: str, private_key: str):
        encryption_key_bytes = binascii.unhexlify(encryption_key)
        aes = AESCipher(encryption_key_bytes)
        encrypted_private_key = aes.encrypt(private_key)

        self.encrypted_private_key = encrypted_private_key
        
        return encrypted_private_key

class Users(BaseModel):
    uuid: UUID
    fullname: str
    username: str
    wallets: list[Wallet]
    created_at: str
    updated_at: str

class MongoAdapterConversationAbstract:
    def create_conversation(self, conversation_data: Conversations): ...
    def get_conversation(self, conversation_id: UUID): ...
    def get_conversations_for_user(self, user_id: UUID): ...
    def get_first_conversation_for_user(self, user_id: UUID): ...
    def x(self, x2: str): ...
    
class MongoAdapterUserAbstract:
    def create_user(self, user_data: Users): ...
    def create_wallet(self, user_id: UUID, wallet: Wallet): ...
    def get_user(self, user_id: UUID): ...
    def get_user_wallets(self, user_id: UUID): ...
    def get_user_wallet(self, user_id: UUID, wallet_id: UUID): ...
    def get_user_wallet_address(self, user_id: UUID, wallet_address: str): ...
    
class PluginManagerAbstract:
    def __init__(self, runtime: any):
        self.runtime: AgentRuntimeAbstract = runtime
        self.plugins: list[Callable]
        self.plugins_metadata: list[PluginMetadata]
        self.cwd: str

    def load_plugins(self): ...
    def load_metadata(self, metadata_path: str): ...
    def from_path_to_module(self, plugin_path: str): ...
    def initialize_plugin(self, plugin_path: str): ...
    def call_all_plugins(self): ...
    def print_informative_plugins(self): ...

class AgentRuntimeAbstract:
    def __init__(
        self,
        character: Character,
        settings: Settings
    ):
        self.character: Character = character
        self.settings: Settings = settings
        self.database_adapter: str
        self.stop_polling: threading.Event
    
        self.worker: WorkerThread

        self.agent: AgentAbstract = None

        self.plugins: PluginManagerAbstract = None

    def init(self): ...
    def get_setting(self, key: str): ...
    def set_agent(self, agent): ...
    def set_database_adapter(self, adapter: MongoClient): ...
    def start(self): ...
    def stop(self): ...

class MongoAdapterAbstract(MongoAdapterConversationAbstract, MongoAdapterUserAbstract):
    def __init__(
        self,
        runtime: AgentRuntimeAbstract,
        client: MongoClient = None
    ):
        self.client: MongoClient = client
        self.runtime: AgentRuntimeAbstract = runtime

        self.database: Database = None
        self.is_connected: bool = False

    def init(self): ...
    def close(self): ...
    def initialize_database(self): ...
    def initialize_collections(self): ...
    def ensure_connection(self): ...
    
class AgentAbstract:
    def __init__(self, runtime: AgentRuntimeAbstract):
        self.runtime: AgentRuntimeAbstract = runtime
        self.plugins: list = []

    def init(self): ...
    def register(self): ...
    def execute(self, input: str): ...
import binascii
import threading
from uuid import UUID
from datetime import datetime
from typing import Literal
from typing import Callable
from typing import Optional
from pydantic import BaseModel
from pydantic import EmailStr
from pydantic import Field
from pymongo import MongoClient
from pymongo.synchronous.database import Database
from langchain.tools import StructuredTool
from telebot.types import Message
from eth_account import Account
from eth_account.signers.local import LocalAccount
from solders.keypair import Keypair

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

    def build_knowledge(self):
        knowledge_strings = []
        for key, values in self.knowledge.items():
            knowledge_string = f"{key}: {', '.join(values)}"
            knowledge_strings.append(knowledge_string)
        return '\n'.join(knowledge_strings)

    def build_communication_style(self):
        return f"""
🗣 Tone
{self.style.tone.capitalize()}
📡 Communication Style
{self.style.communication.capitalize()}
💡 Emphasis
{self.style.emphasis.capitalize()}
😏 Emotion
{self.style.emotion.capitalize()}
🔥 Attitude
{self.style.attitude.capitalize()}
        """
    
    def build_lore(self):
        return f"""
📍 Background
{self.lore.background.capitalize()}
🎯 Mission
{self.lore.mission.capitalize()}
🚀 Current Role
{self.lore.current_role.capitalize()}
"""
    
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
    uuid: UUID = Field(...)
    user_uuid: UUID = Field(...)
    address: str = Field(...)
    wallet_type: Literal["evm", "solana"] = Field(...)
    extra: dict = Field(default_factory=dict)

    def get_private_key(self, secret: str):
        if self.wallet_type == "solana":
            raise NotImplementedError
        account: LocalAccount = Account.decrypt(self.extra, password=secret)
        return account.key

    def fill_extra(self, private_key: str, secret: str):
        if self.wallet_type == "solana":
            raise NotImplementedError
        account: LocalAccount = Account.from_key(private_key)
        account_encrypted = account.encrypt(password=secret)
        self.extra = account_encrypted
        return self
    
class Users(BaseModel):
    uuid: UUID                      = Field(...)
    email: EmailStr                 = Field(...)
    username: str                   = Field(...)
    first_name: Optional[str]       = Field(default=None)
    last_name: Optional[str]        = Field(default=None)
    created_at: datetime            = Field(default_factory=datetime.now)
    updated_at: datetime            = Field(default_factory=datetime.now)

    @property
    def full_name(self):
        full_name = self.first_name
        if self.last_name:
            full_name += f" {self.last_name}"
        return full_name

    def before_save(self):
        self.updated_at = datetime.now()
        return self
    
class MongoAdapterConversationAbstract:
    def create_conversation(self, conversation_data: Conversations): ...
    def get_conversation(self, conversation_id: UUID): ...
    def get_conversations_for_user(self, user_id: UUID): ...
    def get_first_conversation_for_user(self, user_id: UUID): ...
    def x(self, x2: str): ...
    
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

class PluginTool:
    def __init__(self, runtime: any):
        self.runtime: AgentRuntimeAbstract
        self.name: str
        self.description: str
        self.schema: BaseModel

    def init(self): ...
    def call(self, arg: str, message: Message): ...

class ToolsManagerAbstract:
    def __init__(self, runtime: any):
        self.runtime: AgentRuntimeAbstract
        self.tools: list[PluginTool]
        self.tools_binding: list[StructuredTool]
        self.message: Message
    
    def register(self, tool: PluginTool): ...
    def build(self): ...
    def print_informative_tools(self): ...
    def update_message(self, message: Message): ...

class AgentRuntimeAbstract:
    def __init__(
        self,
        character: Character,
        settings: Settings
    ):
        self.character: Character = character
        self.settings: Settings = settings
        self.database_adapter: MongoAdapterAbstract
        self.stop_polling: threading.Event
    
        self.telegram_client
        
        self.worker: WorkerThread

        self.agent: AgentAbstract = None

        self.plugins: PluginManagerAbstract = None
        self.tools: ToolsManagerAbstract = None
        
    def init(self): ...
    def get_setting(self, key: str): ...
    def set_agent(self, agent): ...
    def set_database_adapter(self, adapter: MongoClient): ...
    def start(self): ...
    def stop(self): ...

class UserAdapterAbstract:
    def create_user(self, user_data: Users): ...
    def get_user(self, user_id: UUID): ...
    def exists_user(self, user_id: UUID): ...
    
class WalletAdapterAbstract:
    def create_wallet(self, wallet_data: Wallet): ...

class MongoAdapterAbstract(MongoAdapterConversationAbstract):
    def __init__(
        self,
        runtime: AgentRuntimeAbstract,
        client: MongoClient = None
    ):
        self.client: MongoClient = client
        self.runtime: AgentRuntimeAbstract = runtime

        self.user: UserAdapterAbstract
        self.wallet: WalletAdapterAbstract

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
    def initialize_prompt(self): ...
    def execute(self, input: str, message: Message): ...
    def start_agent(self): ...

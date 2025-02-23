import binascii
from uuid import UUID
from typing import Literal
from pydantic import BaseModel
from pymongo import MongoClient
from pymongo.synchronous.database import Database

from src.crypto.aes import AESCipher

# Database Types
class MongoDatabase(BaseModel):
    url: str
    database: str

# Settings Types
class SettingDatabase(BaseModel):
    mongodb: MongoDatabase

class Settings(BaseModel):
    character: str
    database: SettingDatabase
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

class MongoAdapterAbstract(MongoAdapterConversationAbstract, MongoAdapterUserAbstract):
    def __init__(
        self,
        settings: Settings,
        client: MongoClient
    ):
        self.client: MongoClient = client
        self.settings: Settings = settings

        self.database: Database = None
        self.is_connected: bool = False

    def init(self): ...
    def close(self): ...
    def initialize_database(self): ...
    def initialize_collections(self): ...
    def ensure_connection(self): ...
    
class AgentRuntimeAbstract:
    def __init__(
        self,
        character: Character,
        settings: Settings
    ):
        self.character: Character = character
        self.settings: Settings = settings
        self.database_adapter: str
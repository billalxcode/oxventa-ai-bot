from uuid import UUID
from pymongo import MongoClient
from datetime import datetime
from src.core.types import Settings
from src.core.types import MongoAdapterAbstract
from src.core.types import Conversations
from src.core.types import Users
from src.core.types import Wallet
from src.core.logger import console
from src.core.types import AgentRuntimeAbstract
from src.core.exceptions import InvalidID
from src.adapters.users import UserAdapter
from src.adapters.wallets import WalletAdapter

class MongoAdapter(MongoAdapterAbstract):
    def __init__(self, runtime: AgentRuntimeAbstract, client: MongoClient = None):
        super().__init__(runtime, client)
        
        self.user = UserAdapter(self)
        self.wallet = WalletAdapter(self)

    def init(self):
        if self.client is None:
            database_url = self.runtime.get_setting("database.mongodb.url")

            try:
                self.client = MongoClient(
                    database_url    
                )
                self.is_connected = True
            except Exception as e:
                console.error("Failed to connect database, please check your configuration and ensure the database is running")
                console.exit()
        if self.is_connected is True: return
        
        self.initialize_database()
        self.initialize_collections()
        self.is_connected = True
        
    def close(self):
        if self.is_connected is True:
            self.client.close()
            self.is_connected = False

    def initialize_database(self):
        default_database_name = "agents"

        database_name = self.runtime.get_setting("database.mongodb.database")
        if not database_name:
            console.warn(f"No database name found, set to `{default_database_name}`")
            database_name = default_database_name
        self.database = self.client.get_database(database_name)

    def initialize_collections(self):
        collections = [
            "memories",
            "conversations",
            "accounts",
            "wallets"
        ]
        console.info("Initialize all database collections")
        for collection in collections:
            if collection in self.database.list_collection_names():
                console.info(f"Database collection `{collection}` has been already exists")
            else:
                console.info(f"Initialize database collection `{collection}`")
                self.database.create_collection(collection)

    def ensure_connection(self):
        if self.is_connected is not True:
            self.init()
    
    # ============ Conversations Functions ============= #
    def create_conversation(self, conversation_data: Conversations):
        self.ensure_connection()
        try:
            self.database.get_collection("conversations").insert_one(
                conversation_data.model_dump()
            )
            return True
        except Exception as e:
            console.error(f"Error creating a conversation: {e}")
            return False
        
    def get_conversation(self, conversation_id: UUID):
        self.ensure_connection()
        if isinstance(conversation_id, str):
            try:
                conversation_id = UUID(conversation_id)
            except ValueError:
                raise InvalidID("Invalid conversation id")
        conversation = self.database.get_collection("conversations").find_one({
            "uuid": conversation_id
        })
        if conversation:
            return Conversations(**conversation)
        return None
    
    def get_conversations_for_user(self, user_id: UUID):
        self.ensure_connection()
        if isinstance(user_id, str):
            try:
                user_id = UUID(user_id)
            except ValueError:
                raise InvalidID("Invalid conversation id")
        conversations = self.database.get_collection("conversations").find({
            "user_id": user_id
        })
        return [Conversations(**conversation) for conversation in conversations]

    def get_first_conversation_for_user(self, user_id):
        self.ensure_connection()
        conversations = self.get_conversations_for_user(user_id=user_id)
        if len(conversations) > 0:
            return conversations[0]
        else:
            return None
        
    def get_user(self, user_id: Users):
        self.ensure_connection()
        if isinstance(user_id, str):
            try:
                user_id = UUID(user_id)
            except ValueError:
                raise InvalidID("Invalid user id")
            
        user = self.database.get_collection("users").find_one({
            'uuid': user_id
        })
        if user:
            return Users(**user)
        return None
    
    def get_user_wallets(self, user_id: UUID):
        user = self.get_user(user_id=user_id)
        return user.wallets if user else []

    def get_user_wallet(self, user_id: UUID, wallet_id: UUID):
        if isinstance(wallet_id, str):
            try:
                wallet_id = UUID(wallet_id)
            except ValueError:
                raise InvalidID("Invalid wallet id")
        wallets = self.get_user_wallets(user_id=user_id)
        wallets = [wallet_data.uuid == wallet_id for wallet_data in wallets]
        return wallets[0] if len(wallets) > 0 else None
    
    def get_user_wallet_address(self, user_id: UUID, wallet_address: str):
        wallets = self.get_user_wallets(user_id=user_id)
        wallets = [wallet_data.address == wallet_address for wallet_data in wallets]
        return wallets[0] if len(wallets) > 0 else None
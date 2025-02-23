from uuid import uuid4
from pymongo import MongoClient
from datetime import datetime
from eth_account import Account
from eth_account.signers.local import LocalAccount
from src.core.runtime import AgentRuntime
from src.core.character import CharacterManager
from src.core.settings import SettingsManager
from src.adapters.mongodb import MongoAdapter

from src.core.logger import console
from src.core.types import Users
from src.core.types import Wallet

character_manager = CharacterManager()
settings_manager = SettingsManager()

runtime = AgentRuntime(
    character=character_manager.character,
    settings=settings_manager.settings
)
database_client = MongoClient(uuidRepresentation="standard")
database_adapter = MongoAdapter(settings_manager.settings, database_client)
database_adapter.init()

runtime.set_database_adapter(database_adapter)

user_data = Users(
    uuid=uuid4(),
    fullname="Billal Fauzan",
    username="billalxcode",
    wallets=[],
    created_at=str(datetime.now()),
    updated_at=str(datetime.now())
)

secret_key = runtime.settings.secret_key
account: LocalAccount = Account.create()
wallet_data = Wallet(
    uuid=uuid4(),
    address=str(account.address),
    encrypted_private_key="",
    wallet_type="evm"
)
wallet_data.lock_private_key(secret_key, account.key.hex())
database_adapter.create_wallet("23e7d4f0-686d-4d93-b96a-9e180779bacf", wallet_data)
# console.print(user_data)
# result = database_adapter.create_user(user_data=user_data)
# console.print(result)
# result = database_adapter.create_conversation(conversation_data=conversation_data)
# console.print(result)
from uuid import UUID
from src.core.logger import console
from src.core.types import MongoAdapterAbstract
from src.core.types import WalletAdapterAbstract
from src.core.types import Wallet
from src.core.exceptions import InvalidID

class WalletAdapter(WalletAdapterAbstract):
    def __init__(self, db: MongoAdapterAbstract):
        self.db = db

    def create_wallet(self, wallet_data: Wallet):
        self.db.ensure_connection()
        
        try:
            self.db.database.get_collection("wallets").insert_one(
                wallet_data.model_dump()
            )
            return True
        except Exception as e:
            console.error(f"Error creating a user: {e}")
            return False
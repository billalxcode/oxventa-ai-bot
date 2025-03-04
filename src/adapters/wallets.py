from uuid import UUID
from src.core.logger import console
from src.core.types import MongoAdapterAbstract
from src.core.types import WalletAdapterAbstract
from src.core.types import Wallet
from src.core.types import Literal
from src.core.types import LocalAccount
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
        
    def get_wallet(self, user_id: UUID, wallet_type: Literal["evm", "solana"]):
        self.db.ensure_connection()

        if isinstance(user_id, str):
            try:
                user_id = UUID(user_id)
            except ValueError:
                raise InvalidID("Invalid user id")
        
        if wallet_type not in ["evm", "solana"]:
            raise Exception(f"Wallet type {wallet_type} not supported")
        
        try:
            wallet = self.db.database.get_collection("wallets").find_one({
                "user_uuid": user_id,
                "wallet_type": wallet_type
            })
            if wallet:
                return Wallet(**wallet)
            return None
        except Exception as e:
            console.error(f"Error retrieving wallet for user {user_id}: {e}")
            return None
    
    def get_wallet_account(self, user_id: UUID, wallet_type: Literal["evm", "solana"], secret: str) -> LocalAccount | None:
        wallet = self.get_wallet(user_id=user_id, wallet_type=wallet_type)
        if wallet is None: return None
        
        wallet_account = wallet.decrypt_extra(secret=secret)
        return wallet_account
    
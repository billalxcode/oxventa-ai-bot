from uuid import UUID
from uuid import uuid4
from typing import Literal
from pydantic import BaseModel
from pydantic import Field
from src.core.types import Message
from src.core.types import PluginTool
from src.core.types import AgentRuntimeAbstract
from src.core.types import Wallet

from src.clients.telegram import TelegramAbstract
from src.utils.convert_to_uuid import convert_to_uuid

from eth_account import Account
from eth_account.signers.local import LocalAccount

class CreateWalletSchema(BaseModel):
    network: Literal["evm", "solana"] = Field(...)
    name: str = Field(...)

class CreateWalletTool(PluginTool):
    def __init__(self, runtime: AgentRuntimeAbstract):
        self.runtime = runtime
        self.name = "create-wallet"
        self.schema: CreateWalletSchema = CreateWalletSchema
        self.description = """
Users can create a crypto wallet that supports EVM and Solana networks.  
- The user must provide a wallet name and select the network type.  
- If the user inputs a specific EVM network (Ethereum, BSC, Base, etc.), the network should be set to 'evm'.  
- The accepted networks are 'evm' and 'solana'.  
"""
        self.client: TelegramAbstract = self.runtime.telegram_client
        
    def create_evm_wallet(self, name: str, user_uuid: UUID) -> LocalAccount:
        secret = self.runtime.get_setting("secret_key")

        account: LocalAccount = Account.create()
        
        wallet_data = Wallet(
            uuid=uuid4(),
            user_uuid=user_uuid,
            name=name,
            address=account.address,
            wallet_type="evm"
        )

        wallet_data_with_extra = wallet_data.fill_extra(account.key, secret=secret)
        self.runtime.database_adapter.wallet.create_wallet(
            wallet_data=wallet_data_with_extra
        )
        return account
    
    def call(self, network: Literal["evm", "solana"], name: str, message: Message):
        if name is None or name.strip() == "":
            return "Give the wallet a name"
        
        if network == "solana":
            return "Sorry, it is currently not possible to create wallets on the solana network. Please wait for the next update."

        elif network == "evm":
            user_uuid = convert_to_uuid(message.from_user.id)
            account = self.create_evm_wallet(name=name, user_uuid=user_uuid)
            
            self.runtime.telegram_client.bot.reply_to(
                message=message,
                text=f"""
🎉 Your wallet has been successfully created

Wallet details:
Name: {name}
Address: {account.address}
Private Key: {account.key.hex()}
Compatible: EVM
Encrypted: AES-128

You can use this wallet for in-app transactions
"""
            )

            return "Wallet created successfully"
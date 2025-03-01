from typing import Literal
from pydantic import BaseModel
from pydantic import Field
from src.core.types import Message
from src.core.types import PluginTool
from src.core.types import AgentRuntimeAbstract

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

    def create_evm_wallet(self, name: str):
        pass

    def call(self, network: Literal["evm", "solana"], name: str, message: Message):
        if network == "solana":
            return "Sorry, it is currently not possible to create wallets on the solana network. Please wait for the next update."

        elif network == "evm":
            wallet_data = self.create_evm_wallet(name=name)
            return "Wallet created successfully"
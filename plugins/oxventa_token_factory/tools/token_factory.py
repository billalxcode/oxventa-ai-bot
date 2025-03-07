from pydantic import BaseModel
from telebot.types import InlineKeyboardButton
from telebot.types import InlineKeyboardMarkup

from src.core.types import Message
from src.core.types import Literal
from src.core.types import Field
from src.core.types import Optional
from src.core.types import PluginTool
from src.core.types import AgentRuntimeAbstract
from src.core.types import LocalAccount
from src.core.types import BrokerMessage
from src.core.logger import console
from src.clients.types import TelegramAbstract
from src.chains.types import SUPPORTED_CHAINS
from src.utils.convert_to_uuid import convert_to_uuid

from plugins.oxventa_token_factory.functions.token_factory import TokenFactoryExecutor


class TokenFactorySchema(BaseModel):
    network: Literal["ethereum", "bsc", "hardhat"] = Field(
        default="hardhat"
    )
    token_name: Optional[str] = Field(
        default_factory=str
    )
    token_symbol: Optional[str] = Field(
        default_factory=str
    )
    initial_supply: Optional[str] = Field(
        default_factory=str
    )

class TokenFactoryTool(PluginTool):
    def __init__(self, runtime: AgentRuntimeAbstract):
        self.runtime = runtime
        self.name = "token-factory"
        self.schema = TokenFactorySchema
        self.description = """
Users can create or deploy new tokens using the Token Factory. This feature supports EVM-based networks such as Ethereum, BSC, and Hardhat, but does not support the Solana network.

Requirements:
1. Users must enter:
    - Token Name
	- Token Symbol (Ticker)
	- Initial Supply as a numeric value.
2. If the user does not provide detailed information, leave the values blank.
3. Users can choose the network: Ethereum, BSC, or Hardhat.
    - Default: If no network is specified, default to Hardhat.
4. Numeric Notation Conversion:
    - Convert shorthand notations like 1k to 1000 or 1m to 1000000.
    - Ensure the total supply value is in valid numeric units.
5. If any required parameters or arguments are missing, display a message indicating that the parameters are incomplete.
"""
        self.client: TelegramAbstract = self.runtime.telegram_client

    def call(self,
             network: Literal["ethereum", "bsc", "hardhat"],
             token_name: Optional[str],
             token_symbol: Optional[str],
             initial_supply: Optional[str],
             message: Message):
        if network.lower() not in SUPPORTED_CHAINS:
            return "Failed to create a token, please complete the detailed information."
        if token_name is None or token_name.strip() == "":
            return "Failed to create a token, please complete the detailed information."
        if token_symbol is None or token_name.strip() == "":
            return "Failed to create a token, please complete the detailed information."
        if initial_supply is None or initial_supply.strip() == "":
            return "Failed to create a token, please complete the detailed information."
        if initial_supply.isdigit() is not True:
            return "Failed to create a token, make sure the initial supply is a number!"

        user_id = convert_to_uuid(message.from_user.id)

        secret = self.runtime.get_setting("secret_key")

        account: LocalAccount = self.runtime.database_adapter.wallet.get_wallet_account(
            user_id=user_id, wallet_type="evm", secret=secret)

        if account is None:
            return "Failing to create a token, you have no wallet. Please register yourself on this platform."

        console.print(f"Network selected: {network}")
        console.print(f"Token name: {token_name}")
        console.print(f"Token symbol: {token_symbol}")
        console.print(f"Initial Supply: {initial_supply}")
        console.print(f"Your account is: {account.address}")
        
        self.runtime.database_adapter.broker.create_message(
            BrokerMessage(
                message={
                    "token_name": token_name,
                    "token_symbol": token_symbol,
                    "initial_supply": initial_supply,
                    "network": network
                },
                publisher=f"message:create_token:{message.from_user.id}"
            )
        )
        
        reply_markup = InlineKeyboardMarkup(
            keyboard=[
                [
                    InlineKeyboardButton(
                        text="✅ Confirm Transaction",
                        callback_data="token_factory:confirm_transaction"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="❌ Cancel Transaction",
                        callback_data="token_factory:cancel_transaction"
                    )
                ]
            ]
        )

        self.client.bot.reply_to(
            message=message,
            text=f"""
Please check the detailed data at the time of token creation.

✨ Here is the data you provided:

🔹 Token name:
{token_name}

🔹 Token symbol or ticker:
{token_symbol}

🔹 Initial Supply:
{initial_supply}

🔹 Network
{network}

Make sure the information provided by the AI matches what you provide.
""",
            reply_markup=reply_markup
        )

        return "The transaction has been created, please click the “Confirm Transaction” button to continue."

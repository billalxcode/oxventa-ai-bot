from eth_utils.address import to_checksum_address
from eth_utils.address import is_checksum_address

from telebot.types import InlineKeyboardButton
from telebot.types import InlineKeyboardMarkup

from src.core.types import PluginTool
from src.core.types import BaseModel
from src.core.types import AgentRuntimeAbstract
from src.core.types import Optional
from src.core.types import Message
from src.core.types import Field
from src.core.types import LocalAccount
from src.core.types import BrokerMessage
from src.clients.types import TelegramAbstract
from src.chains.types import SUPPORTED_CHAINS_TYPE
from src.chains.types import SUPPORTED_CHAINS
from src.utils.convert_to_uuid import convert_to_uuid

class CreatePairSchema(BaseModel):
    network: SUPPORTED_CHAINS_TYPE
    token_address: Optional[str] = Field(
        default_factory=str
    )
    
class CreatePairWithWrapped(PluginTool):
    def __init__(self, runtime: AgentRuntimeAbstract):
        self.runtime = runtime
        self.name = "create-pair-with-wrapped-currency"
        self.schema = CreatePairSchema
        self.description = """
Users can create a new token pair with an existing token. This feature is only available on Ethereum-based networks (such as Ethereum, BSC, Hardhat) and not available on the Solana network.

Requirements:
- Users must enter a token contract address to pair with a wrapped currency (e.g., WETH).
    Note: Make sure the entered address is a valid contract address.
- If any required parameters or arguments are missing, display a message indicating that the parameters are incomplete.
"""
        self.client: TelegramAbstract = self.runtime.telegram_client

    def call(self,
             network: SUPPORTED_CHAINS_TYPE,
             token_address: Optional[str],
             message: Message):
        if network.lower() not in SUPPORTED_CHAINS:
            return "Failed to create pair, please complete the detailed information."
        if token_address is None or token_address.strip() == "":
            return "Failed to create pair, please complete the detailed information."

        token_checksum_address = to_checksum_address(token_address)
        if is_checksum_address(token_checksum_address) is not True:
            return "Make sure token is a valid contract address"

        user_id = convert_to_uuid(message.from_user.id)
        secret = self.runtime.get_setting("secret_key")

        account: LocalAccount = self.runtime.database_adapter.wallet.get_wallet_account(
            user_id=user_id, wallet_type="evm", secret=secret
        )

        if account is None:
            return "Failed to create pair, you have no wallet. Please register yourself on this platform."

        self.runtime.database_adapter.broker.create_message(
            BrokerMessage(
                message={
                    "network": network,
                    "token_address": token_checksum_address
                },
                publisher=f"message:create_pair:{message.from_user.id}"
            )
        )

        reply_markup = InlineKeyboardMarkup(
            keyboard=[
                [
                    InlineKeyboardButton(
                        text="✅ Confirm Transaction",
                        callback_data="create_pair:confirm_transaction"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="❌ Cancel Transaction",
                        callback_data="create_pair:cancel_transaction"
                    )
                ]
            ]
        )

        self.client.bot.reply_to(
            message=message,
            text=f"""
Please check the detailed data at the time of create pair.

✨ Here is the data you provided:

🔹 Token address:
{token_checksum_address}

🔹 Token Pair With:
Wrapped Currency (WETH)

🔹 Network
{network}

Make sure the information provided by the AI matches what you provide.
""",
            reply_markup=reply_markup
        )

        return "The transaction has been created, please click the “Confirm Transaction” button to continue."
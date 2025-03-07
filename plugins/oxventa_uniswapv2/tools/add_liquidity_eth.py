from eth_utils.address import is_checksum_address
from eth_utils.address import to_checksum_address

from telebot.types import InlineKeyboardButton
from telebot.types import InlineKeyboardMarkup

from src.core.types import AgentRuntimeAbstract
from src.core.types import BaseModel
from src.core.types import PluginTool
from src.core.types import Optional
from src.core.types import Field
from src.core.types import Message
from src.core.types import BrokerMessage
from src.core.types import LocalAccount
from src.clients.types import TelegramAbstract
from src.chains.types import SUPPORTED_CHAINS_TYPE
from src.chains.types import SUPPORTED_CHAINS
from src.utils.convert_to_uuid import convert_to_uuid
from src.utils.is_number import is_decimal_number

class AddLiquidityETHSchema(BaseModel):
    network: SUPPORTED_CHAINS_TYPE
    token_address: Optional[str] = Field(
        default_factory=str
    )
    amount_eth: Optional[str] = Field(
        default_factory=str
    )
    amount_token: Optional[str] = Field(
        default_factory=str
    )

class AddLiquidityETH(PluginTool):
    def __init__(self, runtime: AgentRuntimeAbstract):
        self.runtime = runtime
        self.name = "add-liquidity-eth"
        self.schema = AddLiquidityETHSchema
        self.description = """
Users can add liquidity to tokens with native currency. To add liquidity, this tool uses uniswap v2 as its main provider in order to add liquidity.

This is not available on the solana network, only on ethereum-based networks.
- The user must enter token address, where token address is the token that you want to add liquidity to. Make sure that the user enters the address of the token contract.
  Input example: 0xDc64a140Aa3E981100a9becA4E685f962f0cF6C9
- The user must enter the amount of eth that will be used as liquidity.
- The user must enter the number of tokens that will be used as liquidity.

If the argument or parameter is incomplete, then indicate that the argument is incomplete.
"""
        self.client: TelegramAbstract = self.runtime.telegram_client

    def call(self,
             network: SUPPORTED_CHAINS_TYPE,
             token_address: Optional[str],
             amount_eth: Optional[str],
             amount_token: Optional[str],
             message: Message):
        if network.lower() not in SUPPORTED_CHAINS:
            return "Failed to add liquidity eth, please complete the detailed information."
        if token_address is None or token_address.strip() == "":
            return "Failed to add liquidity eth, please complete the detailed information."
        if amount_eth is None or amount_eth.strip() == "":
            return "Failed to add liquidity eth, please complete the detailed information."
        if amount_token is None or amount_token.strip() == "":
            return "Failed to add liquidity eth, please complete the detailed information."
        
        if is_decimal_number(amount_eth) is not True:
            return "Failed to add liquidity eth, make sure the amount token is a valid number!"
        if is_decimal_number(amount_token) is not True:
            return "Failed to add liquidity eth, make sure the amount token is a valid number!"
        
        token_checksum_address = to_checksum_address(token_address)

        if is_checksum_address(token_checksum_address) is not True:
            return "Make sure token is a valid contract address"
        
        user_id = convert_to_uuid(message.from_user.id)

        secret = self.runtime.get_setting("secret_key")

        account: LocalAccount = self.runtime.database_adapter.wallet.get_wallet_account(
            user_id=user_id, wallet_type="evm", secret=secret
        )
        if account is None:
            return "Failed to add liquidity eth, you have no wallet. Please register yourself on this platform."

        self.runtime.database_adapter.broker.create_message(
            BrokerMessage(
                message={
                    "network": network,
                    "token_address": token_checksum_address,
                    "amount_eth": amount_eth,
                    "amount_token": amount_token
                },
                publisher=f"message:add_liquidity_eth:{message.from_user.id}"
            )
        )

        reply_markup = InlineKeyboardMarkup(
            keyboard=[
                [
                    InlineKeyboardButton(
                        text="✅ Confirm Transaction",
                        callback_data="add_liquidity_eth:confirm_transaction"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="❌ Cancel Transaction",
                        callback_data="add_liquidity_eth:cancel_transaction"
                    )
                ]
            ]
        )

        self.client.bot.reply_to(
            message=message,
            text=f"""
Please check the detailed data at the time of add liquidity eth.

✨ Here is the data you provided:

🔹 Token address:
{token_checksum_address}

🔹 Token Pair With:
Wrapped Currency (WETH)

🔹 Amount ETH:
{amount_eth}

🔹 Amount Token
{amount_token}

🔹 Network
{network}

Make sure the information provided by the AI matches what you provide.
""",
            reply_markup=reply_markup
        )

        return "The transaction has been created, please click the “Confirm Transaction” button to continue."
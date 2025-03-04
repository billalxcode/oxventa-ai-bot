from telebot.types import CallbackQuery
from telebot.callback_data import CallbackDataFilter
from telebot.custom_filters import AdvancedCustomFilter
from web3.types import TxReceipt

from src.core.logger import console
from src.core.types import AgentRuntimeAbstract
from src.core.types import LocalAccount
from src.core.exceptions import InsufficientBalance
from src.chains.types import ChainEvmAbstract
from src.clients.types import TelegramAbstract
from src.utils.convert_to_uuid import convert_to_uuid
from plugins.oxventa_token_factory.tools.token_factory import TokenFactoryTool
from plugins.oxventa_token_factory.functions.token_factory import TokenFactoryExecutor

class ConfirmTransactionFilter(AdvancedCustomFilter):
    key = "config"

    def check(self, call: CallbackQuery, config: CallbackDataFilter):
        return config.check(query=call)
    
class TokenFactory:
    def __init__(self, runtime: AgentRuntimeAbstract):
        self.runtime: AgentRuntimeAbstract = runtime
        self.client: TelegramAbstract = self.runtime.telegram_client

    def handle_confirm_transaction(self, call: CallbackQuery):
        broker_publisher = f"message:create_token:{call.from_user.id}"
        broker_message = self.runtime.database_adapter.broker.get_message(publisher=broker_publisher)
        if broker_message is None:
            console.error("Broker message is null")
            self.client.bot.answer_callback_query(call.id, text="Invalid data")
            return False
        
        token_name = broker_message.message["token_name"]
        token_symbol = broker_message.message["token_symbol"]
        initial_supply = broker_message.message["initial_supply"]
        network = broker_message.message["network"]

        secret = self.runtime.get_setting("secret_key")
        user_id = convert_to_uuid(call.from_user.id)
        account: LocalAccount = self.runtime.database_adapter.wallet.get_wallet_account(user_id=user_id, wallet_type="evm", secret=secret)

        chain: ChainEvmAbstract = self.runtime.chains.select_chain(network)
        executor = TokenFactoryExecutor(self.runtime, chain=chain)
        executor.load_artifact()
        executor.set_account(account=account)
        
        self.client.bot.reply_to(
            message=call.message,
            text="Transaction is being processed, please wait a moment..."
        )
        try:
            transaction_hash = executor.create_token(
                token_name=token_name,
                token_symbol=token_symbol,
                initial_supply=initial_supply
            )

            self.client.bot.reply_to(
                message=call.message,
                text="Transaction has been sent. Please wait a moment, your transaction is waiting for confirmation from the network..."
            )

            transaction_recipient: TxReceipt = chain.w3.eth.wait_for_transaction_receipt(transaction_hash=transaction_hash)
            token_address = transaction_recipient["contractAddress"]
            transaction_gas_used = transaction_recipient["gasUsed"]
            transaction_block_number = transaction_recipient["blockNumber"]

            self.client.bot.reply_to(
                message=call.message,
                text=f"""
🎉 Contract successfully deployed

Here are the transaction details

✨ Contract address
`{token_address}`

💰 Gas used
`{transaction_gas_used}` WEI

🔓 Transaction hash
`{transaction_hash}`

💡 Block transaction
`{transaction_block_number}`
""",
                parse_mode="markdown"
            )
            self.client.bot.answer_callback_query(
                call.id, text="Confirm a transaction"
            )
        except InsufficientBalance:
            self.client.bot.reply_to(
                message=call.message,
                text="❌ Insufficient balance to create the token."
            )

    def handle_cancel_transaction(self, call: CallbackQuery):
        broker_publisher = f"message:create_token:{call.from_user.id}"
        self.runtime.database_adapter.broker.remove_message_by_publisher(broker_publisher)

        self.client.bot.reply_to(
            message=call.message,
            text="❌ Transaction canceled"
        )
        self.client.bot.answer_callback_query(
            callback_query_id=call.id,
            text="Transaction canceled"
        )

    def register(self):
        self.runtime.tools.register(TokenFactoryTool(self.runtime))

        self.client.bot.register_callback_query_handler(
            callback=lambda call: self.handle_confirm_transaction(call=call),
            func=lambda call: call.data == "token_factory:confirm_transaction",
        )
        self.client.bot.register_callback_query_handler(
            callback=lambda call: self.handle_cancel_transaction(call=call),
            func=lambda call: call.data == "token_factory:cancel_transaction"
        )
        
        # self.client.bot.add_custom_filter(ConfirmTransactionFilter())

def initialize(runtime: AgentRuntimeAbstract):
    token_factory = TokenFactory(runtime=runtime)
    token_factory.register()
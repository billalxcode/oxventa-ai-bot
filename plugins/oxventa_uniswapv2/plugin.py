from telebot.types import CallbackQuery

from src.core.types import AgentRuntimeAbstract
from src.clients.types import TelegramAbstract
from plugins.oxventa_uniswapv2.tools.add_liquidity_eth import AddLiquidityETH
from plugins.oxventa_uniswapv2.tools.create_pair import CreatePairWithWrapped
from plugins.oxventa_uniswapv2.functions.create_pair import CreatePairExecutor

class UniswapV2:
    def __init__(self, runtime: AgentRuntimeAbstract):
        self.runtime = runtime
        self.client: TelegramAbstract = self.runtime.telegram_client
        self.create_pair = CreatePairExecutor(runtime=runtime)

    def init(self):
        self.create_pair.load_artifact()

    def handle_cancel_transaction(self, call: CallbackQuery, topic: str):
        broker_publisher = f"message:{topic}:{call.from_user.id}"
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
        self.runtime.tools.register(AddLiquidityETH(self.runtime))
        self.runtime.tools.register(CreatePairWithWrapped(self.runtime))

        self.client.bot.register_callback_query_handler(
            callback=lambda call: self.create_pair.callback_handler(call),
            func=lambda call: call.data == "create_pair:confirm_transaction"
        )

        for topic in ["add_liquidity_eth"]:
            self.client.bot.register_callback_query_handler(
                callback=lambda call: self.handle_cancel_transaction(call=call, topic=topic),
                func=lambda call: call.data == "add_liquidity_eth:cancel_transaction"
            )

def initialize(runtime: AgentRuntimeAbstract):
    uniswap = UniswapV2(runtime=runtime)
    uniswap.init()
    uniswap.register()
from typing import Optional, List, Callable
from telebot import TeleBot
from telebot.types import Message
from src.core.logger import console
from src.clients.types import TelegramAbstract
from src.core.types import AgentRuntimeAbstract
from src.utils.convert_to_uuid import convert_to_uuid

class Telegram(TelegramAbstract):
    def __init__(self, runtime: AgentRuntimeAbstract):
        super().__init__(runtime)
        self.runtime = runtime

        self.bot: TeleBot = None
        self.is_connected: bool = False

    def init(self):
        console.info("Initialize telegram client")
        telegram_token = self.runtime.get_setting("client.telegram.key")
        telegram_parse_mode: str = self.runtime.get_setting("client.telegram.parse_mode")

        if telegram_parse_mode.lower() not in ["markdownv2", "markdown"]:
            console.error(f"Unknown telegram client parse mode, set default to markdown v2")
            telegram_parse_mode = "MarkdownV2"

        if telegram_token:
            self.bot = TeleBot(
                telegram_token,
                num_threads=4,
                parse_mode=telegram_parse_mode
            )
            self.is_connected = True
        else:
            self.is_connected = False
            console.error("No telegram client key, please check your configuration")
            console.exit()

    def register_handlers(self):
        console.info("Registering all telegram handlers")
        self.bot.register_message_handler(
            callback=lambda msg: self.handle_start_message(msg),
            commands=["start", "help"]
        )
        self.bot.register_message_handler(
            callback=lambda msg: self.handle_new_message(msg)
        )
    
    def ensure_connection(self):
        if self.is_connected is not True:
            self.init()
    
    def stop(self):
        console.info("Stopping telegram client")
        if self.is_connected:
            self.bot.stop_bot()
            self.is_connected = False

    def build_message_handler(
            self,
            handler,
            commands: Optional[List[str]] = None,
            regexp: Optional[str] = None,
            func: Optional[Callable] = None,
            content_types: Optional[List[str]] = None,
            chat_types: Optional[List[str]] = None,
            **kwargs):
        self.bot._build_handler_dict(
            handler,
            chat_types=chat_types,
            content_types=content_types,
            commands=commands,
            regexp=regexp,
            func=func,
            **kwargs
        )

    def handle_new_message(self, message: Message):
        message_text = message.text

        console.info(f"New message: {message_text}")

        user_id = convert_to_uuid(message.from_user.id)
        user_exists = self.runtime.database_adapter.user.exists_user(user_id=user_id)
        if user_exists is False:
            self.bot.reply_to(message=message, text="You are not yet registered on this platform, please type /register to register.")
            return False

        temporary_message_wait_moment = self.bot.reply_to(message=message, text=f"👀 Agent is running, wait a moment...")
        # self.runtime.agent.execute(message_text, message=message)

        self.bot.delete_message(
            chat_id=temporary_message_wait_moment.chat.id,
            message_id=temporary_message_wait_moment.message_id
        )

    def reply_to(self, message: Message, text: str):
        message_return = self.bot.reply_to(
            message=message,
            text=text
        )
        return message_return

    def handle_start_message(self, message: Message):
        message_text = message.text

        console.info(f"New message: {message_text}")
        self.bot.send_message(message.chat.id, "Pongggg")

    def start(self):
        console.info("Starting telegram client")
        self.bot.polling()
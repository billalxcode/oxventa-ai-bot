from pydantic import ValidationError

from src.core.types import AgentRuntimeAbstract
from src.core.types import Message
from src.core.types import Users
from src.clients.types import TelegramAbstract
from src.core.logger import console
from src.utils.convert_to_uuid import convert_to_uuid

class AuthPlugin:
    def __init__(self, runtime: AgentRuntimeAbstract):
        self.runtime: AgentRuntimeAbstract = runtime
        self.client: TelegramAbstract = runtime.telegram_client

    def handle_email_message(self, message: Message):
        message_text = message.text
        message_from_user = message.from_user

        user_uuid = convert_to_uuid(message_from_user.id)

        user = Users(
            email=message_text,
            username=message_from_user.username,
            first_name=message_from_user.first_name,
            last_name=message_from_user.last_name,
            uuid=user_uuid
        )

        console.info(f"Register new user: {user.full_name}")
        self.runtime.database_adapter.user.create_user(user)
        
        self.client.bot.reply_to(
            message=message,

            text=f"🎉 Congratulations, successful registration. You can now use this platform"
        )

    def handle_register_message(self, message: Message):
        self.client.bot.reply_to(
            message=message,
            text="Okay, give me your email"
        )
        self.client.bot.register_next_step_handler(
            message=message,
            callback=lambda msg: self.handle_email_message(msg)
        )

    def register(self):
        console.info("Registering all oxventa auth handler")
        self.client.bot.register_message_handler(
            callback=lambda msg: self.handle_register_message(msg),
            commands=["register"]
        )
        self.client.bot.enable_save_next_step_handlers(delay=20)
        self.client.bot.load_next_step_handlers()

def initialize(runtime: AgentRuntimeAbstract):
    auth_plugin = AuthPlugin(runtime=runtime)
    auth_plugin.register()
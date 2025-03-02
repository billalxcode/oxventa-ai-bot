import base58
from uuid import uuid4
from uuid import UUID
from pydantic import ValidationError
from solders.keypair import Keypair
from eth_account.account import Account
from eth_account.signers.local import LocalAccount

from src.core.types import AgentRuntimeAbstract
from src.core.types import Message
from src.core.types import Users
from src.core.types import Wallet
from src.clients.types import TelegramAbstract
from src.core.logger import console
from src.utils.convert_to_uuid import convert_to_uuid

class AuthPlugin:
    def __init__(self, runtime: AgentRuntimeAbstract):
        self.runtime: AgentRuntimeAbstract = runtime
        self.client: TelegramAbstract = runtime.telegram_client

    def create_solana_wallet(self, user_id: UUID, message: Message):
        keypair = Keypair()
        
        private_key_bytes = keypair.secret()
        public_key_bytes = bytes(keypair.pubkey())

        encoded_keypair = private_key_bytes + public_key_bytes
        private_key = base58.b58encode(encoded_keypair)

        wallet_data = Wallet(
            uuid=uuid4(),
            user_uuid=user_id,
            address=str(keypair.pubkey()),
            wallet_type="solana",
            extra={
                "privkey": keypair.to_json()
            }
        )
        self.runtime.database_adapter.wallet.create_wallet(wallet_data=wallet_data)
        self.client.bot.reply_to(
            message=message,
            text=f"""
🎉 Congratulations, your Solana wallet was successfully created

💳 Your wallet address
`{keypair.pubkey()}`

🔑 Your wallet private key
`{private_key.decode()}`

For security reasons, do not share your private key!
""",
            parse_mode="markdown"
        )

    def create_evm_wallet(self, user_id: UUID, message: Message):
        secret = self.runtime.get_setting("secret_key")
        account: LocalAccount = Account.create()

        wallet_data = Wallet(
            uuid=uuid4(),
            user_uuid=user_id,
            address=account.address,
            wallet_type="evm"
        )
        wallet_with_extra_data = wallet_data.fill_extra(account.key, secret=secret)
        self.runtime.database_adapter.wallet.create_wallet(wallet_data=wallet_with_extra_data)

        self.client.bot.reply_to(
            message=message,
            text=f"""
🎉 Congratulations, your EVM wallet was successfully created

💳 Your wallet address
`{account.address}`

🔑 Your wallet private key
`0x{account.key.hex()}`

For security reasons, do not share your private key!
""",
            parse_mode="markdown"
        )

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
        self.create_evm_wallet(user_id=user_uuid, message=message)
        self.create_solana_wallet(user_id=user_uuid, message=message)

        self.client.bot.reply_to(
            message=message,
            text=f"🎉 Congratulations, successful registration. You can now use this platform"
        )
            # self.client.bot.reply_to(
            #     message=message,
            #     text=f"❌ Invalid email, please re-input your email."
            # )
            # self.client.bot.register_next_step_handler(
            #     message=message,
            #     callback=lambda msg: self.handle_email_message(msg)
            # )
            # return False

    def handle_register_message(self, message: Message):
        user_id = convert_to_uuid(message.from_user.id)
        if message.chat.type != "private":
            self.client.bot.reply_to(message=message, text="Sorry, the registration feature is not available in the group. Please register your account privately")
            return False
        user_exists = self.runtime.database_adapter.user.exists_user(user_id=user_id)
        if user_exists:
            self.client.bot.reply_to(message=message, text="It looks like you already have an account, you can't create a new one.")
            return False
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
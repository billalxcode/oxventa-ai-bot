import os
import json
from pathlib import Path
from telebot.types import CallbackQuery
from web3.types import TxReceipt
from web3.constants import ADDRESS_ZERO
from src.core.types import AgentRuntimeAbstract
from src.core.types import LocalAccount
from src.core.logger import console
from src.core.types import SettingContracts
from src.core.exceptions import InsufficientBalance
from src.chains.types import ChainEvmAbstract
from src.clients.types import TelegramAbstract
from src.utils.convert_to_uuid import convert_to_uuid

from plugins.oxventa_uniswapv2.exceptions import AlreadyTokenPair

class CreatePairExecutor:
    def __init__(self, runtime: AgentRuntimeAbstract):
        self.runtime: AgentRuntimeAbstract = runtime
        self.client: TelegramAbstract = self.runtime.telegram_client
        self.artifact = {}

    def load_artifact(self):
        console.info("Loading artifact for CreatePairExecutor")
        artifact_token_factory_path = os.path.join(
            Path(
                os.path.dirname(__file__)
            ).parent,
            "data",
            "uniswap-v2-core",
            "UniswapV2Factory.sol",
            "UniswapV2Factory.json"
        )
        if os.path.isfile(artifact_token_factory_path) is not True:
            console.error(f"Artifact file not found at path: {artifact_token_factory_path}")
            return False
        with open(artifact_token_factory_path, "r") as File:
            artifact_raw = File.read()
            artifact_json = json.loads(artifact_raw)
            File.close()
            self.artifact = artifact_json
        return True

    def create_pair(self, token_address: str, chain: ChainEvmAbstract, account: LocalAccount):
        settings_contract: SettingContracts = self.runtime.get_setting("contracts")[chain.name]
        factory_address = settings_contract.uniswap_v2_factory
        wrapped_token_address = settings_contract.wrapped_token
        owner_address = account.address
        
        factory_contract = chain.get_contract(factory_address, abi=self.artifact['abi'])
        
        owner_balance = chain.get_balance(owner_address)

        get_pair_function = factory_contract.functions.getPair(token_address, wrapped_token_address)
        pair_address = get_pair_function.call()

        if pair_address != ADDRESS_ZERO:
            raise AlreadyTokenPair(pair_address=pair_address)
        else:
            create_pair_function = factory_contract.functions.createPair(token_address, wrapped_token_address)
            create_pair_estimated_gas = create_pair_function.estimate_gas({
                "from": owner_address,
                "value": 0
            })

            if owner_balance < create_pair_estimated_gas:
                raise InsufficientBalance(f"Insufficient balance to create a pair. Required: {create_pair_estimated_gas} wei, Available: {owner_balance} wei")

            create_pair_transaction = create_pair_function.build_transaction({
                "from": owner_address,
                "gas": 3000000,
                "gasPrice": chain.generate_gas_price(),
                "nonce": chain.get_nonce(owner_address),
                "value": 0
            })
            signed_transaction = account.sign_transaction(create_pair_transaction)

            try:
                create_pair_tx_hash = chain.send_raw_transaction(
                    signed_transaction.raw_transaction
                )
                pair_address = get_pair_function.call()
                return create_pair_tx_hash.hex(), pair_address
            except Exception as e:
                console.print_exception()
                return False
        
    def callback_handler(self, call: CallbackQuery):
        broker_publisher = f"message:create_pair:{call.from_user.id}"
        broker_message = self.runtime.database_adapter.broker.get_message(publisher=broker_publisher)
        if broker_message is None:
            console.error("Broker message is null")
            self.client.bot.answer_callback_query(call.id, text="Invalid data")
            return False

        token_address =  broker_message.message["token_address"]
        network = broker_message.message["network"]

        secret = self.runtime.get_setting("secret_key")
        user_id = convert_to_uuid(call.from_user.id)
        account: LocalAccount = self.runtime.database_adapter.wallet.get_wallet_account(
            user_id=user_id, wallet_type="evm", secret=secret
        )
        chain: ChainEvmAbstract = self.runtime.chains.select_chain(network)
        
        self.client.bot.reply_to(
            message=call.message,
            text="Transaction is being processed, please wait a moment..."
        )

        try:
            transaction_hash, pair_address = self.create_pair(token_address=token_address, chain=chain, account=account)
            self.client.bot.reply_to(
                message=call.message,
                text="Transaction has been sent. Please wait a moment, your transaction is waiting for confirmation from the network..."
            )

            transaction_recipient: TxReceipt = chain.w3.eth.wait_for_transaction_receipt(transaction_hash=transaction_hash)
            
            console.log(transaction_recipient)

            transaction_gas_used = transaction_recipient["gasUsed"]
            transaction_block_number = transaction_recipient["blockNumber"]

            self.client.bot.reply_to(
                message=call.message,
                text=f"""
🎉 Successfully create token pair

Here are the transaction details

✨ Contract address
`{token_address}`

🔗 Token Pair address
`{pair_address}`

💰 Gas used
`{transaction_gas_used}` WEI

🔓 Transaction hash
`{transaction_hash}`

💡 Block transaction
`{transaction_block_number}`
""",
                parse_mode="markdown"
            )
        except InsufficientBalance:
            self.client.bot.reply_to(
                message=call.message,
                text="❌ Insufficient balance to create the token."
            )
        except AlreadyTokenPair as e:
            self.client.bot.reply_to(
                message=call.message,
                text=f"""
Sorry, it looks like this token already has a token pair address.

🔗 Pair Address:
`{e.pair_address}`

You cannot create a pair address anymore.
""",
                parse_mode="markdown"
            )
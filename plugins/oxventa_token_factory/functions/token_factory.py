import os
import json
from pathlib import Path
from eth_account.signers.local import LocalAccount
from src.chains.types import ChainEvmAbstract
from src.core.logger import console
from src.core.types import AgentRuntimeAbstract
from src.core.types import SettingContracts
from src.core.exceptions import InsufficientBalance

class TokenFactoryExecutor:
    def __init__(self, runtime: AgentRuntimeAbstract, chain: ChainEvmAbstract):
        self.runtime = runtime
        self.chain = chain
        self.artifact = {}
        self.account = ""

    def load_artifact(self):
        console.info("Loading artifact for TokenFactory")
        artifact_token_factory_path = os.path.join(
            Path(
                os.path.dirname(__file__)
            ).parent,
            "data",
            "artifacts",
            "contracts",
            "Token.sol",
            "OxVentaToken.json"
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

    def set_account(self, account: LocalAccount):
        self.account = account

    def create_token(self,
                     token_name: str,
                     token_symbol: str,
                     initial_supply: int):
        owner_address = self.account.address
        owner_balance = self.chain.get_balance(owner_address)

        token_factory_contract = self.chain.w3.eth.contract(
            bytecode=self.artifact["bytecode"],
            abi=self.artifact["abi"]
        )
        
        create_token_function = token_factory_contract.constructor(
            token_name,
            token_symbol,
            int(initial_supply),
            owner_address
        )
        
        create_token_estimated_gas = create_token_function.estimate_gas({
            "from": owner_address,
            "value": 0
        })
        console.info(f"Owner address: {owner_address}")
        console.info(f"Owner balance: {owner_balance}")
        console.info(f"Estimated gas: {self.chain.w3.from_wei(create_token_estimated_gas, 'ether')}")

        if owner_balance < create_token_estimated_gas:
            raise InsufficientBalance(f"Insufficient balance to create token. Required: {create_token_estimated_gas} wei, Available: {owner_balance} wei")
        
        create_token_transaction = create_token_function.build_transaction({
            "from": owner_address,
            "gas": 3000000,
            "gasPrice": self.chain.generate_gas_price(),
            "nonce": self.chain.get_nonce(owner_address),
            "value": 0
        })
        
        signed_transaction = self.account.sign_transaction(create_token_transaction)

        try:
            create_token_tx_hash = self.chain.send_raw_transaction(
                signed_transaction.raw_transaction
            )
            return create_token_tx_hash.hex()
        except Exception as e:
            console.print_exception()
            return False
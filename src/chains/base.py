from web3 import Web3
from web3 import HTTPProvider
from web3.types import TxParams
from web3.contract.contract import Contract
from typing import Union

from src.chains.types import ChainEvmAbstract
from src.chains.types import Address
from src.chains.types import ChecksumAddress
from src.chains.types import HexStr
from web3.middleware import ExtraDataToPOAMiddleware
from web3.gas_strategies.rpc import rpc_gas_price_strategy

class BaseChainEvm(ChainEvmAbstract):
    def __init__(self, endpoint_url: str, name: str, base_explorer_url: str):
        self.name = name
        self.w3 = Web3(
            HTTPProvider(
                endpoint_uri=endpoint_url
            )
        )
        self.base_explorer_url = base_explorer_url

    def get_chain_id(self):
        return self.w3.eth.chain_id
    
    def get_gas_price(self):
        return self.w3.eth.gas_price
    
    def generate_gas_price(self):
        return self.w3.eth.generate_gas_price()
    
    def estimate_gas(self, transaction: TxParams):
        return self.w3.eth.estimate_gas(
            transaction=transaction
        )
    
    
    def get_nonce(self, address: Union[Address, ChecksumAddress]):
        return self.w3.eth.get_transaction_count(address)
    
    def get_balance(self, address: Union[Address, ChecksumAddress]):
        return self.w3.eth.get_balance(address)
    
    def send_transaction(self, tx_params: TxParams):
        return self.w3.eth.send_transaction(tx_params)
    
    def send_raw_transaction(self, transaction: Union[HexStr, bytes]):
        return self.w3.eth.send_raw_transaction(transaction=transaction)
    
    def get_contract(self, address: Union[Address, ChecksumAddress], abi: dict) -> Contract:
        return self.w3.eth.contract(address=address, abi=abi)
    
    def add_gas_price_strategy(self):
        self.w3.eth.set_gas_price_strategy(rpc_gas_price_strategy)

    def add_poa_middleware(self):
        if self.exists_poa_middleware() is False:
            self.w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0, name="poa_middleware")

    def exists_poa_middleware(self):
        middleware = self.w3.middleware_onion.get("poa_middleware")
        if middleware is None: return False
        return True
    
    def format_explorer_tx_hash(self, tx_hash: str):
        return f"{self.base_explorer_url}/tx/{tx_hash}"
    
    def format_explorer_address(self, address: str):
        return f"{self.base_explorer_url}/address/{address}"
    
    def format_explorer_token(self, token: str):
        return f"{self.base_explorer_url}/token/{token}"
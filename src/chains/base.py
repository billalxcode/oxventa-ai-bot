from web3 import Web3
from web3 import HTTPProvider
from web3.types import TxParams
from typing import Union

from src.chains.types import ChainEvmAbstract
from src.chains.types import Address
from src.chains.types import ChecksumAddress
from src.chains.types import HexStr

class BaseChainEvm(ChainEvmAbstract):
    def __init__(self, endpoint_url: str):
        self.w3 = Web3(
            HTTPProvider(
                endpoint_uri=endpoint_url
            )
        )

    def get_chain_id(self):
        return self.w3.eth.chain_id
    
    def get_gas_price(self):
        return self.w3.eth.gas_price
    
    def generate_gas_price(self, transaction: TxParams):
        return self.w3.eth.generate_gas_price(transaction_params=transaction)
    
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
    
    def send_raw_transaction(self, transaction_hash: Union[HexStr, bytes]):
        return super().send_raw_transaction(transaction_hash)
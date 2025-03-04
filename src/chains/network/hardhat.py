from src.chains.base import BaseChainEvm

class HardhatNetwork(BaseChainEvm):
    def __init__(self):
        super().__init__(
            "http://localhost:7545",
            name="hardhat",
            base_explorer_url="http://localhost:8545/"
        )
        self.add_poa_middleware()
        self.add_gas_price_strategy()
from src.chains.base import BaseChainEvm

class HardhatNetwork(BaseChainEvm):
    def __init__(self):
        super().__init__(
            "http://localhost:8545"
        )
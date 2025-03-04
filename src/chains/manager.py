from typing import Literal
from src.core.logger import console
from src.chains.types import ChainsManagerAbstract
from src.chains.base import BaseChainEvm
from src.chains.network.hardhat import HardhatNetwork

class ChainsManager(ChainsManagerAbstract):
    def __init__(self):
        super().__init__()

        self.chains = {}

    def register_chain(self, name: str, cls: BaseChainEvm):
        console.info(f"Registering chain: {name}")
        self.chains[name] = {
            "cls": cls
        }

    def register_chains(self):
        self.register_chain("hardhat", HardhatNetwork())
        
    def select_chain(self, name: Literal["ethereum", "base", "bsc", "hardhat"]):
        return self.chains[name]["cls"]
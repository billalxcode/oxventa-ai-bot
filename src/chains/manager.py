from src.chains.types import ChainsManagerAbstract

class ChainsManager(ChainsManagerAbstract):
    def __init__(self):
        super().__init__()

        self.chains = []

    def register_chain(self):
        return super().register_chain()
from src.core.types import AgentRuntimeAbstract

from plugins.oxventa_wallet.tools.create_wallet import CreateWalletTool

class WalletPlugin:
    def __init__(self, runtime: AgentRuntimeAbstract):
        self.runtime: AgentRuntimeAbstract = runtime

    def register(self):
        self.runtime.tools.register(CreateWalletTool(self.runtime))

def initialize(runtime: AgentRuntimeAbstract):
    wallet_plugin = WalletPlugin(runtime=runtime)
    wallet_plugin.register()
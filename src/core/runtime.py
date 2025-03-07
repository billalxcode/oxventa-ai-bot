import threading
from datetime import datetime
from src.core.logger import console
from src.core.character import Character
from src.core.settings import Settings
from src.core.types import MongoAdapterAbstract
from src.core.types import AgentRuntimeAbstract
from src.core.types import AgentAbstract
from src.core.types import ToolsManagerAbstract
from src.core.types import PluginManagerAbstract
from src.core.worker import WorkerThread
from src.core.plugin import PluginManager
from src.core.tools import ToolsManager
from src.clients.telegram import Telegram
from src.clients.types import TelegramAbstract
from src.chains.manager import ChainsManager
from src.chains.types import ChainsManagerAbstract

class AgentRuntime(AgentRuntimeAbstract):
    def __init__(
        self,
        character: Character,
        settings: Settings
    ):
        self.character: Character = character
        self.settings: Settings = settings
        self.database_adapter: MongoAdapterAbstract = None
        self.stop_polling = threading.Event()

        self.chains: ChainsManagerAbstract = ChainsManager()

        self.telegram_client: TelegramAbstract = None
        
        self.worker: WorkerThread = None

        self.agent: AgentAbstract = None
        self.plugins: PluginManagerAbstract = None
        self.tools: ToolsManagerAbstract = None

    def init(self):
        self.telegram_client = Telegram(self)
        self.tools: ToolsManagerAbstract = ToolsManager(
            self
        )

        self.plugins: PluginManagerAbstract = PluginManager(
            self
        )

        self.chains.register_chains()
        
        self.worker = WorkerThread(
            "Runtime",
            target=self.telegram_client.start,
            args=()
        )

    def set_agent(self, agent: AgentAbstract):
        self.agent = agent
    
    def set_database_adapter(self, adapter: MongoAdapterAbstract):
        self.database_adapter = adapter
    
    def get_setting(self, key: str):
        keys = key.split('.')
        value = self.settings
        for k in keys:
            if k.isdigit():
                k = int(k)
                value = value[k] if isinstance(value, list) and 0 <= k < len(value) else None
            else:
                value = getattr(value, k, None)
                if value is None:
                    break
        return value
    
    def start_client(self):
        self.telegram_client.init()

    def start(self):
        self.start_client()

        self.plugins.call_all_plugins()
        self.plugins.print_informative_plugins()

        self.tools.build()
        self.tools.print_informative_tools()

        self.agent.initialize_prompt()
        self.agent.start_agent()

        self.telegram_client.register_handlers()
        self.worker.start()

        console.print(
            self.get_setting("contracts")["hardhat"]
        )
        with console.status(f"[magenta](time)[/magenta] App now running") as status:
            while self.worker.running:
                try:
                    status.update(f"[magenta]({datetime.now().strftime('%H:%M:%S')})[/magenta] App now running")
                except KeyboardInterrupt:
                    console.error("User keyboard interrupt, stopping the worker")
                    self.worker.stop()
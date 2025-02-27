import threading
from datetime import datetime
from src.core.logger import console
from src.core.character import Character
from src.core.settings import Settings
from src.core.types import MongoAdapterAbstract
from src.core.types import AgentRuntimeAbstract
from src.core.types import AgentAbstract
from src.core.types import PluginManagerAbstract
from src.core.worker import WorkerThread
from src.core.plugin import PluginManager
from src.clients.telegram import Telegram
from src.clients.types import TelegramAbstract

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

        self.telegram_client: TelegramAbstract = None
        
        self.worker: WorkerThread = None

        self.agent: AgentAbstract = None
        self.plugins: PluginManagerAbstract = None

    def init(self):
        self.telegram_client = Telegram(self)

        self.plugins: PluginManagerAbstract = PluginManager(
            self
        )

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
            value = getattr(value, k, None)
            if value is None:
                break
        return value
    
    def start_client(self):
        self.telegram_client.init()

    def start(self):
        self.start_client()
        self.worker.start()

        self.plugins.call_all_plugins()
        self.plugins.print_informative_plugins()
        with console.status(f"[magenta](time)[/magenta] App now running") as status:
            while self.worker.running:
                try:
                    status.update(f"[magenta]({datetime.now().strftime('%H:%M:%S')})[/magenta] App now running")
                except KeyboardInterrupt:
                    console.error("User keyboard interrupt, stopping the worker")
                    self.worker.stop()
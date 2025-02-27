import os
import json
import importlib
from typing import Callable
from rich.table import Table
from src.core.worker import console
from src.core.types import AgentRuntimeAbstract
from src.core.types import PluginManagerAbstract
from src.core.types import PluginMetadata

class PluginManager(PluginManagerAbstract):
    def __init__(self, runtime: AgentRuntimeAbstract):
        self.runtime: AgentRuntimeAbstract = runtime
        self.plugins: list[Callable] = []
        self.plugins_metadata: list[PluginMetadata] = []
        
        self.cwd: str = os.getcwd()

        self.load_plugins()

    def load_plugins(self):
        console.info("Loading plugins configuration...")
        plugin_settings = self.runtime.get_setting("plugins")
        
        for plugin in plugin_settings:
            plugin_initialize_status = self.initialize_plugin(plugin)
            if plugin_initialize_status is True:
                console.info(f"Successfully initialized plugin: {plugin}")
            else:
                console.error(f"Failed to initialize plugin: {plugin}")

    def load_metadata(self, metadata_path: str):
        with open(metadata_path, "r") as File:
            try:
                metadata_raw = File.read()
                metadata_json = json.loads(metadata_raw)
                return PluginMetadata(**metadata_json)
            except (ValueError, json.JSONDecodeError):
                console.error(f"Failed to load plugin metadata from `{metadata_path}`.")
                return None
    
    def from_path_to_module(self, plugin_path: str):
        plugin_name = plugin_path.replace(self.cwd, "")
        plugin_module_name = plugin_name.replace("/", ".")
        if plugin_module_name.startswith("."):
            plugin_module_name = plugin_module_name[1:]
        if plugin_module_name.endswith(".py"):
            plugin_module_name = plugin_module_name[
                :len(plugin_module_name)-len(".py")
            ]
        return plugin_module_name
    
    def initialize_plugin(self, plugin_path: str):
        plugin_real_path = os.path.join(
            self.cwd,
            plugin_path
        )
        if os.path.isdir(plugin_real_path) is not True:
            console.error(f"Plugin directory `{plugin_real_path}` does not exist.")
            return False
        
        plugin_metadata_path = os.path.join(
            plugin_real_path,
            "metadata.json"
        )
        if os.path.isfile(plugin_metadata_path) is not True:
            console.error(f"Plugin metadata file `{plugin_metadata_path}` does not exist.")
            return False
        
        plugin_metadata = self.load_metadata(metadata_path=plugin_metadata_path)
        if plugin_metadata is None:
            console.error(f"Failed to initialize plugin from `{plugin_metadata_path}` due to invalid metadata.")
            return False

        plugin_initialize_file = os.path.join(
            plugin_real_path,
            "plugin.py"
        )
        if os.path.isfile(plugin_initialize_file) is not True:
            console.error(f"Plugin initialization file `{plugin_initialize_file}` does not exist.")
            return False
        
        try:
            plugin_module_name = self.from_path_to_module(plugin_path=plugin_initialize_file)
            plugin_module = importlib.import_module(plugin_module_name)
            self.plugins.append(plugin_module.initialize)
            self.plugins_metadata.append(plugin_metadata)
            return True
        except Exception as e:
            console.error(f"An error occurred while initializing the plugin: {e}")
            return False
        
    def call_all_plugins(self):
        for plugin in self.plugins:
            try:
                plugin(self.runtime)
            except Exception as e:
                console.print_exception()
                console.error(f"An error occurred while calling the plugin: {e}")
                return False
    
    def print_informative_plugins(self):
        table = Table(
            title="OxVenta Plugins Manager",
            caption="OxVenta Active Plugins Metadata"
        )
        table.add_column("#", justify="center", style="cyan", no_wrap=True)
        table.add_column("Plugin Name", style="magenta")
        table.add_column("Author", style="green")
        table.add_column("Version")
        table.add_column("License")

        for table_number, plugin_metadata in enumerate(self.plugins_metadata):
            table.add_row(
                str(table_number),
                plugin_metadata.name,
                plugin_metadata.author,
                str(plugin_metadata.version),
                plugin_metadata.license
            )
        console.print(table)

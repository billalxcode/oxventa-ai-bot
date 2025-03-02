from src.core.logger import console
from src.core.types import Message
from src.core.types import PluginTool
from src.core.types import ToolsManagerAbstract
from src.core.types import AgentRuntimeAbstract

from functools import partial
from langchain.tools import StructuredTool

class ToolsManager(ToolsManagerAbstract):
    def __init__(self, runtime: AgentRuntimeAbstract):
        self.runtime = runtime
        self.tools: list[PluginTool] = []
        self.tools_binding: list[StructuredTool] = []

        self.message: Message = None

    def update_message(self, message: Message):
        self.message = message

    def register(self, tool: PluginTool):
        console.info(f"Registering tool: {tool.name}")
        self.tools.append(tool)

    def build(self):
        for tool in self.tools:
            console.info(f"Building tool: {tool.name}")
            tool_for_binding = StructuredTool(
                name=tool.name,
                func=lambda **kwargs: tool.call(**kwargs, message=self.message),
                description=tool.description,
                args_schema=tool.schema
            )
            tool_for_binding.model_dump()
            self.tools_binding.append(tool_for_binding)

    def print_informative_tools(self):
        return super().print_informative_tools()
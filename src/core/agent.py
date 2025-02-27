from src.core.types import AgentAbstract
from src.core.types import AgentRuntimeAbstract
from src.core.logger import console

from langgraph.prebuilt import create_react_agent
from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage

class Agent(AgentAbstract):
    def __init__(self, runtime: AgentRuntimeAbstract):
        super().__init__(runtime)
        
        self.model:  BaseChatModel = None

    def init(self):
        agent_environment = self.runtime.get_setting("agent.environment")
        
        model_provider = agent_environment["model_provider"]
        model_name = agent_environment["model_name"]

        console.info("Initialize agent")
        self.model = init_chat_model(
            model=model_name,
            model_provider=model_provider,
            # api_key="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"
        )
    
    def initialize_character(self):
        pass
    
    def execute(self, input: str):
        console.info("Execute with agent")
        response = self.model.invoke(input=input)
        return response.content
from src.core.types import AgentAbstract
from src.core.types import AgentRuntimeAbstract
from src.core.logger import console
from src.clients.types import TelegramAbstract

from telebot.types import Message

from langgraph.prebuilt import create_react_agent
from langgraph.graph.graph import CompiledGraph
from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage
from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate

class Agent(AgentAbstract):
    def __init__(self, runtime: AgentRuntimeAbstract):
        self.runtime = runtime
        self.prompt: ChatPromptTemplate = None

        self.model:  BaseChatModel = None
        self.agent: CompiledGraph = None

    def init(self):
        agent_environment = self.runtime.get_setting("agent.environment")
        
        model_provider = agent_environment["model_provider"]
        model_name = agent_environment["model_name"]

        console.info("Initialize agent")
        self.model = init_chat_model(
            model=model_name,
            model_provider=model_provider,
            
        )
    
    def initialize_prompt(self):
        console.info("Initializing prompt for the agent")
        character = self.runtime.character

        character_skills_string = ", ".join(character.bio.skills[:-1]) + " and " + character.bio.skills[-1]
        character_personality_string = ", ".join(character.bio.personality[:-1]) + " and " + character.bio.personality[-1]

        character_prompt = f"""
You are {character.name}, an advanced {character.bio.role} designed to assist users with {character_skills_string}. You have an {character_personality_string} while maintaining a professional yet casual tone.

🧠 Knowledge & Skills
{character.build_knowledge()}
           
🎭 Personality & Communication Style
{character.build_communication_style()}

📜 Background (Lore)
{character.build_lore()}

If someone asks an off-topic question, then answer naturally that you can't answer off-topic.

Make sure the parameters you send to the tool are JSON!
If there are any other questions related to the topic and yourself, make sure you answer naturally and without using tools!
Make sure your response is short, clear, and natural.
Answer questions naturally, making sure that the questions and answers do not go off topic. If the user does not provide arguments or parameters for the tool, make sure to indicate that the arguments or parameters must be filled in.
"""
        self.prompt = character_prompt
    
    def start_agent(self):
        console.info("Binding tools with the agent")
        tools = self.runtime.tools
        self.agent = create_react_agent(
            model=self.model,
            tools=tools.tools_binding,
            prompt=self.prompt
        )
    
    def execute(self, input: str, message: Message):
        console.info("Execute with agent")
        temporary_messages: list[Message] = []
        telegram_client: TelegramAbstract = self.runtime.telegram_client

        self.runtime.tools.update_message(message=message)
        
        for agent_step in self.agent.stream({
            "messages": HumanMessage(content=input)
        }, stream_mode="values"):
            agent_message = agent_step["messages"][-1]
            console.print(agent_message)
            if isinstance(agent_message, AIMessage) and agent_message.content.strip() != "":
                console.info(f"Agent response: {agent_message.content}")
                message_return = telegram_client.reply_to(message=message, text=agent_message.content)
                temporary_messages.append(message_return)
        
        if len(temporary_messages) > 1:
            message_ids = [msg.message_id for msg in temporary_messages[:-1]]
            telegram_client.bot.delete_messages(chat_id=message.chat.id, message_ids=message_ids)
        
        telegram_client.reply_to(message=message, text=f"👌 Okay, all in done")
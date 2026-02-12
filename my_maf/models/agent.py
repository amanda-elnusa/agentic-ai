import time
import os
from abc import ABC, abstractmethod
from typing import Optional, List
from azure.identity import AzureCliCredential
from agent_framework.azure import AzureOpenAIChatClient
from dotenv import load_dotenv

load_dotenv()

AZURE_OPENAI_API_VERSION = os.environ["AZURE_OPENAI_API_VERSION"]
AZURE_OPENAI_API_KEY = os.environ["AZURE_OPENAI_API_KEY"]
AZURE_OPENAI_CHAT_DEPLOYMENT_NAME = os.environ["AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"]

class AgentBaseModel(ABC):  
    def __init__(self, instruction: str, tools: Optional[List] = None):
        self.instruction = instruction
        self.tools = tools or []
        self.agent = self._create_agent()
    
    def _create_agent(self):
        agent = AzureOpenAIChatClient(
            credential=AzureCliCredential()
        ).create_agent(
            instructions=self.instruction,
            tools=self.tools,
        )
        return agent
    
    @abstractmethod
    async def ask(self, query: str) -> str:
        """
        Abstract method to ask the agent a question
        
        Args:
            query: User's question/query
            
        Returns:
            str: Agent's response
        """
        pass
    
    async def stream(self, query: str):
        """Stream response from agent"""
        print(f"\nStreaming {self.__class__.__name__} Agent...\n")  

        async for chunk in self.agent.run_stream(query):
            if chunk.text:
                print(chunk.text, end="", flush=True)
    
    async def respond(self, query: str) -> str:
        """Get non-streaming response from agent"""
        print(f"\nResponding without stream ({self.__class__.__name__})...\n")
        
        result = await self.agent.run(query)

        print(f"{self.__class__.__name__}:", result, "\n")
        return result



import os
import time
import requests
import asyncio
import aiohttp
from models.agent import AgentBaseModel
from dotenv import load_dotenv
from agent_framework import ai_function
from typing import Annotated
from pydantic import Field

load_dotenv()

AIMA_URL = os.environ["AIMA_URL"]
AIMA_INSTRUCTION = os.environ["AIMA_INSTRUCTION"]

class Aima(AgentBaseModel):    
    def __init__(self):
        super().__init__(
            instruction=AIMA_INSTRUCTION,
            tools=[self.ask]
        )
    
    @ai_function(name="ask", description="Asks user's query to AIMA and returns response")
    async def ask_v1(
        self,
        message: Annotated[str, Field(description="Pesan user untuk dikirim ke AIMA Chatbot API.")]
    ) -> str:
        try:
            print("[WARNING] You are using v1, switch to the newest method for faster results.")

            url = AIMA_URL
            
            payload = {
                "messages": [
                    {"role": "user", "content": message}
                ]
            }

            # @@@
            start_time = time.time()
            
            res = requests.post(url, json=payload, timeout=40)
            res.raise_for_status()
            data = res.json()

            # @@@
            end_time = time.time()     
            elapsed = end_time - start_time

            if "context" in data and "data_points" in data["context"]:
                text_data = data["context"]["data_points"].get("text", [])
                if text_data:
                    response_text = "\n".join(text_data[:1])

            if not response_text:
                response_text = str(data)
            
            # Calculate response length
            response_length = len(response_text)
            
            print(f"[AIMA TOOL] Response time: {elapsed:.3f} sec | Length: {response_length} chars\n")

            return response_text
        
        except Exception as e:
            return f"Error accessing AIMA: {e}"
        
    @ai_function(name="ask", description="Asks user's query to AIMA and returns response")
    async def ask(
        self,
        message: Annotated[str, Field(description="Pesan user untuk dikirim ke AIMA Chatbot API.")]
    ) -> str:
        try:
            payload = {
                "messages": [
                    {"role": "user", "content": message}
                ]
            }

            # @@@
            start_time = time.time()
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    AIMA_URL,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=40)
                ) as resp:
                    resp.raise_for_status()
                    data = await resp.json()

            # @@@
            end_time = time.time()     
            elapsed = end_time - start_time

            # Extract response
            response_text = ""
            if "context" in data and "data_points" in data["context"]:
                text_data = data["context"]["data_points"].get("text", [])
                if text_data:
                    response_text = "\n".join(text_data[:1])
            
            if not response_text:
                response_text = str(data)
            
            # Calculate response length
            response_length = len(response_text)
            
            print(f"[AIMA TOOL] Response time: {elapsed:.3f} sec | Length: {response_length} chars\n")

            return response_text

        except Exception as e:
            return f"Error accessing AIMA: {e}"

if __name__ == "__main__":
    async def main():
        print("[BEGIN]\n")

        agent = Aima()
        
        query = "Jenis kargo apa saja yang diangkut oleh PT Pertamina Trans Kontinental?"
        print("User:", query)

        # @@@
        start_time = time.time()

        await agent.stream(query)

        # @@@
        end_time = time.time()     
        elapsed = end_time - start_time
        print(f"\n\n[AIMA STREAM] Total response time: {elapsed:.3f} sec\n")

    asyncio.run(main())
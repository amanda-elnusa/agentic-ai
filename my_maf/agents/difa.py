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

DIFA_SECRET = os.environ["DIFA_SECRET"]
DIFA_TOKEN_URL = os.environ["DIFA_TOKEN_URL"]
DIFA_URL = os.environ["DIFA_URL"]
DIFA_INSTRUCTION = os.environ["DIFA_INSTRUCTION"]

class Difa(AgentBaseModel):    
    def __init__(self):
        super().__init__(
            instruction=DIFA_INSTRUCTION,
            tools=[self.ask]
        )
    
    @ai_function(name="ask", description="Asks user's query to DIFA and returns response")
    async def ask_v1(
        self,
        message: Annotated[str, Field(description="Pesan user untuk dikirim ke DIFA Chatbot API.")]
    ) -> str:
        try:
            print("[WARNING] You are using v1, switch to the newest method for faster results.")

            # @@@
            start_time = time.time()

            token_res = requests.get(
                DIFA_TOKEN_URL,
                headers={
                    "Authorization": f"Bearer {DIFA_SECRET}",
                    "Content-Type": "application/json"
                }
            ).json()

            # @@@
            token_time = time.time()
            print(f"\n[DIFA TOOL - TOKEN] Response time: {(token_time - start_time):.3f} sec")

            directline_token = token_res["token"]

            conv_res = requests.post(
                DIFA_URL,
                headers={
                    "Authorization": f"Bearer {directline_token}",
                    "Content-Type": "application/json"
                }
            ).json()

            # @@@
            conv_id_time = time.time()
            print(f"[DIFA TOOL - CONV_ID] Response time: {(conv_id_time - token_time):.3f} sec")

            conv_id = conv_res["conversationId"]

            requests.post(
                DIFA_URL + f'/{conv_id}/activities',
                headers={
                    "Authorization": f"Bearer {directline_token}",
                    "Content-Type": "application/json"
                },
                json={
                    "type": "message",
                    "from": {"id": "azure-agent"},
                    "text": message
                }
            )
            
            # @@@
            post_time = time.time()
            print(f"[DIFA TOOL - POST] Response time: {(post_time - conv_id_time):.3f} sec")
            
            for _ in range(20):
                time.sleep(15)
                data = requests.get(
                    DIFA_URL + f'/{conv_id}/activities',
                    headers={"Authorization": f"Bearer {directline_token}"}
                ).json()

                activities = data.get("activities", [])
                if len(activities) > 1:
                    bot_messages = [a["text"] for a in activities if a["from"]["id"] != "azure-agent"]
                    if bot_messages:
                        response_text = bot_messages[-1]

                        # @@@ 
                        response_length = len(response_text)
                        get_time = time.time()
                        print(f"[DIFA TOOL - GET] Response time: {(get_time - start_time):.3f} sec | Length: {response_length} chars\n")
                        return response_text
                    
                return "DIFA tidak merespons dalam waktu yang ditentukan."

        except Exception as e:
            return f"Error accessing DIFA: {e}"

    @ai_function(name="ask", description="Asks user's query to DIFA and returns response")
    async def ask(
        self,
        message: Annotated[str, Field(description="Pesan user untuk dikirim ke DIFA Chatbot API.")]
    ) -> str:
        try:
            # @@@
            start_time = time.time()

            async with aiohttp.ClientSession() as session:
                # 1. Get token
                async with session.get(
                    DIFA_TOKEN_URL,
                    headers={
                        "Authorization": f"Bearer {DIFA_SECRET}",
                        "Content-Type": "application/json"
                    }
                ) as resp:
                    token_res = await resp.json()
                
                # @@@
                token_time = time.time()
                print(f"[DIFA TOOL - TOKEN] Response time: {(token_time - start_time):.3f} sec")

                directline_token = token_res["token"]

                # 2. Create conversation
                async with session.post(
                    DIFA_URL,
                    headers={
                        "Authorization": f"Bearer {directline_token}",
                        "Content-Type": "application/json"
                    }
                ) as resp:
                    conv_res = await resp.json()
                
                # @@@
                conv_id_time = time.time()
                print(f"[DIFA TOOL - CONV_ID] Response time: {(conv_id_time - token_time):.3f} sec")

                conv_id = conv_res["conversationId"]

                # 3. Send message
                async with session.post(
                    DIFA_URL + f'/{conv_id}/activities',
                    headers={
                        "Authorization": f"Bearer {directline_token}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "type": "message",
                        "from": {"id": "azure-agent"},
                        "text": message
                    }
                ) as resp:
                    await resp.read()
                
                # @@@
                post_time = time.time()
                print(f"[DIFA TOOL - POST] Response time: {(post_time - conv_id_time):.3f} sec")

                poll_intervals = [2, 3, 5, 7, 10, 15]
                max_attempts = 20
                
                for attempt in range(max_attempts):
                    if attempt < len(poll_intervals):
                        delay = poll_intervals[attempt]
                    else:
                        delay = 15
                    
                    await asyncio.sleep(delay)
                    
                    async with session.get(
                        DIFA_URL + f'/{conv_id}/activities',
                        headers={"Authorization": f"Bearer {directline_token}"}
                    ) as resp:
                        data = await resp.json()
                    
                    # @@@
                    elapsed = time.time() - start_time
                    print(f"[DIFA TOOL - Poll #{attempt+1}] Elapsed: {elapsed:.3f} sec")

                    activities = data.get("activities", [])
                    if len(activities) > 1:
                        bot_messages = [a["text"] for a in activities if a["from"]["id"] != "azure-agent"]
                        if bot_messages:
                            response_text = bot_messages[-1]

                            # @@@
                            response_length = len(response_text)
                            get_time = time.time()
                            print(f"[DIFA TOOL - GET] Response time: {(get_time - start_time):.3f} sec | Length: {response_length} chars\n")
                            
                            return response_text

                return "DIFA tidak merespons dalam waktu yang ditentukan."

        except Exception as e:
            return f"Error accessing DIFA: {e}"

if __name__ == "__main__":
    async def main():
        print("[BEGIN]\n")

        agent = Difa()
        
        query = "Siapa saja yang tergabung dalam usecase Jargas?"
        print("User:", query)

        # @@@
        start_time = time.time()

        await agent.stream(query)

        # @@@
        end_time = time.time()     
        elapsed = end_time - start_time
        print(f"\n\n[DIFA STREAM] Total response time: {elapsed:.3f} sec\n")

    asyncio.run(main())
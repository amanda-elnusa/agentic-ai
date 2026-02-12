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

GINO_SECRET = os.environ["GINO_SECRET"]
GINO_TOKEN_URL = os.environ["GINO_TOKEN_URL"]
GINO_URL = os.environ["GINO_URL"]
GINO_INSTRUCTION = os.environ["GINO_INSTRUCTION"]

class Gino(AgentBaseModel):    
    def __init__(self):
        super().__init__(
            instruction=GINO_INSTRUCTION,
            tools=[self.ask]
        )
    
    @ai_function(name="ask", description="Asks user's query to GINO and returns response")
    async def ask_v1(
        self,
        message: Annotated[str, Field(description="Pesan user untuk dikirim ke GINO Chatbot API.")]
    ) -> str:
        try:
            print("[WARNING] You are using v1, switch to the newest method for faster results.")

            # @@@
            start_time = time.time()

            token_res = requests.get(
                GINO_TOKEN_URL,
                headers={
                    "Authorization": f"Bearer {GINO_SECRET}",
                    "Content-Type": "application/json"
                }
            ).json()
            # @@@
            token_time = time.time()
            print(f"\n[GINO TOOL - TOKEN] Response time: {(token_time - start_time):.3f} sec")

            directline_token = token_res["token"]

            conv_res = requests.post(
                GINO_URL,
                headers={
                    "Authorization": f"Bearer {directline_token}",
                    "Content-Type": "application/json"
                }
            ).json()
            # @@@
            conv_id_time = time.time()
            print(f"[GINO TOOL - CONV_ID] Response time: {(conv_id_time - token_time):.3f} sec")

            conv_id = conv_res["conversationId"]

            requests.post(
                GINO_URL + f'/{conv_id}/activities',
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

            for _ in range(20):
                time.sleep(15)
                data = requests.get(
                    GINO_URL + f'/{conv_id}/activities',
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
                        print(f"[GINO TOOL - GET] Response time: {(get_time - start_time):.3f} sec | Length: {response_length} chars\n")
                        return response_text
                    
                return "GINO tidak merespons dalam waktu yang ditentukan."

        except Exception as e:
            return f"Error accessing GINO: {e}"

    @ai_function(name="ask", description="Asks user's query to GINO and returns response")
    async def ask(
        self,
        message: Annotated[str, Field(description="Pesan user untuk dikirim ke GINO Chatbot API.")]
    ) -> str:
        try:
            # @@@
            start_time = time.time()

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    GINO_TOKEN_URL,
                    headers={
                        "Authorization": f"Bearer {GINO_SECRET}",
                        "Content-Type": "application/json"
                    }
                ) as resp:
                    token_res = await resp.json()
                
                # @@@
                token_time = time.time()
                print(f"[GINO TOOL - TOKEN] Response time: {(token_time - start_time):.3f} sec")

                directline_token = token_res["token"]

                async with session.post(
                    GINO_URL,
                    headers={
                        "Authorization": f"Bearer {directline_token}",
                        "Content-Type": "application/json"
                    }
                ) as resp:
                    conv_res = await resp.json()

                # @@@
                conv_id_time = time.time()
                print(f"[GINO TOOL - CONV_ID] Response time: {(conv_id_time - token_time):.3f} sec")

                conv_id = conv_res["conversationId"]

                # Send message
                async with session.post(
                    GINO_URL + f'/{conv_id}/activities',
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
                print(f"[GINO TOOL - POST] Response time: {(post_time - conv_id_time):.3f} sec")

                # OPTIMIZED POLLING with exponential backoff
                poll_intervals = [2, 3, 5, 7, 10, 15]  # Start fast, then slow down
                max_attempts = 20
                
                for attempt in range(max_attempts):
                    if attempt < len(poll_intervals):
                        delay = poll_intervals[attempt]
                    else:
                        delay = 15
                    
                    await asyncio.sleep(delay)
                    
                    async with session.get(
                        GINO_URL + f'/{conv_id}/activities',
                        headers={"Authorization": f"Bearer {directline_token}"}
                    ) as resp:
                        data = await resp.json()

                    # @@@
                    elapsed = time.time() - start_time
                    print(f"[GINO TOOL - Poll #{attempt+1}] Elapsed: {elapsed:.3f} sec")

                    activities = data.get("activities", [])
                    if len(activities) > 1:
                        bot_messages = [a["text"] for a in activities if a["from"]["id"] != "azure-agent"]
                        if bot_messages:
                            response_text = bot_messages[-1]

                            # @@@
                            response_length = len(response_text)
                            get_time = time.time()
                            print(f"[GINO TOOL - GET] Response time: {(get_time - start_time):.3f} sec | Length: {response_length} chars\n")

                            return response_text

                return "GINO tidak merespons dalam waktu yang ditentukan."

        except Exception as e:
            return f"Error accessing GINO: {e}"
        
if __name__ == "__main__":
    async def main():
        print("[BEGIN]\n")

        agent = Gino()
        
        query = "Apa lembaga inspeksi yang melakukan inspeksi untuk DPPU Ahmad Yani?"
        print("User:", query)

        # @@@
        start_time = time.time()

        await agent.stream(query)

        # @@@
        end_time = time.time()     
        elapsed = end_time - start_time
        print(f"\n\n[GINO STREAM] Total response time: {elapsed:.3f} sec\n")

    asyncio.run(main())
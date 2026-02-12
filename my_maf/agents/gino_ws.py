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
    async def ask(
        self,
        message: Annotated[str, Field(description="Pesan user untuk dikirim ke GINO Chatbot API.")]
    ) -> str:
        try:
            # @@@
            start_time = time.time()

            async with aiohttp.ClientSession() as session:
                # 1. Get token
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

                # 2. Start conversation
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
                stream_url = conv_res["streamUrl"]

                # 3. Send message
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

                # 4. Connect to WebSocket stream
                async with session.ws_connect(
                    stream_url,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as ws:
                                        
                    msg_cnt = 0
                    async for msg in ws:
                        if msg.type == aiohttp.WSMsgType.TEXT:

                            msg_cnt += 1
                            if msg_cnt == 3:
                                data = msg.json()
                                activities = data["activities"]
                                response = activities[0]["text"]

                                # @@@
                                ws_time = time.time()
                                print(f"[GINO TOOL - GET WS] Response time: {(ws_time - post_time):.3f} sec | Length: {len(response)} chars\n")

                                return(response)               

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
import os
import ast
import asyncio
from dotenv import load_dotenv
from azure.identity import AzureCliCredential
from agent_framework.azure import AzureOpenAIChatClient
# from agents.aima import Aima
# from agents.difa import Difa
# from agents.gino import Gino
from agents.new_aima import Aima
from agents.new_difa import Difa
from agents.new_gino import Gino

load_dotenv()

ORCHESTRATOR_INSTRUCTION = os.environ["ORCHESTRATOR_INSTRUCTION"]

async def run_orchestration(orchestrator, agents, user_input: str):
    """Run multi-agent orchestration"""

    routing_raw = await orchestrator.run(user_input)

    try:
        routing = ast.literal_eval(str(routing_raw))
    except:
        print("[ERROR] Failed to parse JSON.")
        return {
            "Error": "[ORCHESTRATOR] Failed to parse JSON",
            "raw_response": routing_raw
        }

    target_agent = routing.get("agent")
    message = routing.get("message")

    try:
        agent = agents[target_agent]
    except:
        print("[ERROR] Unknown Agent.")
        return {"Error": "[ORCHESTRATOR] Unknown agent"}

    message = routing.get("message")
    await agent.stream(message)

if __name__ == "__main__":
    async def main():
        print("[BEGIN]\n")

        orchestrator = AzureOpenAIChatClient(
            credential=AzureCliCredential()
        ).create_agent(
            instructions=ORCHESTRATOR_INSTRUCTION,
        )

        agents = {
            'aima_agent': Aima(),
            'difa_agent': Difa(),
            'gino_agent': Gino()
        }

        # query = "Jenis kargo apa saja yang diangkut oleh PT Pertamina Trans Kontinental?" # aima
        # query = "Siapa saja yang tergabung dalam usecase Jargas?" # difa
        query = "Apa lembaga inspeksi yang melakukan inspeksi untuk DPPU Ahmad Yani?" # gino
        print("User:", query)

        await run_orchestration(orchestrator, agents, query)

    asyncio.run(main())
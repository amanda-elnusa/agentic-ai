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
from orchestrator import run_orchestration

load_dotenv()

ORCHESTRATOR_INSTRUCTION = os.environ["ORCHESTRATOR_INSTRUCTION"]

async def interactive_cli():
    """Interactive CLI for testing orchestrator"""
    
    print("=" * 60)
    print("ORCHESTRATOR INTERACTIVE CLI")
    print("=" * 60)
    print("\nInitializing agents...")
    
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
    
    print("✓ All agents initialized!\n")
    print("Available agents:")
    print("  - aima_agent: PT Pertamina Trans Kontinental queries")
    print("  - difa_agent: Jargas usecase queries")
    print("  - gino_agent: DPPU inspection queries")
    print("\nCommands:")
    print("  'quit' or 'exit' - Exit the CLI")
    print("  'clear' - Clear screen")
    print("=" * 60)
    
    while True:
        print("\n" + "-" * 60)
        user_input = input("You: ").strip()
        
        if not user_input:
            continue
            
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("\nExiting... Goodbye!")
            break
            
        if user_input.lower() == 'clear':
            os.system('clear' if os.name != 'nt' else 'cls')
            continue
        
        try:
            await run_orchestration(orchestrator, agents, user_input)
        except Exception as e:
            print(f"\n[ERROR] {e}")

if __name__ == "__main__":
    asyncio.run(interactive_cli())
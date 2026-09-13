import sys
from pathlib import Path

# Add project root and src to path
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from langchain_core.messages import HumanMessage
from ops_pilot.agent.graph import create_agent

CLI_THREAD_ID = "cli-session-001"

def print_separator():
    print("-" * 60)

def main():
    print("Initializing OpsPilot Agent...")
    try:
        agent_app = create_agent()
    except Exception as e:
        print(f"Error compiling agent graph: {e}")
        print("Ensure your environment variables (like API keys) are set correctly.")
        sys.exit(1)
        
    print("OpsPilot Agent Ready! Type 'exit' or 'quit' to stop.")
    print("Example prompts:")
    print(" - 'Is the VPN down?'")
    print(" - 'Create a ticket for EMP001 about monitor flickering'")
    print(" - 'Check status of ticket TKT001'")
    print(" - 'How do I connect to the office WiFi?'")
    print_separator()

    config = {"configurable": {"thread_id": CLI_THREAD_ID}}
    
    while True:
        try:
            user_input = input("\nYou: ")
            if user_input.strip().lower() in ["exit", "quit"]:
                print("Goodbye!")
                break
            if not user_input.strip():
                continue
                
            print("\n[OpsPilot is thinking...]")
            
            # Stream the agent's execution step by step
            for event in agent_app.stream(
                {"messages": [HumanMessage(content=user_input)]},
                config,
                stream_mode="updates",
            ):
                for node_name, node_state in event.items():
                    print(f"  [Graph Trace] -> Node executed: '{node_name}'")
                    
                    if "messages" in node_state and node_state["messages"]:
                        last_msg = node_state["messages"][-1]
                        
                        # Print tool invocations
                        if getattr(last_msg, "tool_calls", None):
                            for tc in last_msg.tool_calls:
                                print(f"     🛠️ Tool Call: {tc['name']}({tc['args']})")
                        
                        # Print final agent answer
                        if getattr(last_msg, "content", None) and not getattr(last_msg, "tool_calls", None) and last_msg.type == "ai":
                            print(f"\nOpsPilot: {last_msg.content}")
                        
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"\n[Error during execution]: {e}")

if __name__ == "__main__":
    main()

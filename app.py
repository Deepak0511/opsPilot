# Entrypoint
from ops_pilot.utils.models import load_llm
# Sanity Test the LLM connectivity
llm = load_llm()

print("Configuration Loaded Successfully")
print("LLM Loaded Successfully")
print(type(llm))

response = llm.invoke("What is LangGraph in one sentence?")
print(response.content)
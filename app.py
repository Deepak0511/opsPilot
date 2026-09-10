# Entrypoint
# app.py — This entire file re-runs on every user interaction
__author__ = "Deepak Kumar Chaudhary <deepak.techprofile@gmail.com>"


from ops_pilot.utils.models import load_llm
import streamlit as st

# Sanity Test the LLM connectivity
llm = load_llm()

print("Configuration Loaded Successfully")
print("LLM Loaded Successfully")
print(type(llm))

response = llm.invoke("What is LangGraph in one sentence?")
print(response.content)

#Test Streamlit UI
st.title("Hello OpsPilot")       # renders <h1>
name = st.text_input("Name")     # renders <input>, returns the value
st.write(f"Hello, {name}!")       # renders <p>s
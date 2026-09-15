# App Entry point
__author__ = "Deepak Kumar Chaudhary <deepak.techprofile@gmail.com>"


import sys
from pathlib import Path
from typing import Any, cast

import streamlit as st
import ulid
from langchain_core.messages import HumanMessage, ToolMessage
from langchain_core.runnables import RunnableConfig

# Make the src layout importable when Streamlit is started from the project root.
PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
	sys.path.insert(0, str(SRC_DIR))

from ops_pilot.agent.graph import create_agent
from ops_pilot.ui.theme import apply_enterprise_theme
from ops_pilot.utils.logger import log


@st.cache_resource
def get_agent():
	"""Create one compiled agent per Streamlit process."""
	return create_agent()


def create_thread_id() -> str:
	return str(ulid.new())


def reset_conversation() -> None:
	"""Clear the UI session and force a fresh compiled agent on the next run."""
	cast(Any, get_agent).clear()
	st.session_state.clear()
	st.session_state.thread_id = create_thread_id()
	st.session_state.chat_messages = []
	st.session_state.ticket_created = False


st.set_page_config(page_title="OpsPilot", page_icon="🪼", layout="wide")
# Disable this line to remove custom enterprise styling
apply_enterprise_theme()
st.title("OpsPilot")
st.caption("IT support assistant")

if "thread_id" not in st.session_state:
	st.session_state.thread_id = create_thread_id()
if "chat_messages" not in st.session_state:
	st.session_state.chat_messages = []
if "ticket_created" not in st.session_state:
	st.session_state.ticket_created = False

with st.sidebar:
	st.title("OpsPilot")
	st.caption("Agentic IT operations support")
	st.divider()

	st.subheader("Active session")
	st.caption("Thread ID")
	st.code(st.session_state.thread_id, language=None)
	st.caption(f"Conversation turns: {len(st.session_state.chat_messages) // 2}")
	st.divider()

	st.subheader("Conversation controls")
	if st.button("Reset conversation", use_container_width=True):
		reset_conversation()
		st.rerun()

for message in st.session_state.chat_messages:
	with st.chat_message(message["role"]):
		st.markdown(message["content"])

if prompt := st.chat_input("How can I help you?", disabled=st.session_state.get("ticket_created", False)):
	st.session_state.chat_messages.append({"role": "user", "content": prompt})
	with st.chat_message("user"):
		st.markdown(prompt)

	config: RunnableConfig = {
		"configurable": {"thread_id": st.session_state.thread_id},
		"recursion_limit": 12,
	}
	tool_executions = []

	with st.chat_message("assistant"):
		try:
			with st.status("Working...", expanded=False) as status:
				responses = []
				for event in get_agent().stream(
					{"messages": [HumanMessage(content=prompt)]},
					config,
					stream_mode="updates",
				):
					for node_state in event.values():
						for message in node_state.get("messages", []):
							for tool_call in getattr(message, "tool_calls", []):
								tool_executions.append(
									{
										"id": tool_call["id"],
										"name": tool_call["name"],
										"inputs": tool_call["args"],
										"output": None,
										"status": "running",
									}
								)
							if isinstance(message, ToolMessage):
								for execution in tool_executions:
									if execution["id"] == message.tool_call_id:
										execution["output"] = message.content
										execution["status"] = getattr(
											message, "status", "success"
										)
							if message.type == "ai" and message.content:
								if message.content not in responses:
									responses.append(message.content)
				status.update(label="Complete", state="complete")

			if tool_executions:
				with st.expander("Tool execution details"):
					for index, execution in enumerate(tool_executions, start=1):
						label = f"{index}. {execution['name']} ({execution['status']})"
						with st.expander(label, expanded=False):
							st.markdown("**Inputs**")
							st.json(execution["inputs"])
							st.markdown("**Output**")
							output = execution["output"]
							if output is None:
								st.write("No output was returned.")
							else:
								st.write(output)

			response = "\n\n".join(responses)
			if not response:
				response = "I could not generate a response. Please try again."

			# Check if a ticket was successfully created in this turn
			new_ticket = False
			if "✅ **Ticket action completed successfully.**" in response:
				new_ticket = True
				st.session_state.ticket_created = True
				response += "\n\n**A designated IT representative will connect with you shortly. Please reset the conversation to report a new issue.**"

			st.markdown(response)
			st.session_state.chat_messages.append(
				{"role": "assistant", "content": response}
			)
			
		except Exception:
			log.exception("OpsPilot request failed")
			st.error("Something went wrong while handling your request. Please try again.")

	if new_ticket:
		st.rerun()

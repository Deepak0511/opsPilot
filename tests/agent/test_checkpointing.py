import sqlite3

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph

from ops_pilot.agent.state import AgentState


def _message_input(content: str) -> AgentState:
    return AgentState(messages=[HumanMessage(content=content)])


def _thread_config(thread_id: str) -> RunnableConfig:
    return {"configurable": {"thread_id": thread_id}}


def _build_checkpoint_test_graph(database_path):
    connection = sqlite3.connect(database_path, check_same_thread=False)
    checkpointer = SqliteSaver(connection)
    graph = StateGraph(AgentState)

    def respond(state: AgentState) -> dict:
        return {"messages": [AIMessage(content="Acknowledged.")]}

    graph.add_node("respond", respond)
    graph.add_edge(START, "respond")
    graph.add_edge("respond", END)

    return graph.compile(checkpointer=checkpointer), connection


def test_same_thread_preserves_messages_between_turns(tmp_path):
    database_path = str(tmp_path / "checkpoint.db")
    agent, connection = _build_checkpoint_test_graph(database_path)
    config = _thread_config("conversation-1")

    try:
        first_result = agent.invoke(
            _message_input("First message"),
            config,
        )
        second_result = agent.invoke(
            _message_input("Follow-up message"),
            config,
        )

        assert [message.content for message in first_result["messages"]] == [
            "First message",
            "Acknowledged.",
        ]
        assert [message.content for message in second_result["messages"]] == [
            "First message",
            "Acknowledged.",
            "Follow-up message",
            "Acknowledged.",
        ]
    finally:
        connection.close()


def test_different_threads_are_isolated(tmp_path):
    database_path = str(tmp_path / "checkpoint.db")
    agent, connection = _build_checkpoint_test_graph(database_path)

    try:
        agent.invoke(
            _message_input("Private message"),
            _thread_config("conversation-1"),
        )
        other_result = agent.invoke(
            _message_input("Other message"),
            _thread_config("conversation-2"),
        )

        assert [message.content for message in other_result["messages"]] == [
            "Other message",
            "Acknowledged.",
        ]
    finally:
        connection.close()


def test_same_thread_is_restored_after_rebuilding_graph(tmp_path):
    database_path = str(tmp_path / "checkpoint.db")
    config = _thread_config("conversation-1")

    first_agent, first_connection = _build_checkpoint_test_graph(database_path)
    first_agent.invoke(
        _message_input("Before restart"),
        config,
    )
    first_connection.close()

    restored_agent, restored_connection = _build_checkpoint_test_graph(database_path)
    try:
        result = restored_agent.invoke(
            _message_input("After restart"),
            config,
        )

        assert [message.content for message in result["messages"]] == [
            "Before restart",
            "Acknowledged.",
            "After restart",
            "Acknowledged.",
        ]
    finally:
        restored_connection.close()
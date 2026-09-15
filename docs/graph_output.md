# OpsPilot Agent Graph Architecture

This document contains the visual workflow and state transitions of the OpsPilot multi-agent system.
It is auto-generated on-demand for documentation and architectural review.

## State Graph Flowchart

```mermaid
---
config:
  flowchart:
    curve: linear
---
graph TD;
	__start__([<p>__start__</p>]):::first
	triage(triage)
	kb_node(kb_node)
	infra_node(infra_node)
	ticket_read_node(ticket_read_node)
	ticket_logger_node(ticket_logger_node)
	tools(tools)
	__end__([<p>__end__</p>]):::last
	__start__ --> triage;
	infra_node -. &nbsp;done&nbsp; .-> __end__;
	infra_node -.-> kb_node;
	infra_node -.-> ticket_logger_node;
	infra_node -.-> ticket_read_node;
	infra_node -.-> tools;
	kb_node -. &nbsp;done&nbsp; .-> __end__;
	kb_node -.-> ticket_logger_node;
	kb_node -.-> ticket_read_node;
	kb_node -.-> tools;
	ticket_logger_node -. &nbsp;done&nbsp; .-> __end__;
	ticket_logger_node -.-> kb_node;
	ticket_logger_node -.-> ticket_read_node;
	ticket_logger_node -.-> tools;
	ticket_read_node -. &nbsp;done&nbsp; .-> __end__;
	ticket_read_node -.-> kb_node;
	ticket_read_node -.-> ticket_logger_node;
	ticket_read_node -.-> tools;
	triage -.-> infra_node;
	triage -.-> kb_node;
	triage -.-> ticket_logger_node;
	triage -.-> ticket_read_node;
	tools --> __end__;
	kb_node -.-> kb_node;
	ticket_logger_node -.-> ticket_logger_node;
	ticket_read_node -.-> ticket_read_node;
	classDef default fill:#f2f0ff,line-height:1.2
	classDef first fill-opacity:0
	classDef last fill:#bfb6fc

```

## Architecture Summary
- **START**: Entry point routing directly to the `triage` node.
- **Triage Node (`triage`)**: Intent classifier determining routing to specialized manager nodes.
- **Specialized Worker Nodes**:
  - `kb_node`: Knowledge Base searches.
  - `infra_node`: System health and infrastructure diagnostics.
  - `ticket_read_node`: Ticket lookup and history queries.
  - `ticket_logger_node`: Ticket creation and updates.
- **ReAct Tool Loop (`tools`)**: Shared `ToolNode` executor; routes back to the calling node upon completion.
- **END**: Concludes interaction once a terminal response is synthesized.

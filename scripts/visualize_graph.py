"""
visualize_graph.py
------------------
Independent utility to compile the OpsPilot multi-agent state graph,
extract its Mermaid flowchart definition, and persist it to a documentation
Markdown file under `docs/graph_output.md`.
"""

import sys
from pathlib import Path
from typing import Optional

# Ensure project root / src is on sys.path for direct CLI execution
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
SRC_DIR = PROJECT_ROOT / "src"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from ops_pilot.agent.graph import create_agent


class GraphVisualizer:
    """
    Utility class to compile the LangGraph workflow and export
    Mermaid diagrams for documentation.
    """

    def __init__(self, output_path: Optional[Path] = None):
        """
        Initializes the visualizer with an optional target markdown path.
        Defaults to `<project_root>/docs/graph_output.md`.
        """
        self.project_root = PROJECT_ROOT
        self.default_output_path = self.project_root / "docs" / "graph_output.md"
        self.output_path = Path(output_path) if output_path else self.default_output_path

    def get_mermaid_markup(self) -> str:
        """
        Compiles the agent graph and retrieves the Mermaid representation.

        Returns:
            str: Raw Mermaid flowchart syntax.
        """
        agent = create_agent()
        graph = agent.get_graph()
        return graph.draw_mermaid()

    def build_markdown_document(self, mermaid_markup: str) -> str:
        """
        Wraps the raw Mermaid diagram in a clean, documented markdown structure.
        """
        return f"""# OpsPilot Agent Graph Architecture

This document contains the visual workflow and state transitions of the OpsPilot multi-agent system.
It is auto-generated on-demand for documentation and architectural review.

## State Graph Flowchart

```mermaid
{mermaid_markup}
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
"""

    def export_to_file(self) -> Path:
        """
        Compiles the graph, generates the Mermaid markdown, and writes
        it to the target file.

        Returns:
            Path: Path to the generated markdown file.
        """
        print("[OpsPilot] Compiling agent state graph...")
        mermaid_markup = self.get_mermaid_markup()

        print("[OpsPilot] Generating markdown documentation...")
        markdown_content = self.build_markdown_document(mermaid_markup)

        # Ensure target directory exists (e.g. ./docs)
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

        self.output_path.write_text(markdown_content, encoding="utf-8")
        print(f"[OpsPilot] Successfully generated graph visualization at: {self.output_path}")
        return self.output_path


def main():
    """Command-line entry point for direct script execution."""
    visualizer = GraphVisualizer()
    visualizer.export_to_file()


if __name__ == "__main__":
    main()

from typing import Optional
from langchain_core.tools import tool
from ops_pilot.models.knowledge_base import KnowledgeBase
from ops_pilot.utils.logger import log

import ops_pilot.repository.knowledge_base_repository as kb_repository
from ops_pilot.utils.error_handler import handle_tool_errors
from ops_pilot.utils import validators


@tool
@handle_tool_errors
def count_knowledge_base_articles_tool(title: Optional[str] = None, category: Optional[str] = None,
                                  incident_id: Optional[str] = None, tag: Optional[str] = None) -> int:
    """Returns the count of knowledge base articles matching the given filters.
    Call this BEFORE search_knowledge_base to gauge result-set size.
    If the count is large, consider narrowing filters before fetching.
    """
    log.info(f"Tool invoked: count_knowledge_base_articles_tool(title={title}, category={category}, incident={incident_id}, tag={tag})")
    if title:
        title = validators.validate_not_empty(title, "title")
    if category:
        category = validators.validate_not_empty(category, "category")
    if incident_id:
        incident_id = validators.validate_id_format(incident_id, "incident_id")
    if tag:
        tag = validators.validate_not_empty(tag, "tag")

    return kb_repository.count_knowledge_base_articles(title=title, category=category,
                                                       incident_id=incident_id, tag=tag)


@tool
@handle_tool_errors
def search_knowledge_base_tool(title: Optional[str] = None, category: Optional[str] = None,
                          incident_id: Optional[str] = None, tag: Optional[str] = None) -> list[KnowledgeBase]:
    """Searches knowledge base articles by optional title, category, related incident ID, or tag.
    At least one filter must be provided. Use count_knowledge_base_articles first to check result-set size.
    Returns matching KB articles that can help resolve recurring or known issues.
    """
    log.info(f"Tool invoked: search_knowledge_base_tool(title={title}, category={category}, incident={incident_id}, tag={tag})")
    if title:
        title = validators.validate_not_empty(title, "title")
    if category:
        category = validators.validate_not_empty(category, "category")
    if incident_id:
        incident_id = validators.validate_id_format(incident_id, "incident_id")
    if tag:
        tag = validators.validate_not_empty(tag, "tag")

    if not any([title, category, incident_id, tag]):
        raise ValueError("At least one search parameter must be provided.")

    results: list[KnowledgeBase] = []

    if title:
        results = kb_repository.search_knowledge_base_by_title(title)
    if category:
        cat_results = kb_repository.search_knowledge_base_by_category(category)
        results = _intersect(results, cat_results) if results else cat_results
    if tag:
        tag_results = kb_repository.search_knowledge_base_by_tag(tag)
        results = _intersect(results, tag_results) if results else tag_results
    if incident_id:
        results = [kb for kb in results if kb.Incident_id and kb.Incident_id == incident_id] if results else []

    if not results:
        # ToolNode converts this into a message the LLM can understand.
        # The KB agent can then ask a clarifying question instead of crashing.
        raise ValueError("No knowledge base articles found for your query. Please ask the user to clarify their input or check your spelling.")

    return results


def _intersect(a: list[KnowledgeBase], b: list[KnowledgeBase]) -> list[KnowledgeBase]:
    ids = {kb.id for kb in b}
    return [kb for kb in a if kb.id in ids]
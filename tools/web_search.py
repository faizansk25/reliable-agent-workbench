"""Web search tool."""


def web_search(query: str, max_results: int = 5) -> list:
    """Search the web (placeholder)."""
    return [{"title": f"Result {i}", "url": f"https://example.com/{i}", "snippet": f"About {query}"} for i in range(max_results)]

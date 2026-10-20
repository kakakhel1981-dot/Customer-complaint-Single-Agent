"""Optional web search integration placeholder.

MVP behavior: web search is intentionally not enabled. This avoids sending internal
ticket details to an external search provider and prevents unverified web instructions
from overriding internal KT.

To add web search later, select an approved search provider, send only a sanitized
general query, and clearly label the results as external.
"""

def search_web(query: str):
    raise NotImplementedError(
        "External web search is not enabled in the MVP. Configure an approved provider before enabling it."
    )

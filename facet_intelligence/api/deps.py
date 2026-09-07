"""FastAPI dependencies."""

from facet_intelligence.inventory.store import ListingStore

_store: ListingStore | None = None


def get_listing_store() -> ListingStore:
    global _store
    if _store is None:
        _store = ListingStore()
    return _store


def set_listing_store(store: ListingStore | None) -> None:
    """Override store (tests). Pass None to reset to default lazy pool."""
    global _store
    _store = store

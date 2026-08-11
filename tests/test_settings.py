import pytest
from pydantic import ValidationError

from dewey_mcp.settings import Settings


def test_image_search_index_name_is_required() -> None:
    with pytest.raises(ValidationError) as exc_info:
        Settings(
            azure_search_endpoint="https://example.search.windows.net",
            azure_search_index_name="archive",
            azure_search_semantic_configuration="semantic",
            azure_search_api_key="secret",
        )

    assert "AZURE_IMAGE_SEARCH_INDEX_NAME" in str(exc_info.value)

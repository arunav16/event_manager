# tests/test_schemas/test_user_schemas_urls.py
import pytest
from pydantic import ValidationError
from app.schemas.user_schemas import UserBase

valid_urls = [
    "http://example.com/image.png",
    "https://example.com/profile",
    None
]

invalid_urls = [
    "ftp://example.com/file.txt",
    "just-a-string",
    "http//missing-colon.com",
    "https//missing-colon.com"
]

@pytest.mark.parametrize("field", ["profile_picture_url", "linkedin_profile_url", "github_profile_url"])
@pytest.mark.parametrize("url", valid_urls + [None])
def test_url_fields_accept_valid(field, url, user_base_data):
    data = user_base_data.copy()
    data[field] = url
    user = UserBase(**data)
    assert (str(getattr(user, field)) if getattr(user, field) else None) == url


@pytest.mark.parametrize("field", ["profile_picture_url", "linkedin_profile_url", "github_profile_url"])
@pytest.mark.parametrize("url", invalid_urls)
def test_url_fields_reject_invalid(field, url, user_base_data):
    data = user_base_data.copy()
    data[field] = url
    with pytest.raises(ValidationError) as exc:
        UserBase(**data)
    # Assert the error is about an invalid URL
    assert "URL" in str(exc.value)

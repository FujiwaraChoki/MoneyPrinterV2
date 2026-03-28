import json
import os
import pytest
from unittest.mock import patch, MagicMock


def test_get_token_path_returns_mp_directory():
    """Token file should live in .mp/ directory."""
    with patch("youtube_auth.ROOT_DIR", "/fake/root"):
        import youtube_auth

        youtube_auth.ROOT_DIR = "/fake/root"
        result = youtube_auth.get_token_path()
        assert result == "/fake/root/.mp/youtube_oauth_token.json"


def test_load_credentials_raises_when_no_token_file(tmp_path):
    """Should raise FileNotFoundError when token file doesn't exist."""
    import youtube_auth

    youtube_auth.ROOT_DIR = str(tmp_path)
    os.makedirs(tmp_path / ".mp", exist_ok=True)

    with pytest.raises(FileNotFoundError, match="Run.*auth_youtube.py"):
        youtube_auth.load_credentials()


def test_load_credentials_returns_credentials_from_token_file(tmp_path):
    """Should load and return credentials from saved token file."""
    import youtube_auth

    youtube_auth.ROOT_DIR = str(tmp_path)
    mp_dir = tmp_path / ".mp"
    mp_dir.mkdir()

    token_data = {
        "token": "fake-access-token",
        "refresh_token": "fake-refresh-token",
        "token_uri": "https://oauth2.googleapis.com/token",
        "client_id": "fake-client-id",
        "client_secret": "fake-client-secret",
        "scopes": ["https://www.googleapis.com/auth/youtube.upload"],
    }
    (mp_dir / "youtube_oauth_token.json").write_text(json.dumps(token_data))

    with patch("youtube_auth.Credentials") as MockCreds:
        mock_creds_instance = MagicMock()
        mock_creds_instance.valid = True
        MockCreds.from_authorized_user_info.return_value = mock_creds_instance

        creds = youtube_auth.load_credentials()
        assert creds == mock_creds_instance
        MockCreds.from_authorized_user_info.assert_called_once()


def test_load_credentials_refreshes_expired_token(tmp_path):
    """Should refresh credentials when token is expired but refresh token exists."""
    import youtube_auth

    youtube_auth.ROOT_DIR = str(tmp_path)
    mp_dir = tmp_path / ".mp"
    mp_dir.mkdir()

    token_data = {
        "token": "expired-token",
        "refresh_token": "fake-refresh-token",
        "token_uri": "https://oauth2.googleapis.com/token",
        "client_id": "fake-client-id",
        "client_secret": "fake-client-secret",
        "scopes": ["https://www.googleapis.com/auth/youtube.upload"],
    }
    (mp_dir / "youtube_oauth_token.json").write_text(json.dumps(token_data))

    with patch("youtube_auth.Credentials") as MockCreds:
        mock_creds_instance = MagicMock()
        mock_creds_instance.valid = False
        mock_creds_instance.expired = True
        mock_creds_instance.refresh_token = "fake-refresh-token"
        mock_creds_instance.to_json.return_value = json.dumps(token_data)
        MockCreds.from_authorized_user_info.return_value = mock_creds_instance

        creds = youtube_auth.load_credentials()
        mock_creds_instance.refresh.assert_called_once()


def test_build_youtube_service_returns_service():
    """Should return a YouTube API service object."""
    import youtube_auth

    mock_creds = MagicMock()
    with patch("youtube_auth.build") as mock_build:
        mock_build.return_value = MagicMock()
        service = youtube_auth.build_youtube_service(mock_creds)
        mock_build.assert_called_once_with("youtube", "v3", credentials=mock_creds)
        assert service is not None

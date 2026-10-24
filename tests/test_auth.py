import jwt
import time
from unittest.mock import patch, MagicMock

from index import is_internal_ip, authenticate


class TestIsInternalIp:
    def test_192_168_1_prefix(self):
        assert is_internal_ip("192.168.1.100") is True

    def test_172_prefix(self):
        assert is_internal_ip("172.18.0.1") is True

    def test_127_prefix(self):
        assert is_internal_ip("127.0.0.1") is True

    def test_192_168_65_prefix(self):
        assert is_internal_ip("192.168.65.1") is True

    def test_external_ip(self):
        assert is_internal_ip("8.8.8.8") is False

    def test_192_168_2_is_external(self):
        """192.168.2.x does not match the 192.168.1. prefix."""
        assert is_internal_ip("192.168.2.1") is False

    def test_172_broad_match(self):
        """Bug: 172. prefix matches all 172.x.x.x, not just RFC 1918 172.16-31."""
        assert is_internal_ip("172.217.0.1") is True


class TestAuthenticate:
    def test_internal_ip_bypasses_auth(self, mock_websocket):
        assert authenticate(mock_websocket) is True

    def test_external_ip_no_token_rejected(self, external_websocket):
        assert authenticate(external_websocket) is False

    @patch("index.Config")
    def test_valid_jwt_accepted(self, mock_cfg, external_websocket):
        mock_cfg.JWT_SECRET = "test-secret"
        token = jwt.encode(
            {"exp": time.time() + 3600},
            "test-secret",
            algorithm="HS256",
        )
        external_websocket.path = f"/?token={token}"
        assert authenticate(external_websocket) is True

    @patch("index.Config")
    def test_expired_jwt_rejected(self, mock_cfg, external_websocket):
        mock_cfg.JWT_SECRET = "test-secret"
        token = jwt.encode(
            {"exp": time.time() - 3600},
            "test-secret",
            algorithm="HS256",
        )
        external_websocket.path = f"/?token={token}"
        assert authenticate(external_websocket) is False

    @patch("index.Config")
    def test_invalid_jwt_rejected(self, mock_cfg, external_websocket):
        mock_cfg.JWT_SECRET = "test-secret"
        token = jwt.encode(
            {"exp": time.time() + 3600},
            "wrong-secret",
            algorithm="HS256",
        )
        external_websocket.path = f"/?token={token}"
        assert authenticate(external_websocket) is False

    def test_empty_token_param_rejected(self, external_websocket):
        external_websocket.path = "/?token="
        assert authenticate(external_websocket) is False

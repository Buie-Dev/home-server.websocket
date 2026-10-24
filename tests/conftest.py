from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.fixture(autouse=True)
def mock_config():
    with patch("config.config.Config") as cfg:
        cfg.MQTT_BROKER = "localhost"
        cfg.JWT_SECRET = "test-secret"
        cfg.DEVICE_NAME = "test-device"
        yield cfg


@pytest.fixture
def mock_mqtt_client():
    client = MagicMock()
    client.subscribe = MagicMock()
    client.publish = MagicMock()
    return client


@pytest.fixture
def mock_websocket():
    ws = AsyncMock()
    ws.remote_address = ("192.168.1.50", 12345)
    ws.path = "/"
    ws.send = AsyncMock()
    ws.close = AsyncMock()
    return ws


@pytest.fixture
def external_websocket():
    ws = AsyncMock()
    ws.remote_address = ("8.8.8.8", 12345)
    ws.path = "/"
    ws.send = AsyncMock()
    ws.close = AsyncMock()
    return ws

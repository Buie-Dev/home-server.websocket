import json
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

import index
from index import websocket_handler, broadcast_message


class TestBroadcastMessage:
    @pytest.mark.asyncio
    async def test_broadcasts_to_all_clients(self):
        ws1 = AsyncMock()
        ws2 = AsyncMock()
        index.websocket_clients = {ws1, ws2}

        await broadcast_message("current", "payload")

        ws1.send.assert_called_once()
        ws2.send.assert_called_once()
        sent = json.loads(ws1.send.call_args[0][0])
        assert sent["topic"] == "current"
        assert sent["message"] == "payload"

    @pytest.mark.asyncio
    async def test_no_clients_does_not_raise(self):
        index.websocket_clients = set()
        await broadcast_message("current", "payload")


class TestWebsocketHandler:
    @pytest.mark.asyncio
    @patch("index.authenticate", return_value=False)
    async def test_unauthorized_client_closed(self, mock_auth, external_websocket):
        await websocket_handler(external_websocket)

        external_websocket.close.assert_called_once_with(1008, "Unauthorized")
        assert external_websocket not in index.websocket_clients

    @pytest.mark.asyncio
    @patch("index.mqtt_client")
    @patch("index.authenticate", return_value=True)
    async def test_replays_cached_state_on_connect(self, mock_auth, mock_mqtt, mock_websocket):
        index.CURRENT_STATE = json.dumps([{"id": 1, "state": 1}])
        index.PRIORITY_QUEUE = json.dumps([{"id": "abc", "zone": 1}])
        index.websocket_clients = set()

        # Simulate empty message stream (client connects then disconnects)
        mock_websocket.__aiter__ = lambda self: aiter([])

        await websocket_handler(mock_websocket)

        # Should have sent two replay messages
        assert mock_websocket.send.call_count == 2
        first_sent = json.loads(mock_websocket.send.call_args_list[0][0][0])
        assert first_sent["topic"] == "current"
        second_sent = json.loads(mock_websocket.send.call_args_list[1][0][0])
        assert second_sent["topic"] == "priorityQueue"

    @pytest.mark.asyncio
    @patch("index.mqtt_client")
    @patch("index.authenticate", return_value=True)
    async def test_no_replay_when_state_is_none(self, mock_auth, mock_mqtt, mock_websocket):
        index.CURRENT_STATE = None
        index.PRIORITY_QUEUE = None
        index.websocket_clients = set()

        mock_websocket.__aiter__ = lambda self: aiter([])

        await websocket_handler(mock_websocket)

        mock_websocket.send.assert_not_called()

    @pytest.mark.asyncio
    @patch("index.mqtt_client")
    @patch("index.authenticate", return_value=True)
    async def test_request_published_to_mqtt(self, mock_auth, mock_mqtt, mock_websocket):
        index.CURRENT_STATE = None
        index.PRIORITY_QUEUE = None
        index.websocket_clients = set()

        message = json.dumps({"topic": "request", "message": {"zone": 1, "duration": 300}})
        mock_websocket.__aiter__ = lambda self: aiter([message])

        await websocket_handler(mock_websocket)

        mock_mqtt.publish.assert_called_once_with(
            "irrigation/request",
            json.dumps({"zone": 1, "duration": 300}),
        )

    @pytest.mark.asyncio
    @patch("index.mqtt_client")
    @patch("index.authenticate", return_value=True)
    async def test_stop_published_to_mqtt(self, mock_auth, mock_mqtt, mock_websocket):
        index.CURRENT_STATE = None
        index.PRIORITY_QUEUE = None
        index.websocket_clients = set()

        message = json.dumps({"topic": "stop", "message": {"id": "abc"}})
        mock_websocket.__aiter__ = lambda self: aiter([message])

        await websocket_handler(mock_websocket)

        mock_mqtt.publish.assert_called_once_with(
            "irrigation/stop",
            json.dumps({"id": "abc"}),
        )

    @pytest.mark.asyncio
    @patch("index.mqtt_client")
    @patch("index.authenticate", return_value=True)
    async def test_stop_all_published_to_mqtt(self, mock_auth, mock_mqtt, mock_websocket):
        index.CURRENT_STATE = None
        index.PRIORITY_QUEUE = None
        index.websocket_clients = set()

        message = json.dumps({"topic": "stopAll", "message": {}})
        mock_websocket.__aiter__ = lambda self: aiter([message])

        await websocket_handler(mock_websocket)

        mock_mqtt.publish.assert_called_once_with(
            "irrigation/stopAll",
            json.dumps({}),
        )

    @pytest.mark.asyncio
    @patch("index.mqtt_client")
    @patch("index.authenticate", return_value=True)
    async def test_healthcheck_request_published_to_mqtt(
        self, mock_auth, mock_mqtt, mock_websocket
    ):
        index.CURRENT_STATE = None
        index.PRIORITY_QUEUE = None
        index.websocket_clients = set()

        message = json.dumps({"topic": "healthcheck/request", "message": {}})
        mock_websocket.__aiter__ = lambda self: aiter([message])

        await websocket_handler(mock_websocket)

        mock_mqtt.publish.assert_called_once_with(
            "healthcheck/request",
            json.dumps({}),
        )

    @pytest.mark.asyncio
    @patch("index.mqtt_client")
    @patch("index.authenticate", return_value=True)
    async def test_rowing_topic_broadcast_not_mqtt(self, mock_auth, mock_mqtt, mock_websocket):
        index.CURRENT_STATE = None
        index.PRIORITY_QUEUE = None
        index.websocket_clients = set()

        ws_peer = AsyncMock()
        index.websocket_clients.add(ws_peer)

        message = json.dumps({"topic": "rowing/start", "message": {"raceId": 1}})
        mock_websocket.__aiter__ = lambda self: aiter([message])

        await websocket_handler(mock_websocket)

        # Rowing topics are broadcast, not published to MQTT
        mock_mqtt.publish.assert_not_called()
        ws_peer.send.assert_called_once()
        sent = json.loads(ws_peer.send.call_args[0][0])
        assert sent["topic"] == "rowing/start"

    @pytest.mark.asyncio
    @patch("index.mqtt_client")
    @patch("index.authenticate", return_value=True)
    async def test_client_removed_on_disconnect(self, mock_auth, mock_mqtt, mock_websocket):
        index.CURRENT_STATE = None
        index.PRIORITY_QUEUE = None
        index.websocket_clients = set()

        mock_websocket.__aiter__ = lambda self: aiter([])

        await websocket_handler(mock_websocket)

        assert mock_websocket not in index.websocket_clients


async def aiter(items):
    for item in items:
        yield item

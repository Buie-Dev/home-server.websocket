import asyncio
import json
from unittest.mock import MagicMock, patch

import index
from index import on_connect, on_message


class TestOnConnect:
    def test_subscribes_to_all_topics(self, mock_mqtt_client):
        on_connect(mock_mqtt_client, None, None, 0)

        subscribed_topics = [call[0][0] for call in mock_mqtt_client.subscribe.call_args_list]
        assert "irrigation/currentState" in subscribed_topics
        assert "irrigation/queue" in subscribed_topics
        assert "healthcheck/response" in subscribed_topics
        assert "healthcheck/request" in subscribed_topics
        assert "irrigation/liveFlow" in subscribed_topics
        assert mock_mqtt_client.subscribe.call_count == 5


class TestOnMessage:
    def _make_msg(self, topic, payload):
        msg = MagicMock()
        msg.topic = topic
        msg.payload = payload.encode() if isinstance(payload, str) else payload
        return msg

    @patch("index.broadcast_message")
    def test_current_state_cached_and_broadcast(self, mock_broadcast, mock_mqtt_client):
        index.CURRENT_STATE = None
        loop = asyncio.new_event_loop()
        index.loop = loop
        payload = json.dumps([{"id": 1, "state": 0, "subzones": []}])
        msg = self._make_msg("irrigation/currentState", payload)

        on_message(mock_mqtt_client, None, msg)

        assert index.CURRENT_STATE == payload
        mock_broadcast.assert_called_once_with("current", payload)
        loop.close()

    @patch("index.broadcast_message")
    def test_priority_queue_cached_and_broadcast(self, mock_broadcast, mock_mqtt_client):
        index.PRIORITY_QUEUE = None
        loop = asyncio.new_event_loop()
        index.loop = loop
        payload = json.dumps([{"id": "abc", "duration": 300, "zone": 1, "priority": 1}])
        msg = self._make_msg("irrigation/queue", payload)

        on_message(mock_mqtt_client, None, msg)

        assert index.PRIORITY_QUEUE == payload
        mock_broadcast.assert_called_once_with("priorityQueue", payload)
        loop.close()

    @patch("index.broadcast_message")
    def test_healthcheck_response_broadcast(self, mock_broadcast, mock_mqtt_client):
        loop = asyncio.new_event_loop()
        index.loop = loop
        payload = json.dumps({"device": "garden-controller"})
        msg = self._make_msg("healthcheck/response", payload)

        on_message(mock_mqtt_client, None, msg)

        mock_broadcast.assert_called_once_with("healthcheck/response", payload)
        loop.close()

    @patch("index.broadcast_message")
    def test_live_flow_broadcast(self, mock_broadcast, mock_mqtt_client):
        loop = asyncio.new_event_loop()
        index.loop = loop
        payload = json.dumps({"litres": 1.5})
        msg = self._make_msg("irrigation/liveFlow", payload)

        on_message(mock_mqtt_client, None, msg)

        mock_broadcast.assert_called_once_with("liveFlow", payload)
        loop.close()

    @patch("index.Config")
    @patch("index.broadcast_message")
    def test_healthcheck_request_publishes_response(
        self, mock_broadcast, mock_cfg, mock_mqtt_client
    ):
        mock_cfg.DEVICE_NAME = "test-device"
        msg = self._make_msg("healthcheck/request", "ping")

        on_message(mock_mqtt_client, None, msg)

        mock_mqtt_client.publish.assert_called_once()
        call_args = mock_mqtt_client.publish.call_args
        assert call_args[0][0] == "healthcheck/response"
        published = json.loads(call_args[0][1])
        assert published["device"] == "test-device"
        mock_broadcast.assert_not_called()

    @patch("index.broadcast_message")
    def test_unknown_topic_ignored(self, mock_broadcast, mock_mqtt_client):
        loop = asyncio.new_event_loop()
        index.loop = loop
        msg = self._make_msg("some/unknown/topic", "data")

        on_message(mock_mqtt_client, None, msg)

        mock_broadcast.assert_not_called()
        loop.close()

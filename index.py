import asyncio
import json
import time
from urllib.parse import parse_qs, urlparse

import jwt
import paho.mqtt.client as mqtt
import websockets

from config.config import Config
from ObjectTypes import CurrentState, PriorityQueue

INTERNAL_PREFIXES = ("192.168.1.", "172.", "127.", "192.168.65.")


def is_internal_ip(ip: str) -> bool:
    return any(ip.startswith(prefix) for prefix in INTERNAL_PREFIXES)


def authenticate(websocket) -> bool:
    ip = websocket.remote_address[0]
    if is_internal_ip(ip):
        return True

    parsed = urlparse(websocket.path)
    params = parse_qs(parsed.query)
    token_list = params.get("token", [])
    if not token_list:
        return False

    try:
        jwt.decode(token_list[0], Config.JWT_SECRET, algorithms=["HS256"])
        return True
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return False


# MQTT Configuration
CURRENT_STATE: CurrentState = None
PRIORITY_QUEUE: PriorityQueue = None


MQTT_PORT = 1883
MQTT_TOPIC_PUB = "irrigation/request"  # Topic to publish messages
MQTT_TOPIC_STOP_PUB = "irrigation/stop"
MQTT_TOPIC_SUB_IRRIGATION_STOP_ALL = "irrigation/stopAll"
MQTT_TOPIC_SUB_CURRENT_STATE = "irrigation/currentState"  # Topic to publish messages
MQTT_TOPIC_SUB_PRIORITY_QUEUE_STATE = "irrigation/queue"
MQTT_TOPIC_HEALTHCHECK_REQUEST = "healthcheck/request"
MQTT_TOPIC_HEALTHCHECK_RESPONSE = "healthcheck/response"
MQTT_TOPIC_LIVE_FLOW = "irrigation/liveFlow"

WEBBROKER_TOPIC_CURRENT_STATE = "current"
WEBBROKER_TOPIC_PRIORITY_QUEUE = "priorityQueue"
WEBBROKER_TOPIC_HEALTHCHECK_RESPONSE = "healthcheck/response"
WEBBROKER_TOPIC_LIVE_FLOW = "liveFlow"


# Store connected WebSocket clients
websocket_clients = set()

# Event loop reference, set in __main__ for thread-safe MQTT→asyncio bridging
loop = None

# Initialize MQTT Client
mqtt_client = mqtt.Client()


# WebSocket Broadcast Function
async def broadcast_message(topic: str, message: object):
    """Send a message to all connected WebSocket clients."""
    if websocket_clients:
        data = json.dumps({"topic": topic, "message": message})
        await asyncio.gather(*(ws.send(data) for ws in websocket_clients))


# MQTT Callbacks
def on_connect(client, userdata, flags, rc):
    client.subscribe(MQTT_TOPIC_SUB_CURRENT_STATE)
    client.subscribe(MQTT_TOPIC_SUB_PRIORITY_QUEUE_STATE)
    client.subscribe(MQTT_TOPIC_HEALTHCHECK_RESPONSE)
    client.subscribe(MQTT_TOPIC_HEALTHCHECK_REQUEST)
    client.subscribe(MQTT_TOPIC_LIVE_FLOW)


def on_message(client, userdata, msg):
    """Handle incoming MQTT messages and forward them to WebSocket clients."""
    global CURRENT_STATE
    global PRIORITY_QUEUE

    topic = msg.topic
    message = msg.payload.decode()
    web_socket_topic = None

    if topic == MQTT_TOPIC_SUB_CURRENT_STATE:
        CURRENT_STATE = message
        web_socket_topic = WEBBROKER_TOPIC_CURRENT_STATE
    elif topic == MQTT_TOPIC_SUB_PRIORITY_QUEUE_STATE:
        PRIORITY_QUEUE = message
        web_socket_topic = WEBBROKER_TOPIC_PRIORITY_QUEUE
    elif topic == MQTT_TOPIC_HEALTHCHECK_RESPONSE:
        web_socket_topic = WEBBROKER_TOPIC_HEALTHCHECK_RESPONSE
    elif topic == MQTT_TOPIC_LIVE_FLOW:
        web_socket_topic = WEBBROKER_TOPIC_LIVE_FLOW
    elif topic == MQTT_TOPIC_HEALTHCHECK_REQUEST:
        payload = json.dumps({"device": Config.DEVICE_NAME})
        client.publish(MQTT_TOPIC_HEALTHCHECK_RESPONSE, payload)
        return

    if web_socket_topic is not None:
        asyncio.run_coroutine_threadsafe(broadcast_message(web_socket_topic, message), loop)


mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message


# WebSocket Server
async def websocket_handler(websocket):
    """Handle new WebSocket connections."""
    if not authenticate(websocket):
        await websocket.close(1008, "Unauthorized")
        return

    websocket_clients.add(websocket)
    if CURRENT_STATE is not None:
        data = json.dumps({"topic": WEBBROKER_TOPIC_CURRENT_STATE, "message": CURRENT_STATE})
        await websocket.send(data)
    if PRIORITY_QUEUE is not None:
        data = json.dumps({"topic": WEBBROKER_TOPIC_PRIORITY_QUEUE, "message": PRIORITY_QUEUE})
        await websocket.send(data)

    try:
        async for message in websocket:
            data = json.loads(message)
            topic = data.get("topic")
            payload = json.dumps(data.get("message"))
            if topic == "request":
                mqtt_client.publish(MQTT_TOPIC_PUB, payload)
            elif topic == "stop":
                mqtt_client.publish(MQTT_TOPIC_STOP_PUB, payload)
            elif topic == "stopAll":
                mqtt_client.publish(MQTT_TOPIC_SUB_IRRIGATION_STOP_ALL, payload)
            elif topic == MQTT_TOPIC_HEALTHCHECK_REQUEST:
                mqtt_client.publish(MQTT_TOPIC_HEALTHCHECK_REQUEST, payload)
            elif topic.startswith("rowing/"):
                await broadcast_message(topic, data.get("message"))

    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        websocket_clients.remove(websocket)


async def start_websocket_server():
    """Start WebSocket server on port 8765."""
    async with websockets.serve(websocket_handler, "0.0.0.0", 8765):
        await asyncio.Future()  # Keep running


# Run everything
if __name__ == "__main__":
    while True:
        try:
            mqtt_client.connect(Config.MQTT_BROKER, MQTT_PORT, 60)
            break
        except Exception as e:
            print(f"MQTT connect failed: {e} — retrying in 5s...")
            time.sleep(5)
    mqtt_client.loop_start()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start_websocket_server())

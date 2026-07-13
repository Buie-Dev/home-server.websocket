import asyncio
import websockets
import json
import jwt
import time
import paho.mqtt.client as mqtt
from urllib.parse import urlparse, parse_qs
from ObjectTypes import PriorityQueue, CurrentState
from config.config import Config

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

# Initialize MQTT Client
mqtt_client = mqtt.Client()


# WebSocket Broadcast Function
async def broadcast_message(topic: str, message: object):
    """Send a message to all connected WebSocket clients."""
    if websocket_clients:
        data = json.dumps({"topic": topic, "message": message})
        await asyncio.wait([ws.send(data) for ws in websocket_clients])


# MQTT Callbacks
def on_connect(client, userdata, flags, rc):
    global CURRENT_STATE
    print(f"Connected to MQTT Broker with result code {rc}")
    client.subscribe(MQTT_TOPIC_SUB_CURRENT_STATE)
    client.subscribe(MQTT_TOPIC_SUB_PRIORITY_QUEUE_STATE)
    client.subscribe(MQTT_TOPIC_HEALTHCHECK_RESPONSE)
    client.subscribe(MQTT_TOPIC_HEALTHCHECK_REQUEST)
    client.subscribe(MQTT_TOPIC_LIVE_FLOW)


def on_message(client, userdata, msg):
    global CURRENT_STATE
    global PRIORITY_QUEUE
    """Handle incoming MQTT messages and forward them to WebSocket clients."""
    print("onMessage")

    topic = msg.topic
    message = msg.payload.decode()
    print(f"MQTT Message Received: Topic {topic}: {message}")
    web_socket_topic = ""

    if topic == MQTT_TOPIC_SUB_CURRENT_STATE:
        CURRENT_STATE = msg.payload.decode()
        web_socket_topic = WEBBROKER_TOPIC_CURRENT_STATE
    elif topic == MQTT_TOPIC_SUB_PRIORITY_QUEUE_STATE:
        PRIORITY_QUEUE = msg.payload.decode()
        web_socket_topic = WEBBROKER_TOPIC_PRIORITY_QUEUE
    elif topic == MQTT_TOPIC_HEALTHCHECK_RESPONSE:
        web_socket_topic = WEBBROKER_TOPIC_HEALTHCHECK_RESPONSE
    elif topic == MQTT_TOPIC_LIVE_FLOW:
        web_socket_topic = WEBBROKER_TOPIC_LIVE_FLOW
    elif topic == MQTT_TOPIC_HEALTHCHECK_REQUEST:
        payload = json.dumps({"device": Config.DEVICE_NAME})
        client.publish(MQTT_TOPIC_HEALTHCHECK_RESPONSE, payload)
        return

    print(f"Boradcasting: Topic {web_socket_topic}: {message}")
    asyncio.run(broadcast_message(web_socket_topic, message))


mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message


# WebSocket Server
async def websocket_handler(websocket):
    """Handle new WebSocket connections."""
    if not authenticate(websocket):
        print(f"Unauthorized WebSocket connection from {websocket.remote_address}")
        await websocket.close(1008, "Unauthorized")
        return

    print("Here -------------")
    websocket_clients.add(websocket)
    print(f"New WebSocket Connection: {websocket.remote_address}")
    print(CURRENT_STATE)
    print(PRIORITY_QUEUE)
    if CURRENT_STATE != None:
        data = json.dumps(
            {"topic": WEBBROKER_TOPIC_CURRENT_STATE, "message": CURRENT_STATE}
        )
        await websocket.send(data)
    if PRIORITY_QUEUE != None:
        data = json.dumps(
            {"topic": WEBBROKER_TOPIC_PRIORITY_QUEUE, "message": PRIORITY_QUEUE}
        )
        await websocket.send(data)

    try:
        async for message in websocket:
            data = json.loads(message)
            print(f"Received from WebSocket: {message}")
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
        print(f"WebSocket Disconnected: {websocket.remote_address}")
    finally:
        print("DISONCECEOINC")
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
    mqtt_client.loop_start()  # Start MQTT in background
    asyncio.run(start_websocket_server())  # Start WebSocket server

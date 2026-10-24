import os

from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()


class Config:
    MQTT_BROKER = os.getenv("MQTT_BROKER")
    JWT_SECRET = os.getenv("JWT_SECRET")
    DEVICE_NAME = os.getenv("DEVICE_NAME", "irrigation_webserver")

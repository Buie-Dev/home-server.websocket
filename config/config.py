import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()


class Config:
    MQTT_BROKER = os.getenv("MQTT_BROKER")  # Default to "localhost" if not found

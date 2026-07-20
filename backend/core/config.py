from dotenv import load_dotenv
import os

load_dotenv()

APP_NAME = "Supply Prescript API"
APP_VERSION = "1.0.0"

HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", 8000))
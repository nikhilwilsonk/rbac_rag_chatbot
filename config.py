import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

DATA_DIR = Path("data")
USER_DB_PATH = DATA_DIR / "users.json"
DOCUMENTS_DIR = DATA_DIR / "documents"
SESSION_DB_PATH = DATA_DIR / "sessions.json"
VECTOR_DB_PATH = DATA_DIR / "vectordb"

DATA_DIR.mkdir(exist_ok=True)
DOCUMENTS_DIR.mkdir(exist_ok=True)
VECTOR_DB_PATH.mkdir(exist_ok=True)

ROLES = ["finance", "engineering", "admin"]

SESSION_EXPIRY = 60 * 60 #s

RATE_LIMIT_WINDOW = 60  # s
RATE_LIMIT_MAX_REQUESTS = 10  # max requests per window

def get_openai_api_key():
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        api_key = input("Please enter your OpenAI API key: ").strip()
        os.environ["OPENAI_API_KEY"] = api_key
    return api_key

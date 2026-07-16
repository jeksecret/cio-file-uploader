import os
from functools import lru_cache
from dotenv import load_dotenv
from notion_client import Client

load_dotenv()

@lru_cache(maxsize=1)
def get_notion() -> Client:
    token = os.getenv("NOTION_API_TOKEN")

    if token is None:
        raise RuntimeError("Environment variable NOTION_API_TOKEN is not set.")

    return Client(auth=token)
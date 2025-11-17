import os
from utils.emojis import *
from motor.motor_asyncio import AsyncIOMotorClient


_uri = os.getenv("MONGO_URL")
_uri = _uri if str(_uri or "").startswith(("mongodb://", "mongodb+srv://")) else "mongodb://localhost:27017"
Mongos = AsyncIOMotorClient(_uri)
DB = Mongos["astro"]
Configuration = DB["Config"]


async def ModuleCheck(id, module: str):
    config = await Configuration.find_one({"_id": id})
    if config is None:
        config = {"_id": id, "Modules": {}}
    elif "Modules" not in config:
        config["Modules"] = {}

    if bool(config.get("Modules", {}).get(module)):
        return True
    else:
        return False

# my_mcp_project/my_mcp_app/server.py
import os
from mcp.server.fastmcp import FastMCP, Context
from mcp.server.fastmcp.prompts import base as prompt_base

from contextlib import contextmanager # Note: not asynccontextmanager for sync lifespan
from collections.abc import Iterator # Note: not AsyncIterator
from dataclasses import dataclass
import asyncio # Still useful for running sync code in threads

import pymongo # Standard synchronous MongoDB driver
from bson import ObjectId

# --- Configuration ---
MONGODB_URI = os.environ.get("MONGODB_URI", "mongodb://localhost:27017")
DATABASE_NAME = "my_mcp_db_sync" # Changed name to avoid confusion with async version

# --- Server State & Lifespan Management (Synchronous) ---
@dataclass
class AppContext:
    db: pymongo.database.Database
    mongo_client: pymongo.MongoClient

@contextmanager # Synchronous context manager
def app_lifespan_sync(server: FastMCP) -> Iterator[AppContext]:
    """Manage MongoDB connection lifecycle (synchronous)."""
    print("MCP Server (Sync): Lifespan starting up...")
    print(f"Attempting to connect to MongoDB at {MONGODB_URI}...")
    
    mongo_client = pymongo.MongoClient(MONGODB_URI)
    # Verify connection by trying to get server info (or ping)
    try:
        mongo_client.admin.command('ping')
        print(f"Successfully connected to MongoDB, database: '{DATABASE_NAME}'.")
    except pymongo.errors.ConnectionFailure as e:
        print(f"Failed to connect to MongoDB: {e}")
        raise # Propagate error to stop server startup

    db = mongo_client[DATABASE_NAME]
    
    try:
        yield AppContext(db=db, mongo_client=mongo_client)
    finally:
        print("MCP Server (Sync): Lifespan shutting down...")
        if mongo_client:
            mongo_client.close()
            print("MongoDB connection closed.")
        print("MCP Server (Sync): Lifespan shutdown complete.")

# Create an MCP server
# FastMCP can handle synchronous lifespan managers
mcp = FastMCP(
    "PyMongoDemoServer",
    lifespan=app_lifespan_sync, # Using the synchronous lifespan
    dependencies=["pymongo"]
)

# --- Helper to run sync DB calls in async context ---
# This is crucial to avoid blocking the event loop with pymongo calls
async def run_sync(func, *args, **kwargs):
    if asyncio.get_running_loop().is_running(): # Python 3.7+
        return await asyncio.to_thread(func, *args, **kwargs) # Python 3.9+
    else: # Fallback for environments where to_thread might not be ideal or for direct sync calls
        return func(*args, **kwargs)


# --- Resources (Data Endpoints) ---
# Handlers are still async because MCP expects them to be potentially async
@mcp.resource("app://info")
async def get_app_info(ctx: Context) -> dict:
    """Get general information about the app and DB status."""
    app_ctx: AppContext = ctx.request_context.lifespan_context
    db_status = "Connected (assuming lifespan succeeded)"
    
    def check_connection_sync():
        try:
            app_ctx.mongo_client.admin.command('ping')
            return "Connected"
        except pymongo.errors.ConnectionFailure:
            return "Connection Error"

    db_status = await run_sync(check_connection_sync)
            
    return {
        "server_name": mcp.name,
        "server_version": "1.0.0",
        "mongodb_uri": MONGODB_URI,
        "database_name": DATABASE_NAME,
        "db_status": db_status
    }

@mcp.resource("mongo://{collection_name}/{item_id}")
async def get_mongo_item(ctx: Context, collection_name: str, item_id: str) -> dict:
    app_ctx: AppContext = ctx.request_context.lifespan_context
    
    def db_call_sync():
        collection = app_ctx.db[collection_name]
        query = {"name": item_id} # Example query
        document = collection.find_one(query)
        if document:
            if isinstance(document.get("_id"), ObjectId):
                document["_id"] = str(document["_id"])
            return {"found": True, "collection": collection_name, "item": document}
        else:
            return {"found": False, "collection": collection_name, "query": query, "message": "Item not found"}
            
    return await run_sync(db_call_sync)


@mcp.resource("mongo://{collection_name}/list_all")
async def list_all_in_collection(ctx: Context, collection_name: str) -> dict:
    app_ctx: AppContext = ctx.request_context.lifespan_context

    def db_call_sync():
        collection = app_ctx.db[collection_name]
        documents_list = []
        # Be careful with find() without limits on large collections
        cursor = collection.find({}).limit(20)
        for doc in cursor:
            if isinstance(doc.get("_id"), ObjectId):
                doc["_id"] = str(doc["_id"])
            documents_list.append(doc)
        return {"collection": collection_name, "count": len(documents_list), "items": documents_list}

    return await run_sync(db_call_sync)

@mcp.resource("mongo://collections")
async def list_mongo_collections(ctx: Context) -> list[str]:
    app_ctx: AppContext = ctx.request_context.lifespan_context
    
    def db_call_sync():
        try:
            return app_ctx.db.list_collection_names()
        except Exception as e:
            return [f"Error listing collections: {str(e)}"]
            
    return await run_sync(db_call_sync)


# --- Tools (Functionality Endpoints) ---
@mcp.tool()
async def add_mongo_item(ctx: Context, collection_name: str, item_data: dict) -> dict:
    app_ctx: AppContext = ctx.request_context.lifespan_context

    def db_call_sync():
        collection = app_ctx.db[collection_name]
        try:
            if not isinstance(item_data, dict):
                return {"success": False, "error": "item_data must be a dictionary"}
            
            result = collection.insert_one(item_data)
            return {
                "success": True,
                "collection": collection_name,
                "inserted_id": str(result.inserted_id)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
            
    return await run_sync(db_call_sync)


@mcp.tool()
async def delete_mongo_item(ctx: Context, collection_name: str, item_name_to_delete: str) -> dict:
    app_ctx: AppContext = ctx.request_context.lifespan_context
    
    def db_call_sync():
        collection = app_ctx.db[collection_name]
        query = {"name": item_name_to_delete}
        try:
            result = collection.delete_one(query)
            if result.deleted_count > 0:
                return {"success": True, "deleted_count": result.deleted_count, "query": query}
            else:
                return {"success": False, "deleted_count": 0, "message": "No item found matching query", "query": query}
        except Exception as e:
            return {"success": False, "error": str(e)}

    return await run_sync(db_call_sync)


# --- Prompts (Unchanged, they don't interact with DB directly) ---
@mcp.prompt()
def generate_summary_request(text_to_summarize: str, max_length: int = 100) -> str:
    return f"Please summarize the following text in under {max_length} words:\n\n{text_to_summarize}"

@mcp.prompt()
def ask_about_mongo_item(collection: str, item_name: str) -> list[prompt_base.Message]:
    return [
        prompt_base.UserMessage(f"Tell me about the item named '{item_name}' in the '{collection}' MongoDB collection."),
    ]

# --- For direct execution ---
if __name__ == "__main__":
    print(f"Attempting to run {mcp.name} server directly...")
    mcp.run()
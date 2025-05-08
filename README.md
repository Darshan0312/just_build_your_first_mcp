# 🚧 Still developing this project. If you're interested, feel free to contribute!

# My Structured MCP Project

This project demonstrates a more structured Model Context Protocol (MCP) server using `FastMCP`.
It includes:
- Lifespan management for initializing and cleaning up resources (like a database connection).
- Resources to expose data.
- Tools to expose functionality.
- Prompts for reusable LLM interactions.

## Project Structure

my_mcp_project/
├── my_mcp_app/ # Main application package
│ ├── init.py # Makes 'my_mcp_app' a Python package
│ ├── server.py # The FastMCP server definition
│ └── fake_database.py # A simple mock database class
└── README.md # This file

## Prerequisites

1.  **Python**: Ensure you have Python 3.8+ installed.
2.  **MCP SDK**: Install the MCP SDK. It's recommended to do this in a virtual environment.
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    pip install mcp-sdk
    ```

## Running the Server

There are a few ways to run this MCP server:

### 1. Development Mode (with MCP Inspector)

This is the recommended way for development and testing. It starts the server and opens the MCP Inspector in your browser, allowing you to interact with your server's tools, resources, and prompts.

Navigate to the `my_mcp_project` directory (the one containing `my_mcp_app` and this `README.md`):

```bash
cd path/to/my_mcp_project
mcp dev my_mcp_app/server.py

---


**To run this:**

1.  Create the directory structure:
    ```bash
    mkdir -p my_mcp_project/my_mcp_app
    cd my_mcp_project
    ```
2.  Save each code block above into its respective file (`my_mcp_app/__init__.py`, `my_mcp_app/fake_database.py`, `my_mcp_app/server.py`, and `README.md`).
3.  Follow the instructions in the `README.md` under "Running the Server", starting with the "Prerequisites".

The `mcp dev my_mcp_app/server.py` command will be the most illustrative as it spins up the MCP Inspector, allowing you to easily test all the defined resources, tools, and prompts. You'll also see the print statements from the lifespan manager and the fake database in your terminal, showing the setup and teardown process.

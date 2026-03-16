# Practice 6: Building an MCP Client

In this task, you'll write an MCP client that connects to your MCP server and discovers its available tools.

## Preparation

1. Confirm that `mcp-client-demo` appears in your account.
2. Clone the repo locally and open it in your editor.

## Write your client script

Create a script called `mcp_client_demo.py` that:

1. **Starts the MCP server** as a subprocess via stdio transport
2. **Initializes a client session** using the MCP SDK
3. **Lists all available tools** exposed by the server
4. **Prints tool details** — name, description, and input schema for each tool

### Implementation steps

```python
# 1. Define StdioServerParameters to launch the MCP server
# 2. Connect via stdio_client and create a ClientSession
# 3. Call session.initialize()
# 4. Call session.list_tools()
# 5. Print each tool's name, description, and input schema
```

### Running the script

```bash
# Run the client demo
uv run python mcp_client_demo.py
```

## Submission checklist

- [ ] `mcp_client_demo.py` exists and is runnable
- [ ] Script connects to the MCP server via stdio
- [ ] Script initializes a client session
- [ ] Script lists and prints all available tools with their schemas

You are working on an MCP server called "git-activity-analyzer". Your task is to write an MCP client script that connects to the server and lists all available tools.

Open `mcp_client_demo.py` and fill in the three TODOs:

1. **TODO 1 — Define server parameters:**
   ```python
   server_params = StdioServerParameters(
       command="uv", args=["run", "server.py"],
   )
   ```

2. **TODO 2 — Connect to the server and initialize the session:**
   Replace the `pass` with:
   ```python
   async with stdio_client(server_params) as (read, write):
       async with ClientSession(read, write) as session:
           await session.initialize()
   ```

3. **TODO 3 — List tools and print their details** (inside the session context):
   ```python
           tool_list = await session.list_tools()
           print(f"Connected to MCP server. Found {len(tool_list.tools)} tools:\n")
           for tool in tool_list.tools:
               print(f"  Tool: {tool.name}")
               if tool.description:
                   print(f"  Description: {tool.description}")
               print(f"  Input schema: {json.dumps(tool.inputSchema, indent=4)}")
               print()
   ```

Make sure there are no TODO comments left. The script should be runnable with `uv run python mcp_client_demo.py`.

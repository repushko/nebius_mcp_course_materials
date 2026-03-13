# Lesson 6: Connecting an AI Agent to Your MCP Server

In this task, you'll connect an AI agent to your MCP server.

## Preparation

1. Confirm that `mcp-agent-demo` appears in your account.
2. Clone the repo locally and open it in your editor.
3. Make sure you have an Anthropic API key (set as `ANTHROPIC_API_KEY` environment variable).

## Write your integration script

Create a script called `mcp_agent_demo.py` that:

1. **Defines tool schemas** that match your MCP server tool(s)
   - At minimum: `analyze_hotspots` (same name + parameters as your server)

2. **Sends a user message** like:
   - `"Which files are risky to change in this repo? Use the available tools."`

3. **Detects the model's tool call** (`tool_use`)

4. **Calls your MCP server** with the tool name + arguments
   - stdio connection (local or Docker command)
   - uses the MCP SDK client if available, or your existing wrapper

5. **Sends the tool result back to the model**

6. **Prints the final answer**

### Implementation steps

```python
# 1. Start the MCP server as a subprocess via stdio
# 2. Initialize the MCP client session
# 3. List available tools from the server
# 4. Convert MCP tool schemas to Anthropic tool format
# 5. Send a message to Claude with the tools
# 6. When Claude responds with tool_use, call the MCP server
# 7. Send the tool result back to Claude
# 8. Print Claude's final analysis
```

### Running the script

```bash
# Set your API key
export ANTHROPIC_API_KEY="your-key-here"

# Run the agent demo (provide a path to any git repo)
uv run python mcp_agent_demo.py /path/to/any/git/repo
```

## Submission checklist

- [ ] `mcp_agent_demo.py` exists and is runnable
- [ ] Script defines tool schemas matching MCP server tools
- [ ] Script sends a user message requesting tool use
- [ ] Script handles `tool_use` responses from the model
- [ ] Script calls the MCP server with tool arguments
- [ ] Script sends tool results back and prints the final answer

# LangChain MCP Integration

**Status**: ✅ Installed & Configured  
**Type**: Model Context Protocol (HTTP)  
**Updated**: 2026-08-18

---

## Overview

Two complementary MCP servers from LangChain documentation are configured for this project:

| Server | URL | Coverage |
|--------|-----|----------|
| `docs-langchain` | `https://docs.langchain.com/mcp` | Conceptual guides, how-tos, tutorials, product docs for LangChain, LangGraph, LangSmith |
| `reference-langchain` | `https://reference.langchain.com/mcp` | API reference: classes, methods, parameters, signatures for all LangChain packages |

---

## Quick Start

### For Claude Code
```bash
# Add both servers to current project
claude mcp add --transport http docs-langchain https://docs.langchain.com/mcp
claude mcp add --transport http reference-langchain https://reference.langchain.com/mcp

# Or add globally (all projects)
claude mcp add --transport http docs-langchain --scope user https://docs.langchain.com/mcp
claude mcp add --transport http reference-langchain --scope user https://reference.langchain.com/mcp
```

### For OpenCode
Already configured in `opencode.json` — MCPs are auto-loaded.

### For Cursor
The MCP configuration is available via `.opencode/.cursor/config.json` (see below).

---

## Configuration Files

### opencode.json Entry
```json
{
  "mcp": [
    {
      "name": "docs-langchain",
      "type": "http",
      "url": "https://docs.langchain.com/mcp",
      "description": "LangChain conceptual guides, how-tos, tutorials, product docs"
    },
    {
      "name": "reference-langchain",
      "type": "http",
      "url": "https://reference.langchain.com/mcp",
      "description": "LangChain API reference: classes, methods, parameters, signatures"
    }
  ]
}
```

### Cursor MCP Config
If using Cursor, create/update `.cursor/config.json`:
```json
{
  "mcpServers": {
    "docs-langchain": {
      "url": "https://docs.langchain.com/mcp"
    },
    "reference-langchain": {
      "url": "https://reference.langchain.com/mcp"
    }
  }
}
```

### Deep Agents Code MCP Config
For Deep Agents Code, create/update `.mcp.json`:
```json
{
  "mcpServers": {
    "docs-langchain": {
      "type": "http",
      "url": "https://docs.langchain.com/mcp"
    },
    "reference-langchain": {
      "type": "http",
      "url": "https://reference.langchain.com/mcp"
    }
  }
}
```

### VS Code MCP Config
For VS Code, update MCP settings:
```json
{
  "servers": {
    "docs-langchain": {
      "url": "https://docs.langchain.com/mcp"
    },
    "reference-langchain": {
      "url": "https://reference.langchain.com/mcp"
    }
  }
}
```

---

## Documentation Index

The LangChain docs are organized into several key sections:

### Core Concepts & How-Tos (Docs Server)
- **Build**: Build agents with LangChain, LangGraph, and Deep Agents
- **LangChain**: Core library documentation (76 pages)
- **LangGraph**: Agent orchestration & persistence (43 pages)
- **LangSmith**: Observability & evaluation platform (449 pages)
- **Deep Agents**: Autonomous coding agents (40 pages)

**Access**: Query via `docs-langchain` MCP

Example queries:
```
"How do I create a basic LangChain agent?"
"Explain LCEL (LangChain Expression Language)"
"How does LangGraph persistence work?"
"What are the best practices for prompt engineering in LangChain?"
```

### API Reference (Reference Server)
- **Python packages**: langchain, langgraph, langsmith (369 pages)
- **JavaScript packages**: langchain, langgraph (357 pages)
- **Class definitions**: All public APIs with signatures
- **Method parameters**: Complete argument documentation

**Access**: Query via `reference-langchain` MCP

Example queries:
```
"What are the parameters for BaseLanguageModel?"
"Show me the signature for ChatOpenAI"
"How do I use RunnableParallel in LCEL?"
```

---

## Use Cases

### 1. Agent Design (Sprint 1)
```
docs-langchain query: "How do I design a multi-agent system with LangChain?"
→ Learn Purchase Orchestrator, Procurement Controller, specialized builders patterns
→ Reference for state management, routing, error handling
```

### 2. Tool Integration
```
docs-langchain query: "How do I create custom tools for LangChain agents?"
reference-langchain query: "Show BaseTool class signature"
→ Implement SharePoint, Outlook, OneDrive integrations (Sprint 1 #9)
```

### 3. Context Management (Sprint 1 #8)
```
docs-langchain query: "How do I manage token budgets and memory in LangChain?"
reference-langchain query: "ConversationTokenBufferMemory parameters"
→ Implement context management, history truncation, token tracking
```

### 4. RAG & Knowledge Integration
```
docs-langchain query: "How do I build a RAG system with LangChain?"
reference-langchain query: "VectorStoreRetriever class"
→ Connect to knowledge graph, implement evidence retrieval
```

### 5. LangGraph Multi-Turn Sessions (Sprint 1 #11)
```
docs-langchain query: "How do I implement session persistence in LangGraph?"
reference-langchain query: "CheckpointSaver interface"
→ Implement multi-turn conversation management
```

### 6. Model Configuration (Sprint 1 #7)
```
docs-langchain query: "How do I integrate with model registries?"
reference-langchain query: "BaseLLM interface"
→ Connect to Databricks model serving endpoints
```

---

## Documentation Map

### Concepts Section (~4 pages)
- LCEL (LangChain Expression Language)
- Runnable interface
- Chat models vs. LLMs
- Structured output

### Guides Section (~76 pages)
**Key areas for Procure AI Sprint 1:**
- Building agents
- Tool use & integrations
- Memory & conversation
- RAG systems
- Prompt engineering
- Evaluation & tracing
- Using LangSmith

### API Reference Section (~369 Python pages)
**Key classes for implementation:**
- `BaseLanguageModel` — LLM abstraction
- `ChatOpenAI`, `Anthropic` — Model providers
- `Agent` — Agent orchestration
- `Tool` — Custom tool definition
- `Memory` — Conversation history management
- `VectorStore` — Embedding storage
- `Retriever` — Document retrieval
- `Chain` — Runnable sequences

---

## Integration with Procure AI

### Mapping to Sprint 1 Deliverables

| Deliverable | LangChain Resource |
|---|---|
| #2 Flask App | Guides: Building REST APIs with LangChain |
| #6 Chat Agent | Guides: Building agents, LangGraph for orchestration |
| #7 Model Registry | API: BaseLLM, ChatOpenAI, model initialization |
| #8 Context Management | API: Memory classes, Token budgeting guides |
| #9 User Tools & MCP | API: BaseTool, Tool integration guides |
| #10 HITL | Guides: Human-in-the-loop patterns |
| #11 Session Management | API: LangGraph checkpoints & persistence |
| #12 Templates | Guides: Prompt templates, output schemas |

### Example Sprint 1 Queries

**Week 1 (Core Agent)**
```
1. docs-langchain: "How do I build a multi-turn conversation agent?"
2. reference-langchain: "Show Agent, Runnable, and Tool APIs"
3. docs-langchain: "What's the difference between LCEL and traditional chains?"
```

**Week 2 (Context & Memory)**
```
1. docs-langchain: "How do I manage conversation history and token budgets?"
2. reference-langchain: "ConversationBufferMemory parameters"
3. docs-langchain: "Best practices for prompt caching and context windows"
```

**Week 3 (Tools & Integration)**
```
1. docs-langchain: "How do I integrate external APIs as LangChain tools?"
2. reference-langchain: "BaseTool and @tool decorator"
3. docs-langchain: "Building SharePoint, Outlook, OneDrive integrations"
```

**Week 4 (Persistence & Evaluation)**
```
1. docs-langchain: "How do I persist multi-turn conversations in LangGraph?"
2. reference-langchain: "Checkpoint and memory persistence APIs"
3. docs-langchain: "Using LangSmith for evaluation and monitoring"
```

---

## Best Practices (from LangChain Docs)

### Agent Design
- Use `ReAct` pattern (Reason + Act) for decision-making
- Implement tool validation before execution
- Use structured output for better parsing
- Add error handling and recovery strategies

### Context Management
- Track token count in real-time
- Implement sliding window for long conversations
- Compress older messages with summary or clustering
- Use semantic caching for expensive operations

### Tool Integration
- Define clear tool descriptions for LLM understanding
- Implement tool validation and error handling
- Use `@tool` decorator for simple functions
- Extend `BaseTool` for complex integrations

### Multi-Turn Sessions
- Use LangGraph's checkpoint mechanism
- Store conversation state in Lakebase/UC
- Implement thread-safe operations
- Monitor token usage per session

### Evaluation
- Use LangSmith for automatic tracing
- Implement custom evaluators for domain logic
- Track metrics: latency, token usage, accuracy
- A/B test prompt versions

---

## Troubleshooting

### MCP Connection Issues
**Problem**: MCP server not responding  
**Solution**: Check network connectivity. Both servers are public HTTP endpoints.

```bash
# Test connectivity
curl https://docs.langchain.com/mcp -I
curl https://reference.langchain.com/mcp -I
```

### Missing API References
**Problem**: Reference server doesn't show latest version  
**Solution**: Refresh cache. Reference docs update weekly with new releases.

**Expected behavior**: Both servers update automatically via Mintlify CDN.

### Finding Specific Documentation
**Use docs-langchain** for "how do I...?" questions  
**Use reference-langchain** for "what are the parameters for...?" questions

---

## Further Reading

- **LangChain Official Docs**: https://docs.langchain.com
- **LangGraph Guides**: https://docs.langchain.com/oss/python/langgraph
- **LangSmith Observability**: https://docs.langchain.com/langsmith
- **LCEL Documentation**: https://docs.langchain.com/oss/python/concepts
- **API Reference Index**: https://docs.langchain.com/llms.txt (full index of all docs)

---

## Contact & Support

- **LangChain Community Forum**: https://forum.langchain.com/
- **GitHub Issues**: https://github.com/langchain-ai/langchain/issues
- **LangSmith Support**: Available in LangSmith dashboard

---

## Version Info

- **Docs Last Updated**: 2026-08-18
- **LangChain Versions Covered**: All current (via llms.txt index)
- **Compatibility**: OpenCode, Claude Code, Cursor, VS Code, Deep Agents, Antigravity
- **Protocol**: HTTP (Model Context Protocol)

---

## Integration Status

✅ **docs-langchain** — Added to opencode.json  
✅ **reference-langchain** — Added to opencode.json  
✅ **Documentation** — Available in this file  
✅ **Configuration Examples** — Provided for all IDEs  

**Ready for use in Sprint 1 implementation.**

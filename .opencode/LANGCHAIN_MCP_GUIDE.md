# LangChain MCP Integration Guide

**Status**: ✅ Ready to Use  
**Installation Date**: 2026-08-18  
**MCPs Available**: 2 (docs-langchain, reference-langchain)

---

## What is LangChain MCP?

LangChain exposes two **Model Context Protocol (MCP) servers** that let AI applications query LangChain documentation in real-time.

**Why this matters for Procure AI**:
- Direct access to LangChain API reference while coding
- Real-time documentation queries (no manual web search)
- Exact signatures and parameters for all classes/methods
- Best practices from LangChain's extensive guides
- Integration with your IDE/agent for seamless development

---

## The Two MCP Servers

### 1. docs-langchain (Conceptual)
**URL**: `https://docs.langchain.com/mcp`  
**Purpose**: Guides, how-tos, tutorials, conceptual knowledge  
**Coverage**: 
- LangChain core concepts (LCEL, Runnables, etc.)
- Agent building patterns
- Memory and context management
- RAG systems and retrieval
- Tool integration and custom tools
- Prompt engineering best practices
- LangGraph state management
- LangSmith observability

**Best for**: "How do I...?" questions

### 2. reference-langchain (API Reference)
**URL**: `https://reference.langchain.com/mcp`  
**Purpose**: API reference, class signatures, method parameters  
**Coverage**:
- Python packages (langchain, langgraph, langsmith)
- JavaScript packages (langchain, langgraph)
- All public class definitions
- Method signatures with parameters
- Return types and exceptions

**Best for**: "What are the parameters for...?" questions

---

## How It Works

### In Claude Code
```bash
# MCPs are auto-loaded from opencode.json
# Just ask questions, and Claude Code queries the MCP servers
```

**Example usage in Claude Code**:
```
"How do I create a custom tool in LangChain?"
→ Queries docs-langchain
→ Returns guide + examples

"What parameters does ChatOpenAI accept?"
→ Queries reference-langchain
→ Returns full API signature
```

### In OpenCode
```
# MCPs are configured in opencode.json
# The OpenCode agent can query both MCP servers
```

### In Cursor
MCPs must be configured in Cursor settings:
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

See `.opencode/mcps/langchain.md` for full setup instructions for all IDEs.

---

## Sprint 1 Integration Map

### Week 1: Core Agent Architecture
**Focus**: Purchase Orchestrator + Procurement Controller agents

**Use docs-langchain for**:
- "How do I design a multi-agent system with LangChain?"
- "What are the ReAct pattern principles for agents?"
- "How do I implement agent routing and decision-making?"
- "Best practices for agent error handling and recovery?"

**Use reference-langchain for**:
- Agent class signature and methods
- Runnable interface and LCEL operators
- Tool and BaseTool class definitions
- AgentExecutor configuration options

**Deliverable**: #6 Chat Agent, part of #2 Flask App

---

### Week 2: Context & Session Management
**Focus**: Memory buffers, token tracking, conversation history

**Use docs-langchain for**:
- "How do I manage conversation history and context windows?"
- "What are best practices for token budgeting?"
- "How do I implement conversation summarization?"
- "How does memory persistence work in LangGraph?"

**Use reference-langchain for**:
- BaseMemory and ConversationMemory classes
- ConversationTokenBufferMemory parameters
- ConversationSummaryMemory options
- CheckpointSaver interface (for LangGraph)

**Deliverable**: #8 Context Management, #11 Session Management

---

### Week 3: Tools & External Integrations
**Focus**: SharePoint, Outlook, OneDrive, User Memory tools

**Use docs-langchain for**:
- "How do I build custom tools for external APIs?"
- "What's the pattern for integrating with SharePoint/Outlook/OneDrive?"
- "How do I handle authentication in tool integrations?"
- "Best practices for tool validation and error handling?"

**Use reference-langchain for**:
- BaseTool and @tool decorator
- ToolCall structure and handling
- Tool validation and return types
- AsyncTool for async operations

**Deliverable**: #9 User Tools & MCP

---

### Week 4: Persistence, Evaluation, & Deployment
**Focus**: Multi-turn session persistence, HITL, evaluation

**Use docs-langchain for**:
- "How do I implement human-in-the-loop approval in LangGraph?"
- "How do I track and evaluate agent performance?"
- "What are best practices for multi-turn persistence?"
- "How do I integrate with model registries?"

**Use reference-langchain for**:
- Checkpoint interface and implementation
- LangSmith API for tracking
- EvaluatorBase class
- Model provider integration APIs

**Deliverable**: #10 HITL, #7 Model Registry

---

## Query Examples

### For docs-langchain (Guides & Concepts)

```
Query 1: "How do I build a multi-agent system with LangChain?"
Expected: Guide on agent design patterns, multi-agent orchestration

Query 2: "What is LCEL and how do I use it?"
Expected: Explanation + examples of LangChain Expression Language

Query 3: "Best practices for prompt engineering in LangChain"
Expected: Guide with examples on prompt design and optimization

Query 4: "How do I implement RAG (Retrieval-Augmented Generation)?"
Expected: Step-by-step guide with code examples

Query 5: "How does LangGraph manage state in conversations?"
Expected: Guide on state management, checkpointing, persistence
```

### For reference-langchain (API Details)

```
Query 1: "ChatOpenAI class signature and parameters"
Expected: Full API with all __init__ parameters, defaults, types

Query 2: "What methods does the Agent class have?"
Expected: Method names, signatures, return types

Query 3: "ConversationBufferMemory constructor and options"
Expected: Full API documentation with parameter descriptions

Query 4: "BaseTool interface and how to extend it"
Expected: Class definition, abstract methods, required implementations

Query 5: "RunnableParallel operator syntax and options"
Expected: Constructor, usage examples, parameter documentation
```

---

## Sprint 1 Task Examples

### Task: Implement Purchase Orchestrator Agent

**Step 1**: Understand agent patterns
```
docs-langchain:
"Explain the Purchase Orchestrator pattern in multi-agent systems.
Show me examples of agent hierarchies and routing."
```

**Step 2**: Get API details
```
reference-langchain:
"Show me the Agent and AgentExecutor class signatures.
What are the key parameters for agent configuration?"
```

**Step 3**: Implement the agent
```python
from langchain.agents import Agent, AgentExecutor
from langchain.tools import BaseTool

# Use insights from both MCPs to implement
class PurchaseOrchestrator(Agent):
    # Implementation based on MCP docs
    pass
```

---

### Task: Implement Context Management

**Step 1**: Understand context patterns
```
docs-langchain:
"How do I implement token-aware context management?
What are the best practices for managing long conversations?"
```

**Step 2**: Get API details
```
reference-langchain:
"Show ConversationTokenBufferMemory API.
What parameters control token limits?"
```

**Step 3**: Implement context manager
```python
from langchain.memory import ConversationTokenBufferMemory

# Use MCP to get exact parameters and options
memory = ConversationTokenBufferMemory(
    llm=llm,
    max_token_limit=2000,
    # See reference-langchain for all available options
)
```

---

### Task: Create SharePoint Tool

**Step 1**: Understand tool patterns
```
docs-langchain:
"How do I create a custom tool that integrates with external APIs?
Best practices for authentication and error handling?"
```

**Step 2**: Get API details
```
reference-langchain:
"Show BaseTool class signature and required methods.
What does @tool decorator do?"
```

**Step 3**: Implement SharePoint tool
```python
from langchain.tools import BaseTool, @tool

@tool
def query_sharepoint(query: str) -> str:
    """Search SharePoint for documents."""
    # Implementation based on MCP patterns
    pass
```

---

## Troubleshooting

### MCPs Not Showing Up in IDE

**Claude Code**:
- MCPs are auto-loaded from `opencode.json`
- Ensure you're in the project directory
- Restart Claude Code if MCPs were just added

**Cursor**:
- Update `.cursor/config.json` with MCP servers
- Restart Cursor
- Check settings > MCP servers

**OpenCode**:
- MCPs should be in `opencode.json`
- Run `opencode --reload` to refresh

### Query Returns No Results

**Possible causes**:
- Network connectivity issue (check `curl https://docs.langchain.com/mcp`)
- Query is too specific or uses wrong terminology
- Try searching with different keywords

**Solution**:
1. Test connectivity: `curl https://docs.langchain.com/mcp -I`
2. Try simpler queries first
3. Use docs-langchain for general concepts, reference-langchain for APIs

### Finding Specific Information

**I want to know "how do I...?"**
→ Use `docs-langchain` MCP

**I want the exact API signature**
→ Use `reference-langchain` MCP

**I'm unsure which to use**
→ Start with `docs-langchain`, then drill into `reference-langchain` for details

---

## Configuration Status

### opencode.json ✅
```json
{
  "mcp": [
    {
      "name": "docs-langchain",
      "type": "http",
      "url": "https://docs.langchain.com/mcp"
    },
    {
      "name": "reference-langchain",
      "type": "http",
      "url": "https://reference.langchain.com/mcp"
    }
  ]
}
```

### Claude Code ✅
Auto-loads from opencode.json

### Cursor 📝
See `.opencode/mcps/langchain.md` for setup instructions

### VS Code 📝
See `.opencode/mcps/langchain.md` for setup instructions

### Deep Agents 📝
See `.opencode/mcps/langchain.md` for setup instructions

---

## Quick Reference

| Need | Use This | Example |
|------|----------|---------|
| Understanding patterns | docs-langchain | "How do agents work?" |
| API signatures | reference-langchain | "ChatOpenAI parameters?" |
| Best practices | docs-langchain | "Agent error handling?" |
| Class methods | reference-langchain | "Agent class methods?" |
| Troubleshooting | docs-langchain | "Why is my agent failing?" |
| Implementation details | reference-langchain | "BaseMemory interface?" |

---

## Related Resources

- **LangChain Docs**: https://docs.langchain.com
- **LangGraph Guide**: https://docs.langchain.com/oss/python/langgraph
- **LangSmith**: https://docs.langchain.com/langsmith
- **Community Forum**: https://forum.langchain.com/
- **GitHub**: https://github.com/langchain-ai/langchain

---

## Next Steps

### For Agents Starting Sprint 1
1. Read this guide (you're reading it now ✓)
2. Read `.opencode/mcps/langchain.md` for full MCP details
3. Start with `docs-langchain` for agent design patterns
4. Use `reference-langchain` when implementing agent classes
5. Refer back to MCPs throughout Sprint 1 as you build features

### For IDE Setup
- **Claude Code**: Works out of the box (auto-loads from opencode.json)
- **Cursor**: Follow instructions in `.opencode/mcps/langchain.md`
- **OpenCode**: Uses opencode.json
- **VS Code**: Follow instructions in `.opencode/mcps/langchain.md`

### For Questions
- Ask the MCPs directly: `"How do I...?"`
- Check `.design_docs/Knowledge/04 Agent System Arch.md` for requirements
- Check this guide for examples matching your task

---

**LangChain MCP is ready to use. Start building Sprint 1! 🚀**

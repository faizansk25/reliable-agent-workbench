<div align="center">

# 🔧 Reliable Agent Workbench

### *Production-grade AI agent with state management, tool permissions, and audit trails*

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![LangChain](https://img.shields.io/badge/LangGraph-Agents-1C3C3C?style=for-the-badge)](https://langchain.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-State-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://postgresql.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)

**Resumable agent tasks, per-tool permissions, MCP integration, and failure replay**

</div>

---

## 📖 What is this?

Most AI agents crash and lose all progress. This one **resumes from failure**.

Built based on *Agent Operating System* patterns (2025-2026) and MCP specification:

1. 🔄 **Durable execution** — Tasks survive crashes and restarts
2. 🔐 **Tool permissions** — Each tool has explicit access controls
3. 📋 **Audit trail** — Every action logged with timestamps
4. 🧠 **Memory** — Short-term conversation + long-term task memory
5. ✅ **Human approval** — Sensitive actions require confirmation
6. 📊 **Trace timeline** — Visual execution history
7. 🔁 **Failure replay** — Debug and retry failed steps

> **Why this matters:** The shift from "prompt engineer" to "AI systems engineer" means understanding state, tools, permissions, and reliability — not just prompts.

---

## 🎯 Key Features

| Feature | Description |
|---------|-------------|
| **State Machine** | Explicit agent loop: observe → decide → act → verify |
| **Tool Registry** | Register tools with schemas, permissions, and rate limits |
| **Checkpointing** | Save and resume agent state at any point |
| **MCP Support** | Model Context Protocol for tool interop |
| **Approval Gates** | Human-in-the-loop for sensitive operations |
| **Evaluation Suite** | Automated testing of agent behavior |
| **Cost Tracking** | Token usage and API cost monitoring |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│              User Request                │
└──────────────┬──────────────────────────┘
               │
       ┌───────▼───────┐
       │  Agent Loop    │  observe → decide → act → verify
       └───────┬───────┘
               │
   ┌───────────┼───────────┐
   │           │           │
┌──▼──┐  ┌────▼────┐  ┌───▼────┐
│Tool │  │  State  │  │ Memory │
│Reg. │  │ Manager │  │ Store  │
└──┬──┘  └────┬────┘  └───┬────┘
   │           │           │
   └───────────┼───────────┘
               │
       ┌───────▼───────┐
       │  Audit Log    │  Every action recorded
       └───────────────┘
```

---

## 🚀 Quick Start

```bash
git clone https://github.com/faizansk25/reliable-agent-workbench.git
cd reliable-agent-workbench
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env  # Add your API keys

# Run the agent
python -m core.agent --task "Research the latest Python 3.13 features"

# Run evaluation suite
pytest tests/ -v
```

---

## 📁 Project Structure

```
reliable-agent-workbench/
├── core/
│   ├── agent.py              # Main agent loop
│   ├── state.py              # State machine
│   ├── tools.py              # Tool registry with permissions
│   ├── memory.py             # Short/long-term memory
│   ├── approval.py           # Human-in-the-loop gates
│   ├── checkpoint.py         # Save/resume state
│   ├── cost_tracker.py       # Token and cost monitoring
│   └── audit.py              # Action logging
├── agents/
│   ├── researcher.py         # Web research agent
│   ├── coder.py              # Code generation agent
│   └── planner.py            # Task decomposition agent
├── tools/
│   ├── web_search.py         # Search tool
│   ├── file_ops.py           # File operations
│   └── code_exec.py          # Code execution
├── tests/
│   ├── test_agent.py
│   ├── test_tools.py
│   └── test_checkpoint.py
├── requirements.txt
└── README.md
```

---

## 📚 References

- [OpenAI Agents SDK (2025)](https://openai.github.io/openai-agents-python/)
- [Model Context Protocol Specification (2026)](https://blog.modelcontextprotocol.io/)
- [LangGraph Agent Documentation](https://langchain-ai.github.io/langgraph/)

---

## 👨‍💻 Author

**Faizan Muktar Shaikh**
- 🔗 [LinkedIn](https://linkedin.com/in/faizansk25) | [GitHub](https://github.com/faizansk25)

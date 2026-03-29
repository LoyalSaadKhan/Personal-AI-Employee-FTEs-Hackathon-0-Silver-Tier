# Personal AI Employee FTEs - Project Context

## Project Overview

This is a **hackathon project** for building **Autonomous AI Employees (Digital FTEs)** - AI agents that work 24/7 to manage personal and business affairs. The project uses **Claude Code** as the reasoning engine and **Obsidian** (local Markdown) as the dashboard/memory system.

**Tagline:** *Your life and business on autopilot. Local-first, agent-driven, human-in-the-loop.*

### Core Architecture

| Layer | Component | Purpose |
|-------|-----------|---------|
| **Brain** | Claude Code | Reasoning engine, task execution |
| **Memory/GUI** | Obsidian Vault | Dashboard, long-term memory, state management |
| **Senses** | Python Watchers | Monitor Gmail, WhatsApp, filesystems for triggers |
| **Hands** | MCP Servers | External actions (email, browser automation, payments) |
| **Persistence** | Ralph Wiggum Loop | Keep agent working until tasks complete |

### Key Concepts

- **Digital FTE**: An AI agent priced/managed like a human employee (works 168 hrs/week vs human 40 hrs/week)
- **Watcher Pattern**: Lightweight Python scripts that monitor inputs and create `.md` files in `/Needs_Action` folder
- **Human-in-the-Loop**: Sensitive actions require approval via file movement (`/Pending_Approval` → `/Approved`)
- **Monday Morning CEO Briefing**: Autonomous weekly audit generating revenue/bottleneck reports

## Directory Structure

```
Personal-AI-Employee-FTEs/
├── .qwen/skills/           # Qwen Code skills (agent capabilities)
│   └── browsing-with-playwright/
│       ├── SKILL.md        # Skill documentation
│       ├── scripts/        # MCP client & server helpers
│       └── references/     # Tool reference docs
├── skills-lock.json        # Installed skills registry
└── QWEN.md                 # This file
```

## Available Skills

### browsing-with-playwright

Browser automation via Playwright MCP server. Use for:
- Web scraping & data extraction
- Form submission & UI automation
- Testing workflows
- Any task requiring browser interaction

**Server Management:**
```bash
# Start server (shared browser context for stateful sessions)
bash .qwen/skills/browsing-with-playwright/scripts/start-server.sh

# Stop server (closes browser + process)
bash .qwen/skills/browsing-with-playwright/scripts/stop-server.sh

# Verify server is running
python .qwen/skills/browsing-with-playwright/scripts/verify.py
```

**Key Tools Available:**
- `browser_navigate` - Navigate to URL
- `browser_snapshot` - Get accessibility snapshot (element refs)
- `browser_click`, `browser_type`, `browser_fill_form` - Interact with elements
- `browser_take_screenshot` - Capture screenshots
- `browser_evaluate` - Execute JavaScript
- `browser_run_code` - Run multi-step Playwright code
- `browser_wait_for` - Wait for text/time conditions

**Usage Pattern:**
```bash
# Call via mcp-client.py
python scripts/mcp-client.py call -u http://localhost:8808 \
  -t browser_navigate -p '{"url": "https://example.com"}'
```

See `.qwen/skills/browsing-with-playwright/SKILL.md` for complete documentation.

## Hackathon Tiers

| Tier | Requirements | Estimated Time |
|------|--------------|----------------|
| **Bronze** | Obsidian dashboard, 1 watcher, Claude reading/writing to vault | 8-12 hrs |
| **Silver** | 2+ watchers, MCP server, human-in-loop workflow, scheduling | 20-30 hrs |
| **Gold** | Full integration, Odoo accounting, social media APIs, Ralph Wiggum loop | 40+ hrs |
| **Platinum** | Cloud deployment, domain specialization, A2A agent communication | 60+ hrs |

## Obsidian Vault Structure

Recommended folder organization:

```
Vault/
├── Inbox/                 # Raw incoming items
├── Needs_Action/          # Items requiring processing
├── In_Progress/<agent>/   # Claimed by specific agent
├── Pending_Approval/      # Awaiting human approval
├── Approved/              # Approved actions (triggers execution)
├── Rejected/              # Declined actions
├── Done/                  # Completed tasks
├── Plans/                 # Generated plan.md files
├── Briefings/             # CEO briefing reports
├── Accounting/            # Transaction logs
└── Business_Goals.md      # Objectives & metrics
```

## Watcher Pattern Implementation

All watchers follow this base structure:

```python
from pathlib import Path
from abc import ABC, abstractmethod

class BaseWatcher(ABC):
    def __init__(self, vault_path: str, check_interval: int = 60):
        self.vault_path = Path(vault_path)
        self.needs_action = self.vault_path / 'Needs_Action'
    
    @abstractmethod
    def check_for_updates(self) -> list:
        """Return list of new items to process"""
        pass
    
    @abstractmethod
    def create_action_file(self, item) -> Path:
        """Create .md file in Needs_Action folder"""
        pass
    
    def run(self):
        while True:
            items = self.check_for_updates()
            for item in items:
                self.create_action_file(item)
            time.sleep(self.check_interval)
```

## Human-in-the-Loop Pattern

For sensitive actions (payments, sending emails), Claude writes an approval request:

```markdown
---
type: approval_request
action: payment
amount: 500.00
recipient: Client A
status: pending
---

## Payment Details
- Amount: $500.00
- To: Client A

## To Approve
Move this file to /Approved folder.
```

The orchestrator watches `/Approved` and triggers MCP action when files appear.

## Ralph Wiggum Loop (Persistence)

A Stop hook pattern that keeps Claude working until tasks complete:

1. Orchestrator creates state file with prompt
2. Claude works on task
3. Claude tries to exit
4. Stop hook checks: Is task file in `/Done`?
5. If NO → Block exit, re-inject prompt (loop continues)
6. Repeat until complete or max iterations

Reference: `.claude/plugins/ralph-wiggum`

## Recommended MCP Servers

| Server | Capabilities | Use Case |
|--------|--------------|----------|
| `filesystem` | Read/write/list files | Built-in vault access |
| `email-mcp` | Send/draft/search emails | Gmail integration |
| `browser-mcp` | Navigate, click, fill | Payment portals, web automation |
| `calendar-mcp` | Create/update events | Scheduling |
| `mcp-odoo-adv` | Odoo ERP integration | Accounting, invoicing |

## Development Practices

- **Local-first**: All data stored locally in Obsidian vault
- **File-based communication**: Agents coordinate via file movements
- **Claim-by-move rule**: First agent to move item to `/In_Progress/<agent>/` owns it
- **Single-writer rule**: Only Local agent writes to `Dashboard.md`
- **Security**: Secrets never sync (`.env`, tokens, banking credentials excluded)

## Related Documentation

- **Main Blueprint**: `Personal AI Employee Hackathon 0_ Building Autonomous FTEs in 2026.md`
- **Skill Docs**: `.qwen/skills/browsing-with-playwright/SKILL.md`
- **Tool Reference**: `.qwen/skills/browsing-with-playwright/references/playwright-tools.md`

## Getting Started

1. **Install prerequisites**: Claude Code, Obsidian, Python 3.13+, Node.js 24+
2. **Create Obsidian vault**: Named `AI_Employee_Vault`
3. **Install skills**: Already configured in `skills-lock.json`
4. **Start watcher scripts**: Monitor your chosen inputs (Gmail, WhatsApp, etc.)
5. **Configure MCP servers**: Set up credentials for external services
6. **Run Ralph Wiggum loop**: Keep agent working autonomously

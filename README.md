# Personal AI Employee - Bronze Tier

> **Tagline:** Your life and business on autopilot. Local-first, agent-driven, human-in-the-loop.

A comprehensive architectural blueprint and implementation for building a "Digital FTE" (Full-Time Equivalent) - an AI agent that proactively manages personal and business affairs 24/7 using **Qwen Code** as the reasoning engine and **Obsidian** as the management dashboard.

## 🏆 Bronze Tier Deliverables

✅ **Completed:**
- Obsidian vault with `Dashboard.md` and `Company_Handbook.md`
- File System Watcher script (monitors drop folder for new files)
- Claude Code integration for reading/writing to vault
- Basic folder structure: `/Inbox`, `/Needs_Action`, `/Done`
- Agent Skills documentation

## 📁 Project Structure

```
Personal-AI-Employee-FTEs/
├── AI_Employee_Vault/          # Obsidian vault (your AI's memory)
│   ├── Dashboard.md            # Real-time status dashboard
│   ├── Company_Handbook.md     # Rules of engagement
│   ├── Business_Goals.md       # Objectives and metrics
│   ├── AI_Employee_SKILL.md    # Agent skills documentation
│   ├── Inbox/                  # Drop folder for incoming files
│   ├── Needs_Action/           # Items awaiting processing
│   ├── Plans/                  # Generated action plans
│   ├── Pending_Approval/       # Awaiting human decision
│   ├── Approved/               # Ready for execution
│   ├── Rejected/               # Declined actions
│   ├── Done/                   # Completed tasks
│   ├── Logs/                   # Audit trail
│   ├── Accounting/             # Financial records
│   └── Briefings/              # CEO reports
│
├── scripts/                    # Python watcher & orchestration scripts
│   ├── base_watcher.py         # Abstract base class for all watchers
│   ├── filesystem_watcher.py   # Monitors folder for new files
│   └── orchestrator.py         # Master process coordinating Claude Code
│
└── README.md                   # This file
```

## 🚀 Quick Start

### Prerequisites

| Software | Version | Purpose |
|----------|---------|---------|
| [Python](https://www.python.org/downloads/) | 3.13+ | Watcher scripts |
| [Qwen Code](https://github.com/anthropics/qwen-code) | Latest | Reasoning engine |
| [Obsidian](https://obsidian.md/download) | v1.10.6+ | Dashboard/Knowledge base |
| [Node.js](https://nodejs.org/) | v24+ LTS | MCP servers (future tiers) |

### Installation

1. **Clone or download this repository:**
   ```bash
   cd Personal-AI-Employee-FTEs
   ```

2. **Verify Python installation:**
   ```bash
   python --version  # Should be 3.13 or higher
   ```

3. **Verify Qwen Code installation:**
   ```bash
   qwen --version
   ```

4. **Open the vault in Obsidian:**
   - Launch Obsidian
   - Click "Open folder as vault"
   - Select the `AI_Employee_Vault` folder

### Running the AI Employee

#### Option 1: Run File System Watcher (Continuous Monitoring)

The watcher monitors the `Inbox` folder for new files:

```bash
# From project root directory
python scripts/filesystem_watcher.py ./AI_Employee_Vault
```

**How it works:**
- Drag-and-drop any file into `AI_Employee_Vault/Inbox/`
- Watcher detects the file within 30 seconds
- Creates a metadata `.md` file in `Needs_Action/`
- Original file is copied and removed from Inbox

#### Option 2: Run Orchestrator (Full Cycle Processing)

The orchestrator triggers Qwen Code to process pending items:

```bash
# From project root directory
python scripts/orchestrator.py ./AI_Employee_Vault 60
```

The `60` is the check interval in seconds.

#### Option 3: Manual Processing

Drop a file directly into `AI_Employee_Vault/Needs_Action/` and run Qwen Code manually:

```bash
cd AI_Employee_Vault
qwen "Process all files in /Needs_Action folder. Follow Company_Handbook.md rules."
```

## 📖 How It Works

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    EXTERNAL INPUT                           │
│                    (Files dropped)                          │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                 PERCEPTION LAYER                            │
│              FilesystemWatcher (Python)                     │
│         Polls Inbox folder every 30 seconds                 │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                  OBSIDIAN VAULT                             │
│  /Needs_Action/  ← New action files created here            │
│  /Plans/         ← Qwen creates action plans                │
│  /Done/          ← Completed tasks                          │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                 REASONING LAYER                             │
│              Qwen Code (AI Brain)                           │
│    Reads → Thinks → Plans → Writes → Requests Approval      │
└─────────────────────────────────────────────────────────────┘
```

### File Processing Flow

1. **User drops file** → `AI_Employee_Vault/Inbox/`
2. **FilesystemWatcher detects** → Creates `.md` metadata file
3. **File moved to** → `Needs_Action/`
4. **Orchestrator triggers Qwen** → Reads and processes file
5. **Qwen creates plan** → `Plans/PLAN_xxx.md`
6. **If approval needed** → Creates `Pending_Approval/xxx.md`
7. **Human approves** → Moves to `Approved/`
8. **Action executed** → File moved to `Done/`
9. **Audit log updated** → `Logs/YYYY-MM-DD.json`

## 📝 Usage Examples

### Example 1: Process a Document

1. Drop a PDF or text file into `AI_Employee_Vault/Inbox/`
2. Watcher creates action file in `Needs_Action/`
3. Run orchestrator or Qwen manually
4. Qwen reads the document and creates a summary
5. Qwen suggests actions based on content

### Example 2: Task Request

Create a file `AI_Employee_Vault/Needs_Action/task_request.md`:

```markdown
---
type: task_request
priority: high
received: 2026-03-20
---

# Task: Prepare Weekly Report

Please gather all completed tasks from this week and create a summary report.
Include:
- Number of tasks completed
- Key accomplishments
- Any blockers encountered
```

Then run:
```bash
python scripts/orchestrator.py ./AI_Employee_Vault
```

### Example 3: Approval Workflow

When Qwen needs approval for an action, it creates:

```markdown
---
type: approval_request
action: send_email
created: 2026-03-20T10:30:00Z
status: pending
---

# Approval Required: Send Weekly Report

## Details
- **To:** team@example.com
- **Subject:** Weekly Status Report - March 2026
- **Attachment:** weekly_report.pdf

## To Approve
Move this file to `/Approved` folder

## To Reject
Move this file to `/Rejected` folder
```

## 🔧 Configuration

### Watcher Settings

Edit `scripts/filesystem_watcher.py` to customize:

```python
# Check interval (default: 30 seconds)
check_interval = 30

# Watch folder (default: vault_path/Inbox)
watch_folder = vault_path / 'Inbox'
```

### Orchestrator Settings

Edit `scripts/orchestrator.py` to customize:

```python
# Check interval (default: 60 seconds)
check_interval = 60

# Log file location
logs = vault_path / 'Logs'
```

## 🛡️ Security & Privacy

### What's Safe

✅ All data stored locally in your Obsidian vault
✅ No cloud sync required (unless you enable it)
✅ Credentials never stored in vault files
✅ Full audit trail of all AI actions

### What to Watch

⚠️ Never store API keys or passwords in vault files
⚠️ Review approval requests before authorizing
⚠️ Regularly audit the `/Logs/` folder
⚠️ Keep your vault backed up (GitHub private repo recommended)

### Best Practices

1. Use environment variables for any API keys
2. Review all `/Pending_Approval` items daily
3. Run `python scripts/orchestrator.py` in a trusted terminal
4. Keep your Obsidian vault in a secure location

## 📊 Monitoring & Debugging

### Check Status

View `Dashboard.md` in Obsidian for real-time status:
- Pending actions count
- Awaiting approval count
- Recent activity log

### View Logs

```bash
# Today's log file
cat AI_Employee_Vault/Logs/2026-03-20.log

# JSON activity log
cat AI_Employee_Vault/Logs/2026-03-20.json
```

### Common Issues

| Issue | Solution |
|-------|----------|
| Watcher not detecting files | Check file permissions, ensure folder exists |
| Qwen not processing | Verify `qwen --version` works |
| Files not moving to Done | Check for approval requests in Pending_Approval |
| Dashboard not updating | Ensure orchestrator is running |

## 🎯 Next Steps (Silver Tier)

Ready to level up? Here's what's next:

1. **Gmail Watcher** - Monitor Gmail for new emails
2. **WhatsApp Watcher** - Monitor WhatsApp messages (Playwright-based)
3. **MCP Server Integration** - Send real emails, make payments
4. **Human-in-the-Loop Workflow** - Full approval system
5. **Scheduled Operations** - Cron-based daily briefings
6. **Plan.md Generation** - Qwen creates detailed action plans

## 📚 Documentation

| File | Purpose |
|------|---------|
| [`AI_Employee_SKILL.md`](AI_Employee_Vault/AI_Employee_SKILL.md) | Agent skills documentation |
| [`Company_Handbook.md`](AI_Employee_Vault/Company_Handbook.md) | Rules of engagement |
| [`Business_Goals.md`](AI_Employee_Vault/Business_Goals.md) | Objectives and metrics |
| [`Dashboard.md`](AI_Employee_Vault/Dashboard.md) | Real-time status |

## 🤝 Contributing

This is a hackathon project. Feel free to:
- Fork and customize for your needs
- Add new watcher implementations
- Improve the orchestrator logic
- Create MCP server integrations

## 📄 License

This project is part of the Personal AI Employee Hackathon 0. Share and build upon it freely within the community.

## 🔗 Resources

- [Hackathon Blueprint](./Personal%20AI%20Employee%20Hackathon%200_%20Building%20Autonomous%20FTEs%20in%202026.md)
- [Qwen Code Documentation](https://github.com/anthropics/qwen-code)
- [Obsidian Help](https://help.obsidian.md/)
- [Model Context Protocol](https://modelcontextprotocol.io/)

---

**Built with ❤️ for the Personal AI Employee Hackathon 0**

*Version: 0.1.0 (Bronze Tier)*

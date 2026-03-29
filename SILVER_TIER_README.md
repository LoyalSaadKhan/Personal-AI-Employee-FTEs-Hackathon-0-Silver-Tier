# AI Employee - Silver Tier Setup Guide

> **Tagline:** Your life and business on autopilot. Local-first, agent-driven, human-in-the-loop.

Complete setup guide for Silver Tier: Gmail Watcher + LinkedIn Auto-Poster + Human-in-the-Loop approvals.

---

## 🏆 Silver Tier Deliverables

| Component | Status | Description |
|-----------|--------|-------------|
| **Gmail Watcher** | ✅ Ready | Monitors Gmail for important/unread emails |
| **LinkedIn Poster** | ✅ Ready | Generates automated posts for lead generation |
| **File Watcher** | ✅ Ready | Monitors folder for file drops (from Bronze) |
| **HITL Approval** | ✅ Ready | Human approval workflow for sensitive actions |
| **Plan.md Reasoning** | ✅ Ready | Structured planning before execution |
| **Scheduled Operations** | ✅ Ready | Cron/Task Scheduler integration |

---

## 📁 Project Structure

```
Personal-AI-Employee-FTEs/
├── AI_Employee_Vault/
│   ├── Dashboard.md
│   ├── Company_Handbook.md
│   ├── Business_Goals.md
│   ├── AI_Employee_SKILL_SILVER.md    # Silver Tier skills doc
│   ├── .gmail/
│   │   ├── credentials.json            # Gmail OAuth credentials
│   │   └── token.json                  # Gmail OAuth token (after setup)
│   ├── Inbox/                          # Drop folder
│   ├── Needs_Action/
│   │   ├── email/                      # Gmail-triggered items
│   │   ├── whatsapp/                   # WhatsApp-triggered items
│   │   └── files/                      # File drop items
│   ├── Plans/                          # Action plans
│   ├── Pending_Approval/               # Awaiting approval
│   ├── Approved/                       # Ready for execution
│   ├── Done/                           # Completed tasks
│   ├── Social/
│   │   ├── drafts/                     # LinkedIn post drafts
│   │   ├── scheduled/                  # Scheduled posts
│   │   └── published/                  # Published posts log
│   └── Logs/                           # Audit trail
│
├── scripts/
│   ├── base_watcher.py                 # Base watcher class
│   ├── filesystem_watcher.py           # File drop watcher (Bronze)
│   ├── gmail_watcher.py                # Gmail watcher (Silver)
│   ├── whatsapp_watcher.py             # WhatsApp watcher (Silver)
│   ├── linkedin_poster.py              # LinkedIn post generator
│   ├── setup_gmail_oauth.py            # Gmail OAuth setup
│   └── orchestrator.py                 # Main orchestrator (Qwen Code)
│
└── credentials.json                     # Your Gmail credentials
```

---

## 🚀 Quick Start

### Step 1: Verify Prerequisites

```bash
# Check Python version (need 3.13+)
python --version

# Check Qwen Code installation
qwen --version

# Verify Gmail API packages
python -c "from google.oauth2.credentials import Credentials; print('OK')"
```

### Step 2: Set Up Gmail OAuth (Required)

Your `credentials.json` is already in the project root. Let's set up OAuth:

```bash
# Navigate to project directory
cd "C:\Users\Jawaria Noor\Desktop\Personal-AI-Employee-FTEs\Personal-AI-Employee-FTEs"

# Run OAuth setup (opens browser for authentication)
python scripts/setup_gmail_oauth.py ./AI_Employee_Vault ./AI_Employee_Vault/.gmail/credentials.json
```

**What happens:**
1. Browser opens with Google sign-in
2. Sign in with your Gmail account
3. Grant permissions to the AI Employee
4. Token is saved to `AI_Employee_Vault/.gmail/token.json`

**Troubleshooting:**
- If browser doesn't open, copy the URL from terminal
- Use a Gmail account you want to monitor
- Permissions needed: Read Gmail messages

### Step 3: Start the Watchers

**Terminal 1 - Gmail Watcher:**
```bash
python scripts/gmail_watcher.py ./AI_Employee_Vault
```

**Terminal 2 - File Watcher (optional, for file drops):**
```bash
python scripts/filesystem_watcher.py ./AI_Employee_Vault
```

**Terminal 3 - Orchestrator:**
```bash
python scripts/orchestrator.py ./AI_Employee_Vault 60
```

### Step 4: Generate LinkedIn Post

```bash
# Generate a draft post
python scripts/linkedin_poster.py ./AI_Employee_Vault --draft

# List recent posts
python scripts/linkedin_poster.py ./AI_Employee_Vault --list
```

---

## 📧 Gmail Watcher Configuration

### How It Works

1. Watches Gmail every 2 minutes for unread, important emails
2. Detects priority keywords: `urgent`, `asap`, `invoice`, `payment`, `help`
3. Creates action file in `Needs_Action/email/`
4. Orchestrator triggers Qwen Code to process
5. Qwen creates plan and approval request
6. Human approves → Email action executed

### Priority Keywords

Emails containing these keywords are flagged as high priority:
- `urgent`, `asap`, `invoice`, `payment`, `help`
- `deadline`, `meeting`, `review`, `approval`

### Customizing Gmail Watcher

Edit `scripts/gmail_watcher.py`:

```python
# Change check interval (default: 120 seconds)
check_interval = 60  # Check every minute

# Add custom keywords
PRIORITY_KEYWORDS = ['urgent', 'asap', 'your_keyword']

# Change Gmail query
q='is:unread is:important'  # Default
q='is:unread after:2026/03/01'  # Recent emails only
```

---

## 💼 LinkedIn Post Generator

### How It Works

1. Generates posts based on templates (tips, questions, insights)
2. Saves draft to `Social/drafts/`
3. Human reviews and moves to `Social/scheduled/`
4. Orchestrator publishes at scheduled time
5. Logs to `Social/published/`

### Generate Posts

```bash
# Generate random post type
python scripts/linkedin_poster.py ./AI_Employee_Vault --draft

# Generate specific type
python scripts/linkedin_poster.py ./AI_Employee_Vault --draft --type tip
python scripts/linkedin_poster.py ./AI_Employee_Vault --draft --type question
python scripts/linkedin_poster.py ./AI_Employee_Vault --draft --type insight

# List recent posts
python scripts/linkedin_poster.py ./AI_Employee_Vault --list
```

### Post Types

| Type | Purpose | Example |
|------|---------|---------|
| `tip` | Share actionable advice | "Quick Tip: Automate your..." |
| `question` | Engage audience | "What's your biggest challenge..." |
| `insight` | Share expertise | "Here's what I learned..." |
| `announcement` | Share news | "Exciting news!" |

### Customizing LinkedIn Posts

Create `AI_Employee_Vault/.linkedin_config.json`:

```json
{
  "post_frequency": "daily",
  "post_time": "09:00",
  "content_types": ["tip", "question", "insight"],
  "hashtags": [
    "#AI",
    "#Automation",
    "#Productivity",
    "#DigitalTransformation",
    "#YourIndustry"
  ],
  "require_approval": true,
  "auto_approve_themes": ["tips", "insights"]
}
```

---

## ✅ Human-in-the-Loop Approval

### Approval Workflow

```
┌─────────────────────────────────────────────────────────────┐
│  Qwen Code creates approval request in /Pending_Approval/   │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  Human reviews the request                                  │
│  - Check action details                                     │
│  - Verify content is appropriate                            │
│  - Add comments if needed                                   │
└────────────────────┬────────────────────────────────────────┘
                     │
         ┌───────────┴───────────┐
         │                       │
         ▼                       ▼
┌─────────────────┐     ┌─────────────────┐
│ Move to         │     │ Move to         │
│ /Approved/      │     │ /Rejected/      │
└────────┬────────┘     └─────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│  Orchestrator executes the action                           │
│  Logs result and moves to /Done/                            │
└─────────────────────────────────────────────────────────────┘
```

### Actions Requiring Approval

| Action | Auto-Approve | Require Approval |
|--------|--------------|------------------|
| Send email | ❌ Never | ✅ Always |
| WhatsApp reply | ❌ Never | ✅ Always |
| LinkedIn post | ⚠️ If matches themes | Otherwise |
| Payment | ❌ Never | ✅ Always |
| File organization | ✅ Yes | Never |

---

## 📋 Scheduled Operations

### Windows Task Scheduler

Set up automated daily briefing at 8 AM:

```powershell
# Open PowerShell as Administrator

$action = New-ScheduledTaskAction `
  -Execute "python" `
  -Argument "scripts/orchestrator.py C:\Users\Jawaria Noor\Desktop\Personal-AI-Employee-FTEs\Personal-AI-Employee-FTEs\AI_Employee_Vault" `
  -WorkingDirectory "C:\Users\Jawaria Noor\Desktop\Personal-AI-Employee-FTEs\Personal-AI-Employee-FTEs"

$trigger = New-ScheduledTaskTrigger `
  -Daily `
  -At 8:00AM

Register-ScheduledTask `
  -TaskName "AI_Employee_Daily_Briefing" `
  -Action $action `
  -Trigger $trigger `
  -Description "AI Employee daily briefing at 8 AM"
```

### LinkedIn Post Schedule (9 AM Daily)

```powershell
$action = New-ScheduledTaskAction `
  -Execute "python" `
  -Argument "scripts/linkedin_poster.py C:\Users\Jawaria Noor\Desktop\Personal-AI-Employee-FTEs\Personal-AI-Employee-FTEs\AI_Employee_Vault --draft" `
  -WorkingDirectory "C:\Users\Jawaria Noor\Desktop\Personal-AI-Employee-FTEs\Personal-AI-Employee-FTEs"

$trigger = New-ScheduledTaskTrigger `
  -Daily `
  -At 8:00AM

Register-ScheduledTask `
  -TaskName "AI_Employee_LinkedIn_Draft" `
  -Action $action `
  -Trigger $trigger `
  -Description "Generate LinkedIn post draft at 8 AM"
```

---

## 🧪 Testing

### Test Gmail Watcher

1. **Send yourself a test email** with subject: `URGENT: Test Invoice Request`
2. **Wait 2 minutes** for watcher to detect
3. **Check** `AI_Employee_Vault/Needs_Action/email/` for action file
4. **Run orchestrator:**
   ```bash
   python scripts/orchestrator.py ./AI_Employee_Vault
   ```
5. **Check** `AI_Employee_Vault/Plans/` for created plan

### Test LinkedIn Poster

1. **Generate draft:**
   ```bash
   python scripts/linkedin_poster.py ./AI_Employee_Vault --draft --type tip
   ```
2. **Open in Obsidian:** Review the generated post
3. **Move to scheduled:** Move file to `Social/scheduled/`
4. **Publish:**
   ```bash
   python scripts/linkedin_poster.py ./AI_Employee_Vault --publish
   ```
5. **Check log:** `Social/published/` for publication record

---

## 🔧 Troubleshooting

### Gmail Watcher Issues

| Problem | Solution |
|---------|----------|
| "Credentials not found" | Run `setup_gmail_oauth.py` first |
| "Token expired" | Delete `token.json` and re-run OAuth setup |
| No emails detected | Check Gmail labels, ensure emails are unread |
| API quota exceeded | Wait 1 hour, reduce check frequency |

### LinkedIn Poster Issues

| Problem | Solution |
|---------|----------|
| No drafts created | Check folder permissions |
| Wrong post type | Use `--type` flag to specify |
| Hashtags not showing | Check `.linkedin_config.json` |

### Orchestrator Issues

| Problem | Solution |
|---------|----------|
| Qwen not processing | Verify `qwen --version` works |
| Files not moving | Check for approval requests |
| Logs not writing | Check `Logs/` folder exists |

---

## 📊 Monitoring

### Check System Status

```bash
# View Dashboard in Obsidian
# Open: AI_Employee_Vault/Dashboard.md

# Check recent logs
type AI_Employee_Vault\Logs\*.log

# Count pending items
dir AI_Employee_Vault\Needs_Action /b | find /c ".md"

# Count approvals waiting
dir AI_Employee_Vault\Pending_Approval /b | find /c ".md"
```

### Daily Checklist

- [ ] Check Dashboard.md for pending items
- [ ] Review /Pending_Approval/ folder
- [ ] Verify watchers are running
- [ ] Check LinkedIn post was generated
- [ ] Review any errors in Logs/

---

## 🔐 Security Notes

### Credential Management

```bash
# NEVER commit credentials to git
echo ".gmail/token.json" >> .gitignore
echo "credentials.json" >> .gitignore

# Set restrictive permissions (Linux/Mac)
chmod 600 AI_Employee_Vault/.gmail/token.json
chmod 600 AI_Employee_Vault/.gmail/credentials.json
```

### What's Stored Where

| File | Contains | Safe to Share |
|------|----------|---------------|
| `credentials.json` | OAuth client ID/secret | ❌ Never |
| `token.json` | Access token | ❌ Never |
| `AI_Employee_Vault/*` | Business data | ⚠️ Review first |
| `Logs/*` | Activity logs | ✅ Generally safe |

---

## 📚 Documentation

| File | Purpose |
|------|---------|
| [`AI_Employee_SKILL_SILVER.md`](AI_Employee_Vault/AI_Employee_SKILL_SILVER.md) | Silver Tier skills documentation |
| [`HITL_APPROVAL_WORKFLOW.md`](AI_Employee_Vault/HITL_APPROVAL_WORKFLOW.md) | Approval workflow guide |
| [`PLAN_REASONING_LOOP.md`](AI_Employee_Vault/PLAN_REASONING_LOOP.md) | Plan.md creation guide |
| [`LINKEDIN_AUTOPOSTER.md`](AI_Employee_Vault/LINKEDIN_AUTOPOSTER.md) | LinkedIn automation guide |
| [`SCHEDULED_OPERATIONS.md`](AI_Employee_Vault/SCHEDULED_OPERATIONS.md) | Cron/Task Scheduler setup |

---

## 🎯 Next Steps (Gold Tier)

Ready to level up? Gold Tier adds:
- Odoo accounting integration
- Facebook/Instagram posting
- Twitter/X integration
- Multiple MCP servers
- Weekly CEO Briefings
- Ralph Wiggum persistence loop

---

**Silver Tier Complete!** 🎉

*Your AI Employee now monitors Gmail, generates LinkedIn posts, and handles approvals.*

# MCP Email Server Setup Guide

## 📧 Send Emails via Gmail API

This MCP server enables Qwen Code to send emails through your Gmail account.

---

## 🚀 Installation

### Step 1: Install Dependencies

```bash
cd scripts/mcp-email-server
npm install
```

### Step 2: Configure Gmail Credentials

Copy your Gmail credentials:

```bash
# From AI_Employee_Vault
copy ..\..\AI_Employee_Vault\.gmail\credentials.json .\.gmail\credentials.json
copy ..\..\AI_Employee_Vault\.gmail\token.json .\.gmail\token.json
```

Or create symlinks:

```bash
# Windows (as Administrator)
mklink /H .\.gmail\credentials.json ..\..\AI_Employee_Vault\.gmail\credentials.json
mklink /H .\.gmail\token.json ..\..\AI_Employee_Vault\.gmail\token.json
```

### Step 3: Update Gmail Scopes

The email server needs additional scopes. Re-run OAuth with send scope:

```bash
# Edit credentials.json to include send scope
# Then re-authenticate
python ../../scripts/setup_gmail_oauth.py ../../AI_Employee_Vault
```

---

## 🔧 Configure Qwen Code

Add to `~/.qwen/mcp.json` (Windows: `%USERPROFILE%\.qwen\mcp.json`):

```json
{
  "mcpServers": {
    "email": {
      "command": "node",
      "args": ["C:/Users/Jawaria Noor/Desktop/Personal-AI-Employee-FTEs/Personal-AI-Employee-FTEs/scripts/mcp-email-server/index.js"],
      "env": {
        "GMAIL_CREDENTIALS_PATH": "C:/Users/Jawaria Noor/Desktop/Personal-AI-Employee-FTEs/Personal-AI-Employee-FTEs/AI_Employee_Vault/.gmail/credentials.json",
        "GMAIL_TOKEN_PATH": "C:/Users/Jawaria Noor/Desktop/Personal-AI-Employee-FTEs/Personal-AI-Employee-FTEs/AI_Employee_Vault/.gmail/token.json"
      }
    }
  }
}
```

---

## ✅ Test Connection

```bash
# Start Qwen Code with MCP
cd AI_Employee_Vault
qwen "List available email tools"
```

Expected output:
```
Available email tools:
- email_send: Send an email via Gmail
- email_draft: Create a draft email
- email_search: Search emails in Gmail
```

---

## 📝 Usage Examples

### Send Email

```bash
qwen "Send email to test@example.com with subject 'Hello' and body 'This is a test email'"
```

### Create Draft

```bash
qwen "Create a draft email to client@example.com about the project update"
```

### Search Emails

```bash
qwen "Search for emails from boss@company.com"
```

---

## 🔐 Human-in-the-Loop Workflow

For Silver Tier, all email sending requires approval:

```
1. Email request detected → Creates approval file
2. Human reviews → Moves to /Approved
3. Orchestrator calls MCP → Sends email
4. Logs result → Moves to /Done
```

### Approval File Template

```markdown
---
type: approval_request
action: email_send
created: 2026-03-23T10:30:00Z
status: pending
---

# Approval Required: Send Email

## Details
- **To:** client@example.com
- **Subject:** Invoice #001
- **Body:** Please find attached...

## To Approve
Move to /Approved folder

## To Reject
Move to /Rejected folder
```

---

## 🐛 Troubleshooting

### Error: "Credentials not found"

**Solution:**
```bash
# Verify credentials exist
dir AI_Employee_Vault\.gmail\credentials.json

# Update mcp.json with correct path
```

### Error: "Token expired"

**Solution:**
```bash
# Re-run OAuth
python scripts/setup_gmail_oauth.py ./AI_Employee_Vault
```

### Error: "Scope insufficient"

**Solution:**
```bash
# Delete token and re-authenticate with send scope
del AI_Employee_Vault\.gmail\token.json
python scripts/setup_gmail_oauth.py ./AI_Employee_Vault
```

---

## 📊 Available Tools

| Tool | Description | Requires Approval |
|------|-------------|-------------------|
| `email_send` | Send email immediately | ✅ Yes |
| `email_draft` | Create draft (doesn't send) | ❌ No |
| `email_search` | Search emails | ❌ No |

---

## 🔒 Security Notes

- ✅ Credentials stored locally
- ✅ OAuth 2.0 authentication
- ✅ No passwords in code
- ✅ Token auto-refresh
- ⚠️ Never commit credentials to Git

Add to `.gitignore`:
```
.gmail/credentials.json
.gmail/token.json
```

---

**MCP Email Server Ready!** 🎉

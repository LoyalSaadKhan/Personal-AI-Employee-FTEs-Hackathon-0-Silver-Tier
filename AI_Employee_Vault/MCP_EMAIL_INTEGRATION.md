---
name: mcp-email-integration
description: |
  MCP Email Server integration for sending, drafting, and searching emails.
  Provides email capabilities to Qwen Code via Model Context Protocol.
---

# MCP Email Server Integration - Silver Tier

## Overview

This skill enables Qwen Code to send emails via MCP (Model Context Protocol) server.
Email sending requires human approval per Company_Handbook.md rules.

## Installation

### Step 1: Install MCP Email Server

```bash
npm install -g @anthropic/mcp-server-email
```

### Step 2: Configure Gmail Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create new project or select existing
3. Enable Gmail API
4. Create OAuth 2.0 credentials (Desktop app)
5. Download `credentials.json`
6. Save to secure location: `~/.gmail/credentials.json`

### Step 3: Configure Qwen Code MCP Settings

Create or edit `~/.qwen/mcp.json`:

```json
{
  "mcpServers": {
    "email": {
      "command": "npx",
      "args": ["-y", "@anthropic/mcp-server-email"],
      "env": {
        "GMAIL_CREDENTIALS": "/home/user/.gmail/credentials.json",
        "GMAIL_TOKEN_PATH": "/home/user/.gmail/token.json"
      }
    }
  }
}
```

### Step 4: Initial OAuth Flow

Run once to authenticate:

```bash
# This will open browser for OAuth
npx @anthropic/mcp-server-email
```

Follow the OAuth flow and save the token.

---

## Available Tools

### email/send

Send an email immediately.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| to | string | Yes | Recipient email address |
| subject | string | Yes | Email subject |
| body | string | Yes | Email body (plain text or HTML) |
| cc | string[] | No | CC recipients |
| bcc | string[] | No | BCC recipients |
| attachments | string[] | No | File paths to attach |

**Example:**
```bash
python scripts/mcp-client.py call -u http://localhost:8808 \
  -t email_send \
  -p '{"to": "client@example.com", "subject": "Invoice #001", "body": "Please find attached...", "attachments": ["/path/to/invoice.pdf"]}'
```

### email/draft

Create a draft email (doesn't send).

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| to | string | Yes | Recipient email address |
| subject | string | Yes | Email subject |
| body | string | Yes | Email body |

**Example:**
```bash
python scripts/mcp-client.py call -u http://localhost:8808 \
  -t email_draft \
  -p '{"to": "client@example.com", "subject": "Meeting Request", "body": "Hi, can we schedule..."}'
```

### email/search

Search emails in Gmail.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| query | string | Yes | Gmail search query |
| limit | number | No | Max results (default: 10) |

**Example:**
```bash
python scripts/mcp-client.py call -u http://localhost:8808 \
  -t email_search \
  -p '{"query": "from:client@example.com invoice", "limit": 5}'
```

---

## Human-in-the-Loop Workflow

For Silver Tier, all email sending requires approval:

### Step 1: Qwen Creates Approval Request

```markdown
---
type: approval_request
action: email_send
created: 2026-03-20T10:30:00Z
expires: 2026-03-21T10:30:00Z
status: pending
---

# Approval Required: Send Email

## Details
- **To:** client@example.com
- **Subject:** January 2026 Invoice - $1,500
- **Attachments:** invoice_2026_01.pdf

## Body
Dear Client,

Please find attached your invoice for January 2026 services.

Amount: $1,500
Due Date: February 19, 2026

Best regards,
AI Employee

## To Approve
Move this file to /Approved folder

## To Reject
Move this file to /Rejected folder
```

### Step 2: Human Reviews and Approves

Move file from `/Pending_Approval/` to `/Approved/`

### Step 3: Orchestrator Executes

```python
# In orchestrator.py
def send_approved_email(self, approval_file: Path):
    """Send email from approved approval request."""
    content = approval_file.read_text()
    metadata = parse_frontmatter(content)
    
    # Extract email details from approval
    email_data = {
        'to': metadata.get('to'),
        'subject': metadata.get('subject'),
        'body': extract_body(content),
        'attachments': metadata.get('attachments', [])
    }
    
    # Call MCP email server
    result = call_mcp_tool('email', 'send', email_data)
    
    # Log result
    self.log_action({
        'type': 'email_sent',
        'to': email_data['to'],
        'subject': email_data['subject'],
        'result': result
    })
    
    # Move to Done
    approval_file.rename(self.done / approval_file.name)
```

---

## Usage with Qwen Code

### Direct Command

```bash
cd AI_Employee_Vault
qwen -p "Send email to test@example.com with subject 'Hello' and body 'This is a test'" -y
```

### Via Orchestrator (Recommended)

The orchestrator handles the full workflow:

1. Watcher detects email request
2. Qwen creates plan
3. Qwen creates approval request
4. Human approves
5. Orchestrator sends via MCP

---

## Error Handling

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `Credentials not found` | Missing credentials.json | Check GMAIL_CREDENTIALS path in mcp.json |
| `Token expired` | OAuth token expired | Re-run OAuth flow |
| `Rate limit exceeded` | Too many emails | Wait 1 hour, reduce sending frequency |
| `Attachment not found` | Invalid file path | Use absolute paths for attachments |

### Retry Logic

```python
def send_with_retry(email_data, max_attempts=3):
    """Send email with retry on transient errors."""
    for attempt in range(max_attempts):
        try:
            result = call_mcp_tool('email', 'send', email_data)
            return result
        except RateLimitError:
            if attempt == max_attempts - 1:
                raise
            wait_time = 60 * (2 ** attempt)  # Exponential backoff
            time.sleep(wait_time)
```

---

## Security Best Practices

### Credential Management

```bash
# NEVER commit credentials to git
echo "*.json" >> .gitignore
echo ".gmail/" >> .gitignore

# Set restrictive file permissions
chmod 600 ~/.gmail/credentials.json
chmod 600 ~/.gmail/token.json
```

### Approval Thresholds

Per Company_Handbook.md:

| Email Type | Auto-Approve | Require Approval |
|------------|--------------|------------------|
| Draft creation | ✅ Yes | Never |
| Internal emails | ❌ No | Always |
| External to known contacts | ❌ No | Always |
| External to new contacts | ❌ No | Always + manual review |
| Bulk emails (>10 recipients) | ❌ Never | Always + explicit approval |
| Emails with attachments | ❌ No | Always |

---

## Testing

### Test Email Send

1. Create test approval request:
```markdown
---
type: approval_request
action: email_send
to: your-test-email@gmail.com
subject: TEST - Silver Tier Email Integration
---

# Test Email

This is a test of the Silver Tier email integration.

If you receive this, the integration is working!
```

2. Move to `/Approved/`
3. Run orchestrator
4. Check if email received

### Verify MCP Connection

```bash
# List available tools
python scripts/mcp-client.py list --url http://localhost:8808

# Test email search
python scripts/mcp-client.py call -u http://localhost:8808 \
  -t email_search -p '{"query": "label:inbox", "limit": 1}'
```

---

## Integration with Other Silver Tier Skills

### With Gmail Watcher

```
Gmail Watcher → Detects important email
    ↓
Qwen Code → Creates reply draft
    ↓
Approval Request → Human reviews
    ↓
MCP Email → Sends reply
```

### With WhatsApp Watcher

```
WhatsApp Watcher → Detects urgent message
    ↓
Qwen Code → Drafts email response
    ↓
Approval Request → Human reviews
    ↓
MCP Email → Sends email
```

---

*Silver Tier MCP Email Integration v0.1*

---
name: ai-employee-silver
description: |
  AI Employee Silver Tier - Functional Assistant with multiple watchers,
  MCP integration, human-in-the-loop approvals, and automated social media posting.
  Builds on Bronze Tier with enhanced capabilities for real-world automation.
---

# AI Employee Skills - Silver Tier

## Overview

Silver Tier extends Bronze Tier with:
- **Multiple Watchers**: Gmail + WhatsApp + File System monitoring
- **MCP Integration**: Real email sending via MCP server
- **Human-in-the-Loop**: Formal approval workflow for sensitive actions
- **Social Media Automation**: Auto-post to LinkedIn for lead generation
- **Plan.md Reasoning**: Structured planning before execution
- **Scheduled Operations**: Cron/Task Scheduler integration

## Vault Structure (Extended)

```
AI_Employee_Vault/
├── Dashboard.md              # Real-time status dashboard
├── Company_Handbook.md       # Rules of engagement
├── Business_Goals.md         # Objectives and metrics
├── Inbox/                    # Drop folder for incoming files
├── Needs_Action/             # Items awaiting processing
│   ├── email/                # Gmail-triggered items
│   ├── whatsapp/             # WhatsApp-triggered items
│   └── files/                # File drop items
├── Plans/                    # Generated action plans
├── Pending_Approval/         # Awaiting human decision
├── Approved/                 # Ready for execution
├── Rejected/                 # Declined actions
├── Done/                     # Completed tasks
├── Logs/                     # Audit trail
├── Accounting/               # Financial records
├── Briefings/                # CEO reports
├── Social/                   # Social media drafts and posts
│   ├── drafts/               # Posts awaiting approval
│   └── scheduled/            # Scheduled posts
└── Templates/                # Email and document templates
```

---

## Core Skills

### 1. Multi-Watcher Integration

#### Gmail Watcher

Monitors Gmail for new important/unread emails and creates action files.

**Configuration:**
```python
# gmail_watcher.py
GMAIL_CONFIG = {
    'credentials_path': '~/.gmail/credentials.json',
    'check_interval': 120,  # Check every 2 minutes
    'query': 'is:unread is:important',
    'keywords': ['invoice', 'payment', 'urgent', 'asap']
}
```

**Action File Format:**
```markdown
---
type: email
from: client@example.com
subject: Invoice Request - January 2026
received: 2026-03-20T10:30:00Z
priority: high
status: pending
message_id: 18f3c2a1b2c3d4e5
---

# Email Received

**From:** client@example.com
**Subject:** Invoice Request - January 2026
**Received:** 2026-03-20 10:30 AM

## Content
Hi, could you please send me the invoice for January services?

## Suggested Actions
- [ ] Generate invoice for January
- [ ] Send via email
- [ ] Log transaction

## Keywords Detected
- invoice
```

#### WhatsApp Watcher (Playwright-based)

Monitors WhatsApp Web for messages containing priority keywords.

**Configuration:**
```python
# whatsapp_watcher.py
WHATSAPP_CONFIG = {
    'session_path': '~/.whatsapp/session',
    'check_interval': 30,  # Check every 30 seconds
    'keywords': ['urgent', 'asap', 'invoice', 'payment', 'help', 'meeting'],
    'priority_contacts': ['+1234567890', '+0987654321']
}
```

**Action File Format:**
```markdown
---
type: whatsapp
from: +1234567890
contact_name: John Doe
received: 2026-03-20T10:30:00Z
priority: high
status: pending
keywords: ['urgent', 'payment']
---

# WhatsApp Message

**From:** John Doe (+1234567890)
**Received:** 2026-03-20 10:30 AM

## Message
Hi! Urgent: When can we schedule the payment discussion?

## Keywords Detected
- urgent
- payment

## Suggested Actions
- [ ] Reply to schedule meeting
- [ ] Add to calendar
- [ ] Flag for follow-up
```

#### File System Watcher

Already implemented in Bronze Tier - continues to work for file drops.

---

### 2. Plan.md Reasoning Loop

For every task, create a structured plan before execution.

**Plan Template:**
```markdown
---
plan_id: PLAN-20260320-001
created: 2026-03-20T10:30:00Z
source_file: EMAIL_18f3c2a1b2c3d4e5.md
priority: high
status: in_progress
estimated_turns: 5
---

# Action Plan: Send Invoice to Client

## Objective
Generate and send January 2026 invoice to client@example.com

## Context
- Client requested invoice via email
- Amount: $1,500 (from Business_Goals.md rates)
- Due date: Net 30

## Steps
- [x] Step 1: Identify client and request details
- [x] Step 2: Calculate invoice amount from rates
- [ ] Step 3: Generate invoice PDF
- [ ] Step 4: Create approval request for email send
- [ ] Step 5: Wait for human approval
- [ ] Step 6: Send email via MCP
- [ ] Step 7: Log transaction and move to Done

## Decisions Made
1. Using standard rate of $1,500/month
2. Invoice due in 30 days
3. Email requires human approval before sending

## Approval Required
**Yes** - Email sending requires human approval per Company_Handbook.md

## Related Files
- Source: /Needs_Action/email/EMAIL_18f3c2a1b2c3d4e5.md
- Invoice: /Invoices/2026-01_Client_Invoice.pdf (to create)
- Approval: /Pending_Approval/EMAIL_send_invoice.md (to create)

## Notes
Client has been with us for 6 months, always pays on time.
```

---

### 3. Human-in-the-Loop Approval Workflow

For sensitive actions, create formal approval requests.

**Approval Request Template:**
```markdown
---
type: approval_request
action: send_email
created: 2026-03-20T10:35:00Z
expires: 2026-03-21T10:35:00Z
status: pending
priority: high
---

# Approval Required: Send Email

## Action Details
- **Type:** Send Email
- **To:** client@example.com
- **Subject:** January 2026 Invoice - $1,500
- **Attachment:** 2026-01_Client_Invoice.pdf

## Email Body
```
Dear Client,

Please find attached your invoice for January 2026 services.

Invoice Details:
- Amount: $1,500
- Due Date: February 19, 2026
- Invoice #: INV-2026-001

Please let me know if you have any questions.

Best regards,
AI Employee
```

## Why This Requires Approval
Per Company_Handbook.md: All external communications require human approval.

## To Approve
Move this file to `/Approved` folder

## To Reject
Move this file to `/Rejected` folder with a note explaining why.

## Deadline
This approval expires in 24 hours. If not approved, the task will be escalated.
```

**Approval Processing:**
```python
# In orchestrator.py
def process_approved_items(self):
    """Process items that have been approved."""
    for item in self.approved.iterdir():
        metadata = parse_frontmatter(item.read_text())
        
        if metadata['action'] == 'send_email':
            # Call MCP Email Server
            result = call_email_mcp('send', {
                'to': metadata['to'],
                'subject': metadata['subject'],
                'body': metadata['body'],
                'attachments': metadata.get('attachments', [])
            })
            
            # Log result
            self.log_action(metadata, result)
            
            # Move to Done
            item.rename(self.done / item.name)
```

---

### 4. MCP Email Server Integration

Configure and use MCP server for email operations.

**MCP Configuration:**
```json
// ~/.qwen/mcp.json
{
  "mcpServers": {
    "email": {
      "command": "npx",
      "args": ["-y", "@anthropic/mcp-server-email"],
      "env": {
        "GMAIL_CREDENTIALS": "/path/to/gmail/credentials.json"
      }
    }
  }
}
```

**Available Email Tools:**
```python
# Tools available via MCP
EMAIL_TOOLS = {
    'email/send': {
        'description': 'Send an email',
        'parameters': ['to', 'subject', 'body', 'cc', 'bcc', 'attachments']
    },
    'email/draft': {
        'description': 'Create email draft',
        'parameters': ['to', 'subject', 'body']
    },
    'email/search': {
        'description': 'Search emails',
        'parameters': ['query', 'limit']
    }
}
```

**Usage in Qwen Code:**
```bash
# Via Qwen Code with MCP
qwen -p "Send email to client@example.com with subject 'Invoice' and attach invoice.pdf" -y
```

---

### 5. LinkedIn Auto-Poster

Automatically generate and post content to LinkedIn for lead generation.

**Configuration:**
```python
# linkedin_poster.py
LINKEDIN_CONFIG = {
    'credentials_path': '~/.linkedin/credentials.json',
    'post_frequency': 'daily',  # daily, weekly
    'post_time': '09:00',  # 9 AM local time
    'content_types': ['tip', 'announcement', 'question', 'case_study'],
    'hashtags': ['#AI', '#Automation', '#Productivity', '#DigitalTransformation']
}
```

**Post Generation Template:**
```markdown
---
type: social_post
platform: linkedin
created: 2026-03-20T08:00:00Z
scheduled: 2026-03-20T09:00:00Z
status: draft
---

# LinkedIn Post Draft

## Content
🚀 Quick Tip: Automate Your Repetitive Tasks

Did you know the average professional spends 2.5 hours daily on repetitive tasks?

Here's what you can automate TODAY:
✅ Email responses
✅ Meeting scheduling
✅ Invoice generation
✅ Social media posting

Start small. Pick ONE task. Automate it. Reclaim your time.

What's the first task you'd automate? Drop a comment! 👇

## Hashtags
#AI #Automation #Productivity #DigitalTransformation #BusinessEfficiency

## Media
[Optional: Image or carousel attachment]

## Approval Required
Move to /Approved to publish at scheduled time.
```

**Posting Flow:**
```
1. Orchestrator triggers daily at 8 AM
2. Qwen generates post based on Business_Goals.md themes
3. Creates draft in /Social/drafts/
4. Optional: Auto-approve if matches approved themes
5. Publish via LinkedIn API or browser automation
6. Log post in /Social/scheduled/
7. Update Dashboard with engagement metrics (later)
```

---

### 6. Scheduled Operations

Use cron (Linux/Mac) or Task Scheduler (Windows) for recurring tasks.

**Windows Task Scheduler Setup:**
```powershell
# Create scheduled task for daily briefing
$action = New-ScheduledTaskAction -Execute "python" `
  -Argument "scripts/orchestrator.py C:\path\to\vault --daily-briefing"
$trigger = New-ScheduledTaskTrigger -Daily -At 8:00AM
Register-ScheduledTask -TaskName "AI_Employee_Daily_Briefing" `
  -Action $action -Trigger $trigger -Description "Generate daily CEO briefing"
```

**Linux Cron Setup:**
```bash
# Edit crontab
crontab -e

# Add daily briefing at 8 AM
0 8 * * * cd /path/to/AI-Employee && python scripts/orchestrator.py ./vault --daily-briefing

# Add hourly check
0 * * * * cd /path/to/AI-Employee && python scripts/orchestrator.py ./vault
```

**Scheduled Task Types:**
| Task | Frequency | Time | Purpose |
|------|-----------|------|---------|
| Daily Briefing | Daily | 8:00 AM | Summarize yesterday's activities |
| Hourly Check | Hourly | :00 | Process pending items |
| Weekly Audit | Weekly | Monday 7 AM | Generate CEO Briefing |
| Social Post | Daily | 9:00 AM | Post to LinkedIn |
| Inbox Cleanup | Daily | 6:00 PM | Archive processed items |

---

### 7. Dashboard Updates (Real-time)

Keep Dashboard.md synchronized with system state.

**Auto-Update Triggers:**
- New item in Needs_Action → Increment pending count
- Plan created → Log in Recent Activity
- Approval requested → Increment awaiting approval count
- Task completed → Update Recent Activity, increment completed count

**Dashboard Sections:**
```markdown
## Quick Status
| Metric | Value | Trend |
|--------|-------|-------|
| Pending Actions | 3 | ↑ +2 |
| Awaiting Approval | 1 | - |
| Completed Today | 12 | ↑ +5 |
| Revenue MTD | $4,500 | ↑ +$500 |

## Recent Activity
**2026-03-20 10:45 AM** - Email sent to client@example.com (Invoice #2026-001)
**2026-03-20 10:30 AM** - WhatsApp message received from John Doe (urgent)
**2026-03-20 09:00 AM** - LinkedIn post published (127 impressions)

## Pending Approvals
| Request | Type | Created | Expires |
|---------|------|---------|---------|
| Send Invoice Email | email_send | 10:35 AM | Tomorrow 10:35 AM |

## System Health
| Component | Status | Last Check |
|-----------|--------|------------|
| Gmail Watcher | 🟢 Running | 10:45 AM |
| WhatsApp Watcher | 🟢 Running | 10:45 AM |
| File Watcher | 🟢 Running | 10:45 AM |
| Orchestrator | 🟢 Running | 10:45 AM |
```

---

## Decision Rules (Extended)

### Priority Classification

| Priority | Response Time | Auto-Approve | Examples |
|----------|---------------|--------------|----------|
| **Critical** | Immediate | Never | System failures, security issues |
| **High** | 2 hours | No | Client requests, deadlines <48h |
| **Normal** | 24 hours | Yes (low-risk) | General inquiries, routine tasks |
| **Low** | 72 hours | Yes | Archive, organize, research |

### Auto-Approve Matrix

| Action Type | Auto-Approve | Require Approval |
|-------------|--------------|------------------|
| File organization | ✅ Yes | Never |
| Reading/summarizing | ✅ Yes | Never |
| Plan creation | ✅ Yes | Never |
| Internal documentation | ✅ Yes | Never |
| Email to known contacts | ⚠️ Draft only | Send approval |
| Email to new contacts | ❌ Never | Always |
| Social media posts | ⚠️ If matches themes | Otherwise |
| Payments < $50 | ❌ Never | Always |
| Payments >= $50 | ❌ Never | Always |
| Delete files | ❌ Never | Always |

---

## Integration with Qwen Code

### Full Processing Prompt

```
You are an AI Employee assistant (Silver Tier). Process all files in /Needs_Action folder.

For each file:
1. Read and understand the content
2. Classify priority using Company_Handbook.md rules
3. Create detailed Plan.md in /Plans folder with:
   - Clear objective
   - Step-by-step checklist
   - Approval requirements
   - Related files
4. If action requires approval:
   - Create formal approval request in /Pending_Approval
   - Include all details for human review
   - Set 24-hour expiration
5. If no approval needed:
   - Execute the action using available MCP servers
   - Log the action in /Logs/
6. Move processed files to /Done
7. Update Dashboard.md with:
   - New pending/approved counts
   - Recent activity entries
   - System health status

Always follow Company_Handbook.md rules.
When in doubt, request approval rather than guessing.
```

### Completion Signal

```
<completion>
Silver Tier Processing Complete

Summary:
- Files processed: 5
- Plans created: 5
- Approvals requested: 2
- Actions executed: 3
- Social posts drafted: 1

Pending Approvals:
1. EMAIL_send_invoice.md (expires: 2026-03-21 10:35 AM)
2. WHATSAPP_reply_john_doe.md (expires: 2026-03-21 11:00 AM)

Dashboard Updated: ✅
Logs Written: ✅
</completion>
```

---

## Error Handling

### Common Errors

| Error | Recovery |
|-------|----------|
| Gmail API quota exceeded | Pause Gmail watcher for 1 hour, queue emails locally |
| WhatsApp session expired | Alert human to re-scan QR code |
| MCP server unavailable | Queue actions, retry in 5 minutes |
| Approval timeout (>24h) | Escalate: move to Dashboard "Overdue Approvals" |
| LinkedIn API rate limit | Skip post, reschedule for tomorrow |
| Plan execution failed | Log error, create clarification request |

### Graceful Degradation

1. **If Gmail Watcher fails**: Continue with WhatsApp + File watchers
2. **If MCP server down**: Create drafts, queue for later execution
3. **If Qwen unavailable**: Watchers continue, queue grows for later
4. **If vault locked**: Write to temp folder, sync when available
5. **If approval pending >24h**: Create reminder, escalate to human

---

## Testing the Silver Tier

### Test Scenario 1: Gmail Integration

1. Set up Gmail credentials
2. Send test email to yourself with subject "URGENT: Test"
3. Run: `python scripts/gmail_watcher.py ./AI_Employee_Vault`
4. Verify: Action file created in /Needs_Action/email/
5. Run orchestrator
6. Verify: Plan created, approval requested

### Test Scenario 2: WhatsApp Integration

1. Set up WhatsApp Web session
2. Send test message from another device: "Test urgent message"
3. Run: `python scripts/whatsapp_watcher.py ./AI_Employee_Vault`
4. Verify: Action file created in /Needs_Action/whatsapp/
5. Run orchestrator
6. Verify: Plan created with reply suggestion

### Test Scenario 3: Approval Workflow

1. Create approval request manually in /Pending_Approval/
2. Move file to /Approved/
3. Run orchestrator
4. Verify: Action executed, file moved to /Done/, log written

### Test Scenario 4: LinkedIn Auto-Post

1. Run: `python scripts/linkedin_poster.py ./AI_Employee_Vault --draft`
2. Verify: Draft created in /Social/drafts/
3. Review and move to /Social/scheduled/
4. Run: `python scripts/linkedin_poster.py ./AI_Employee_Vault --publish`
5. Verify: Post published, logged in Dashboard

---

## Extension Points (Gold Tier)

- **Odoo Integration**: Accounting system via MCP
- **Facebook/Instagram**: Social media integration
- **Twitter/X**: Tweet posting and monitoring
- **Multiple MCP Servers**: Email + Browser + Calendar + Slack
- **Weekly CEO Briefing**: Autonomous business audit
- **Ralph Wiggum Loop**: Persistent multi-step task completion
- **Error Recovery**: Advanced retry and fallback logic

---

*Silver Tier Skill v0.1 - Functional Assistant Layer*

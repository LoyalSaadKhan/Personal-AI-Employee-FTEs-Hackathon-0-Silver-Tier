---
name: human-in-the-loop-approval
description: |
  Human-in-the-Loop (HITL) approval workflow for sensitive actions.
  Ensures AI never takes critical actions without human review.
---

# Human-in-the-Loop Approval Workflow - Silver Tier

## Overview

The HITL approval workflow ensures that sensitive actions (sending emails, making payments, posting on social media) are reviewed and approved by a human before execution.

## Approval Folder Structure

```
AI_Employee_Vault/
├── Pending_Approval/     # Awaiting human decision
│   ├── EMAIL_send_invoice.md
│   └── WHATSAPP_reply_client.md
├── Approved/             # Approved, ready for execution
│   └── (files moved here by human)
├── Rejected/             # Declined actions
│   └── (files moved here by human)
└── Done/                 # Completed actions
    └── (files moved after execution)
```

---

## Actions Requiring Approval

| Action Type | Always Requires Approval | Auto-Approve |
|-------------|-------------------------|--------------|
| Send external email | ✅ Yes | Never |
| Send WhatsApp message | ✅ Yes | Never |
| Post on social media | ✅ Yes | If matches approved themes |
| Payment any amount | ✅ Yes | Never |
| Delete files | ✅ Yes | Never |
| Share sensitive info | ✅ Yes | Never |
| Create internal doc | ❌ No | ✅ Yes |
| Move files between folders | ❌ No | ✅ Yes |
| Summarize content | ❌ No | ✅ Yes |

---

## Approval Request Template

```markdown
---
type: approval_request
action: send_email
created: 2026-03-20T10:30:00Z
expires: 2026-03-21T10:30:00Z
status: pending
priority: high
---

# Approval Required: [Action Name]

## Action Details
- **Type:** [email_send / whatsapp_send / social_post / payment]
- **Description:** [What will happen]
- **Impact:** [Consequences of this action]

## Specific Details

### For Email
- **To:** recipient@example.com
- **Subject:** Email Subject Line
- **Attachments:** file1.pdf, file2.docx

### For WhatsApp
- **To:** +1234567890 (Contact Name)
- **Message:** [Full message text]

### For Social Post
- **Platform:** LinkedIn / Twitter / Facebook
- **Content:** [Post text]
- **Scheduled Time:** 2026-03-20 09:00 AM

### For Payment
- **Amount:** $500.00
- **Recipient:** Client Name
- **Reference:** Invoice #1234

## Why This Requires Approval

Per Company_Handbook.md section [X]: [Reason]

## To Approve

**Option 1:** Move this file to `/Approved` folder

**Option 2:** Reply to this file with comments, then move to `/Approved`

## To Reject

**Option 1:** Move this file to `/Rejected` folder with a note

**Option 2:** Add rejection reason below, then move to `/Rejected`

### Rejection Reason (if applicable)
<!-- Human can add notes here -->

## Deadline

This approval expires in **24 hours**. If not approved by [expiry datetime], the task will be escalated and added to Dashboard.

---

*Created by AI Employee v0.1 (Silver Tier)*
```

---

## Human Workflow

### Step 1: Notification

When approval is needed, you can be notified via:
- Dashboard.md update (check regularly)
- Email notification (if configured)
- WhatsApp message (if configured)
- Desktop notification (if running locally)

### Step 2: Review

Open the approval request file from `/Pending_Approval/` and review:
- Action type and details
- Potential impact
- Attached files or content
- Deadline for response

### Step 3: Decision

**To Approve:**
1. (Optional) Add comments or modifications to the file
2. Move file to `/Approved/` folder

**To Reject:**
1. Add rejection reason in the file
2. Move file to `/Rejected/` folder

**To Request Changes:**
1. Add comments explaining what needs to change
2. Move file back to `/Needs_Action/` with note

### Step 4: Execution

After approval:
- Orchestrator detects file in `/Approved/`
- Executes the action via MCP server
- Logs the action in `/Logs/`
- Moves file to `/Done/`

---

## Orchestrator Implementation

```python
class Orchestrator:
    def process_approved_items(self):
        """Process items that have been approved."""
        for item in self.approved.iterdir():
            if item.suffix == '.md':
                content = item.read_text()
                metadata = self.parse_frontmatter(content)
                
                action_type = metadata.get('action')
                
                if action_type == 'send_email':
                    self.send_email(metadata, content)
                elif action_type == 'send_whatsapp':
                    self.send_whatsapp(metadata, content)
                elif action_type == 'social_post':
                    self.post_social(metadata, content)
                elif action_type == 'payment':
                    self.process_payment(metadata, content)
                else:
                    self.logger.warning(f'Unknown action type: {action_type}')
                    continue
                
                # Log and move to Done
                self.log_action(metadata, 'executed')
                item.rename(self.done / item.name)
    
    def check_expired_approvals(self):
        """Check for expired approvals and escalate."""
        now = datetime.now()
        
        for item in self.pending_approval.iterdir():
            content = item.read_text()
            metadata = self.parse_frontmatter(content)
            
            expires_str = metadata.get('expires', '')
            if expires_str:
                expires = datetime.fromisoformat(expires_str.replace('Z', '+00:00'))
                
                if now > expires:
                    # Escalate expired approval
                    self.logger.warning(f'Expired approval: {item.name}')
                    self.create_escalation_task(item, metadata)
```

---

## Escalation Rules

### Approval Expiry

| Priority | Expires In | Escalation Action |
|----------|------------|-------------------|
| Critical | 1 hour | Immediate notification to human |
| High | 4 hours | Add to Dashboard "Overdue" section |
| Normal | 24 hours | Move to top of Pending_Approval |
| Low | 72 hours | Archive if still pending |

### Escalation Template

```markdown
---
type: escalation
original_approval: EMAIL_send_invoice.md
escalated_at: 2026-03-21T11:00:00Z
reason: approval_expired
---

# Escalation: Overdue Approval

## Original Request
- **File:** EMAIL_send_invoice.md
- **Action:** Send Email
- **Created:** 2026-03-20 10:30 AM
- **Expired:** 2026-03-21 10:30 AM

## Status
⚠️ This approval has expired without action.

## Required Action
Please review and decide:
1. Approve and move to /Approved
2. Reject and move to /Rejected
3. Request changes and add notes

## Impact of Delay
- Client waiting for invoice
- Payment may be delayed
- Relationship impact

---

*Auto-generated by AI Employee v0.1*
```

---

## Audit Trail

All approval actions are logged:

```json
{
  "timestamp": "2026-03-20T10:30:00Z",
  "type": "approval_created",
  "file": "EMAIL_send_invoice.md",
  "action": "send_email",
  "to": "client@example.com"
}
```

```json
{
  "timestamp": "2026-03-20T14:45:00Z",
  "type": "approval_approved",
  "file": "EMAIL_send_invoice.md",
  "approved_by": "human",
  "time_to_approve": "4h 15m"
}
```

```json
{
  "timestamp": "2026-03-20T14:46:00Z",
  "type": "action_executed",
  "action": "send_email",
  "result": "success",
  "message_id": "msg_12345"
}
```

---

## Best Practices

### For Humans

1. **Check approvals daily** - Set a recurring reminder
2. **Respond within SLA** - Don't let approvals expire
3. **Add context when rejecting** - Help AI learn
4. **Review patterns weekly** - Identify automation opportunities

### For AI

1. **Be specific** - Include all relevant details
2. **Explain why** - Justify why approval is needed
3. **Set clear deadlines** - Make expiry explicit
4. **Track outcomes** - Log approval decisions for learning

---

## Testing the Workflow

### Test Approval Flow

1. Create test approval request:
```bash
cat > AI_Employee_Vault/Pending_Approval/TEST_approval.md << 'EOF'
---
type: approval_request
action: test_action
created: 2026-03-20T10:00:00Z
expires: 2026-03-21T10:00:00Z
---

# Test Approval

This is a test of the approval workflow.

## To Approve
Move to /Approved folder
EOF
```

2. Move to `/Approved/`:
```bash
mv AI_Employee_Vault/Pending_Approval/TEST_approval.md AI_Employee_Vault/Approved/
```

3. Run orchestrator:
```bash
python scripts/orchestrator.py ./AI_Employee_Vault
```

4. Verify file moved to `/Done/`

---

*Silver Tier HITL Workflow v0.1*

---
name: ai-employee-bronze
description: |
  AI Employee Bronze Tier - Autonomous file processing and task management.
  Processes files dropped in the vault, creates action plans, requests approvals,
  and manages task completion workflow.
---

# AI Employee Skills - Bronze Tier

## Overview

This skill enables Qwen Code to function as an autonomous AI Employee that:
- Processes files dropped into the Obsidian vault
- Creates structured action plans
- Requests human approval for sensitive actions
- Tracks task completion
- Maintains audit logs

## Vault Structure

```
AI_Employee_Vault/
├── Dashboard.md           # Real-time status dashboard
├── Company_Handbook.md    # Rules and guidelines
├── Business_Goals.md      # Objectives and metrics
├── Inbox/                 # Drop folder for incoming files
├── Needs_Action/          # Items awaiting processing
├── Plans/                 # Generated action plans
├── Pending_Approval/      # Awaiting human decision
├── Approved/              # Ready for execution
├── Rejected/              # Declined actions
├── Done/                  # Completed tasks
├── Logs/                  # Audit trail
├── Accounting/            # Financial records
└── Briefings/             # CEO reports
```

## Core Skills

### 1. File Processing

When a file appears in `/Needs_Action`:

```
1. READ the file content
2. IDENTIFY the type and required action
3. CLASSIFY priority (Critical/High/Normal/Low)
4. CREATE action plan in /Plans
5. EXECUTE or REQUEST APPROVAL
6. LOG the action
7. MOVE to /Done when complete
```

### 2. Plan Creation

For each task, create a plan file:

```markdown
---
created: 2026-03-20T10:30:00Z
status: in_progress
priority: normal
---

# Plan: [Task Name]

## Objective
[Clear statement of what needs to be accomplished]

## Steps
- [ ] Step 1: Description
- [ ] Step 2: Description
- [ ] Step 3: Description

## Approval Required
[Yes/No - if yes, create file in /Pending_Approval]

## Notes
[Any relevant context or decisions]
```

### 3. Approval Workflow

For sensitive actions (payments, external communications, etc.):

```markdown
---
type: approval_request
action: [action_type]
created: 2026-03-20T10:30:00Z
expires: 2026-03-21T10:30:00Z
status: pending
---

# Approval Required

## Action Details
- **Type:** [payment/email/post/etc.]
- **Description:** [What will happen]
- **Impact:** [Consequences]

## To Approve
Move this file to `/Approved` folder

## To Reject
Move this file to `/Rejected` folder
```

### 4. Dashboard Updates

Keep `/Dashboard.md` current:

- Update pending action count
- Log completed activities
- Track approval status
- Note any errors or blockers

### 5. Logging

Every action must be logged in `/Logs/YYYY-MM-DD.json`:

```json
{
  "timestamp": "2026-03-20T10:30:00Z",
  "action_type": "file_processed",
  "file": "example.md",
  "status": "completed",
  "notes": "Successfully processed"
}
```

## Decision Rules

### Priority Classification

| Priority | Response Time | Examples |
|----------|---------------|----------|
| **Critical** | Immediate | System failures, security issues |
| **High** | 2 hours | Client requests, deadlines <48h |
| **Normal** | 24 hours | General inquiries, routine tasks |
| **Low** | 72 hours | Archive, organize, research |

### Auto-Approve vs. Human Approval

**Auto-Approve (can execute directly):**
- File organization tasks
- Reading and summarizing content
- Creating plans and documentation
- Moving files between folders

**Require Human Approval:**
- External communications (emails, messages)
- Financial transactions
- Deleting files
- Sharing sensitive information

## Usage Examples

### Example 1: Process Dropped File

```
User drops: invoice_template.xlsx into /Inbox

AI Employee actions:
1. FilesystemWatcher detects file
2. Creates FILE_invoice_template.md in /Needs_Action
3. Qwen reads and identifies as invoice template
4. Creates PLAN_invoice_template.md in /Plans
5. Asks: "Should I create an invoice from this template?"
6. If approved, generates invoice in /Invoices
7. Logs action and moves to /Done
```

### Example 2: Client Request

```
File content: "Please send me the project status update"

AI Employee actions:
1. Classify as: High priority client request
2. Create plan with steps:
   - [ ] Gather project status
   - [ ] Draft response email
   - [ ] Request approval
   - [ ] Send email
3. Create approval request for email
4. Wait for human to move to /Approved
5. Send email and log action
```

## Integration with Qwen Code

### Prompt Template

```
You are an AI Employee assistant. Process all files in /Needs_Action folder.

For each file:
1. Read and understand the content
2. Determine what action is needed based on Company_Handbook.md rules
3. Create a detailed plan in /Plans folder
4. If action requires approval, create file in /Pending_Approval
5. Execute approved actions
6. Move processed files to /Done
7. Update Dashboard.md with progress

Always follow the rules in Company_Handbook.md
```

### Completion Signal

When all tasks are complete, output:
```
<completion>
All pending items processed. 
- Files processed: X
- Plans created: Y
- Approvals requested: Z
- Actions completed: W
</completion>
```

## Error Handling

### Common Errors

| Error | Recovery |
|-------|----------|
| File unreadable | Log error, move to /Done with error note |
| Unclear action | Create clarification request in /Pending_Approval |
| Qwen unavailable | Watchers continue, queue grows for later |
| Approval timeout | Alert human after 24 hours |

### Graceful Degradation

1. If Qwen Code unavailable: Queue items, process when restored
2. If vault locked: Write to temp folder, sync when available
3. If approval pending >24h: Create reminder in Dashboard

## Testing the Skill

### Quick Test

1. Create a test file:
   ```markdown
   ---
   type: test
   received: 2026-03-20
   ---

   # Test Task

   Please acknowledge this test file and move it to /Done
   ```

2. Save to `/Needs_Action/test_task.md`

3. Run: `python orchestrator.py ./AI_Employee_Vault`

4. Verify:
   - Qwen reads the file
   - Creates plan in /Plans
   - Moves test file to /Done
   - Updates Dashboard

## Extension Points (Silver/Gold Tier)

- **Gmail Watcher**: Monitor Gmail for new emails
- **WhatsApp Watcher**: Monitor WhatsApp messages
- **MCP Integration**: Execute real external actions
- **Scheduled Briefings**: Generate weekly CEO reports
- **Ralph Wiggum Loop**: Persistent autonomous processing

---

*Bronze Tier Skill v0.1 - Foundation Layer*

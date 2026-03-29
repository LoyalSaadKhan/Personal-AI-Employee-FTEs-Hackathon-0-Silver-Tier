---
name: plan-reasoning-loop
description: |
  Structured Plan.md creation and reasoning loop for complex task execution.
  Ensures AI thinks before acting and tracks progress systematically.
---

# Plan.md Reasoning Loop - Silver Tier

## Overview

Before executing any non-trivial task, Qwen Code creates a structured Plan.md document that:
- Defines the objective clearly
- Breaks down steps into checkboxes
- Tracks decisions made
- Records approval requirements
- Logs progress as steps complete

---

## Plan Template

```markdown
---
plan_id: PLAN-20260320-001
created: 2026-03-20T10:30:00Z
updated: 2026-03-20T10:35:00Z
source_file: EMAIL_client_invoice_request.md
priority: high
status: in_progress
estimated_turns: 5
actual_turns: 0
---

# Action Plan: [Clear Objective Statement]

## Objective
[One clear sentence describing what needs to be accomplished]

## Context
- **Trigger:** [What initiated this task]
- **Stakeholders:** [Who is involved/affected]
- **Constraints:** [Any limitations or requirements]
- **Success Criteria:** [How we know the task is complete]

## Steps

### Phase 1: Analysis
- [ ] Step 1.1: [Specific action]
- [ ] Step 1.2: [Specific action]

### Phase 2: Execution
- [ ] Step 2.1: [Specific action]
- [ ] Step 2.2: [Specific action]

### Phase 3: Verification
- [ ] Step 3.1: [Verify outcome]
- [ ] Step 3.2: [Log results]

## Decisions Made

| Decision # | What | Why | Alternative Considered |
|------------|------|-----|----------------------|
| 1 | [Decision] | [Rationale] | [Alternative] |

## Approval Required

**Yes/No**

If yes:
- **Type:** [email_send / payment / social_post / other]
- **Approval File:** /Pending_Approval/[filename].md
- **Status:** pending / approved / rejected
- **Expires:** [datetime]

## Related Files

- **Source:** /Needs_Action/[source_file].md
- **Output:** [Expected output files]
- **Approval:** [Approval file if applicable]
- **References:** [Any reference files used]

## Progress Log

| Timestamp | Turn | Action | Result |
|-----------|------|--------|--------|
| 2026-03-20 10:30 | 1 | Created plan | Plan initialized |
| 2026-03-20 10:35 | 2 | Completed Step 1.1 | [Result] |

## Blockers

[List any obstacles or issues encountered]

## Notes

[Any additional context, observations, or learnings]

---

*Plan created by AI Employee v0.1 (Silver Tier)*
```

---

## Reasoning Loop Process

### Step 1: Read and Understand

```
Input: File in /Needs_Action/
Process: Read content, identify type and required action
Output: Understanding of what needs to be done
```

### Step 2: Create Plan

```
Input: Understanding from Step 1
Process: Create Plan.md with:
  - Clear objective
  - Step-by-step breakdown
  - Approval requirements
  - Success criteria
Output: Plan.md file in /Plans/
```

### Step 3: Execute Plan (Iterative)

```
For each step in plan:
  1. Check if approval needed
  2. If yes, create approval request and wait
  3. Execute step
  4. Update progress log
  5. Mark step complete
  6. If error, log and decide: retry / escalate / skip
```

### Step 4: Verify and Close

```
1. Verify all steps complete
2. Verify success criteria met
3. Update plan status to 'completed'
4. Move source file to /Done/
5. Update Dashboard
6. Log completion
```

---

## Example: Invoice Request Plan

```markdown
---
plan_id: PLAN-20260320-001
created: 2026-03-20T10:30:00Z
updated: 2026-03-20T10:30:00Z
source_file: EMAIL_client_invoice_request.md
priority: high
status: in_progress
estimated_turns: 6
---

# Action Plan: Generate and Send Invoice to Client

## Objective
Generate January 2026 invoice for Client A and send via email.

## Context
- **Trigger:** Email from client@example.com requesting invoice
- **Stakeholders:** Client A, Finance team
- **Constraints:** Use standard rate of $1,500/month, Net 30 terms
- **Success Criteria:** Invoice sent, logged in accounting, client confirmation

## Steps

### Phase 1: Analysis
- [x] Step 1.1: Read email and identify client
- [x] Step 1.2: Look up client rate in Business_Goals.md
- [x] Step 1.3: Determine invoice period and amount

### Phase 2: Invoice Generation
- [ ] Step 2.1: Create invoice PDF with details
- [ ] Step 2.2: Save to /Invoices/ folder
- [ ] Step 2.3: Log in /Accounting/Invoices.md

### Phase 3: Email Preparation
- [ ] Step 3.1: Draft email with invoice attached
- [ ] Step 3.2: Create approval request

### Phase 4: Approval & Sending
- [ ] Step 4.1: Wait for human approval
- [ ] Step 4.2: Send email via MCP
- [ ] Step 4.3: Log sent email

### Phase 5: Completion
- [ ] Step 5.1: Update Dashboard
- [ ] Step 5.2: Move files to /Done/
- [ ] Step 5.3: Mark email as read in Gmail

## Decisions Made

| # | What | Why | Alternative |
|---|------|-----|-------------|
| 1 | Use standard rate | Client has ongoing monthly contract | Could negotiate ad-hoc rate |
| 2 | Net 30 terms | Per Company_Handbook.md standard | Could offer early payment discount |

## Approval Required

**Yes**

- **Type:** email_send
- **Approval File:** /Pending_Approval/EMAIL_send_invoice_client_a.md
- **Status:** pending
- **Expires:** 2026-03-21T10:30:00Z

## Related Files

- **Source:** /Needs_Action/email/EMAIL_client_invoice_request.md
- **Output:** /Invoices/2026-01_Client_A.pdf
- **Approval:** /Pending_Approval/EMAIL_send_invoice_client_a.md
- **References:** /Business_Goals.md (client rates)

## Progress Log

| Timestamp | Turn | Action | Result |
|-----------|------|--------|--------|
| 2026-03-20 10:30 | 1 | Created plan | Plan initialized |
| 2026-03-20 10:31 | 2 | Step 1.1 complete | Identified: Client A |
| 2026-03-20 10:32 | 3 | Step 1.2 complete | Rate: $1,500/month |
| 2026-03-20 10:33 | 4 | Step 1.3 complete | Amount: $1,500, Net 30 |

## Blockers

None currently.

## Notes

- Client has been with us for 6 months
- Always pays on time
- Prefers PDF invoices

---

*Plan created by AI Employee v0.1 (Silver Tier)*
```

---

## Integration with Qwen Code

### Prompt Template

```
You are processing a task from /Needs_Action/. Before taking any action:

1. READ the source file completely
2. IDENTIFY the type of request and required actions
3. CREATE a Plan.md file in /Plans/ with:
   - Clear objective (one sentence)
   - Context section with trigger, stakeholders, constraints
   - Step-by-step checklist organized by phases
   - Approval requirements (if any)
   - Related files section
   - Progress log (start with step 1 complete)

4. EXECUTE the plan step by step:
   - Update progress log after each step
   - Mark steps complete with [x]
   - If approval needed, create approval request and pause

5. VERIFY completion:
   - All steps marked complete
   - Success criteria met
   - Files moved to appropriate folders

6. CLOSE the plan:
   - Update status to 'completed'
   - Add final progress log entry
   - Move source file to /Done/

Always follow Company_Handbook.md rules.
When in doubt, request approval.
```

---

## Plan Status Lifecycle

```
created → in_progress → awaiting_approval → in_progress → completed
                                              ↓
                                          rejected → cancelled
```

### Status Definitions

| Status | Meaning | Next Action |
|--------|---------|-------------|
| created | Plan just created | Start executing steps |
| in_progress | Steps being executed | Continue execution |
| awaiting_approval | Waiting for human approval | Pause until approved |
| completed | All steps done | Archive plan |
| cancelled | Task cancelled | Move to archive |
| blocked | Cannot proceed | Escalate to human |

---

## Multi-Turn Execution

For complex plans requiring multiple Qwen Code turns:

### Turn 1: Analysis & Planning
```
- Read source file
- Create Plan.md
- Complete analysis phase
- Create approval request if needed
```

### Turn 2: Execution
```
- Continue from progress log
- Execute next phase steps
- Update progress log
```

### Turn 3+: Continue Execution
```
- Pick up where left off
- Complete remaining steps
- Handle any blockers
```

### Final Turn: Verification & Closure
```
- Verify all steps complete
- Update status to 'completed'
- Move files to /Done/
- Update Dashboard
```

---

## Error Handling in Plans

### When Step Fails

```markdown
## Progress Log

| Timestamp | Turn | Action | Result |
|-----------|------|--------|--------|
| 10:30 | 1 | Created plan | Success |
| 10:35 | 2 | Step 2.1: Generate PDF | FAILED: Template not found |

## Blockers

1. **Invoice template missing**
   - Expected: /Templates/invoice_template.pdf
   - Actual: File not found
   - Resolution needed: Create template or use alternative

## Next Steps

- [ ] Create invoice template
- [ ] OR use generic invoice format
- [ ] Retry Step 2.1
```

### Escalation Pattern

```markdown
## Escalation

**Escalated at:** 2026-03-20T10:40:00Z
**Reason:** Blocker requires human decision
**File:** /Pending_Approval/ESCALATION_PLAN_20260320_001.md

Waiting for human to:
1. Provide invoice template path
2. OR approve use of generic format
```

---

## Best Practices

### For Plan Creation

1. **Be specific** - Each step should be actionable
2. **Estimate turns** - Helps track complexity
3. **Identify approvals early** - Don't discover mid-execution
4. **Log as you go** - Update progress after each step
5. **Link related files** - Makes audit easier

### For Plan Execution

1. **Follow the plan** - Don't skip steps
2. **Update progress** - Keep log current
3. **Flag blockers early** - Don't spin on unsolvable problems
4. **Verify before closing** - Ensure success criteria met

---

*Silver Tier Plan Reasoning Loop v0.1*

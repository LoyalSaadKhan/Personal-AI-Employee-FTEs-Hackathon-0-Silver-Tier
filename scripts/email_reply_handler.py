#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Email Reply Handler - Automatically reply to emails using Qwen Code + MCP.

This script:
1. Reads emails from Needs_Action/email/
2. Uses Qwen Code to generate reply
3. Creates approval request
4. Sends via MCP when approved

Usage:
    python email_reply_handler.py ./AI_Employee_Vault
"""

import sys
import json
import subprocess
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('Email Reply Handler')


class EmailReplyHandler:
    """Handle email replies automatically."""

    def __init__(self, vault_path: Path):
        self.vault_path = vault_path
        self.needs_action = vault_path / 'Needs_Action' / 'email'
        self.pending_approval = vault_path / 'Pending_Approval'
        self.approved = vault_path / 'Approved'
        self.done = vault_path / 'Done'
        self.plans = vault_path / 'Plans'
        
        # Ensure folders exist
        for folder in [self.pending_approval, self.approved, self.done, self.plans]:
            folder.mkdir(parents=True, exist_ok=True)

    def get_unprocessed_emails(self):
        """Get emails that need replies."""
        if not self.needs_action.exists():
            return []
        
        emails = []
        for f in self.needs_action.iterdir():
            if f.is_file() and f.suffix == '.md' and not f.name.startswith('.'):
                content = f.read_text(encoding='utf-8')
                # Check if it's a reply request
                if 'type: email' in content and 'status: pending' in content:
                    emails.append(f)
        
        return emails

    def generate_reply(self, email_content: str) -> Optional[Dict]:
        """
        Use Qwen Code to generate a reply.
        
        Returns:
            dict: {'subject': str, 'body': str} or None
        """
        # Extract original email details
        lines = email_content.split('\n')
        from_email = ''
        subject = ''
        body = ''
        in_body = False
        
        for line in lines:
            if line.startswith('from:'):
                from_email = line.split(':', 1)[1].strip()
            elif line.startswith('subject:'):
                subject = line.split(':', 1)[1].strip()
            elif line.strip() == '## Email Content':
                in_body = True
            elif in_body and line.strip() == '---':
                break
            elif in_body:
                body += line + '\n'
        
        prompt = f'''You are an AI Employee assistant. Generate a professional email reply.

Original Email:
From: {from_email}
Subject: {subject}

Message:
{body}

Generate a professional, courteous reply that:
1. Acknowledges their inquiry
2. Provides helpful information
3. Offers to discuss further

Respond with EXACTLY this JSON format (no other text):
{{
  "reply_subject": "Re: {subject}",
  "reply_body": "Your professional reply here"
}}
'''

        try:
            # Call Qwen Code
            result = subprocess.run(
                ['qwen', '-p', prompt],
                capture_output=True,
                text=True,
                timeout=120,
                shell=True,
                cwd=str(self.vault_path)
            )

            # Parse JSON from output
            output = result.stdout.strip()
            logger.info(f"Qwen output: {output[:200]}...")
            
            # Try to find JSON in output
            start = output.find('{')
            end = output.rfind('}') + 1
            
            if start >= 0 and end > start:
                json_str = output[start:end]
                try:
                    reply_data = json.loads(json_str)
                    logger.info(f"✓ Parsed reply from Qwen")
                    return {
                        'subject': reply_data.get('reply_subject', f'Re: {subject}'),
                        'body': reply_data.get('reply_body', 'Thank you for your email.')
                    }
                except json.JSONDecodeError as e:
                    logger.warning(f"JSON parse error: {e}")
                    logger.warning(f"JSON string: {json_str}")
            
            # Fallback: Generate a simple reply
            logger.info("Using fallback reply")
            return {
                'subject': f'Re: {subject}',
                'body': f'''Dear Sender,

Thank you for your email. We have received your inquiry and will get back to you shortly with the requested information.

Best regards,
AI Employee'''
            }

        except Exception as e:
            logger.error(f"Failed to generate reply: {e}")
            return None

    def create_approval_request(self, email_file: Path, reply: Dict) -> Path:
        """Create approval request file."""
        # Parse original email metadata
        content = email_file.read_text(encoding='utf-8')
        
        metadata = {}
        lines = content.split('\n')
        in_frontmatter = False
        for line in lines:
            if line.strip() == '---':
                in_frontmatter = not in_frontmatter
            elif in_frontmatter and ':' in line:
                key, value = line.split(':', 1)
                metadata[key.strip()] = value.strip()

        # Create approval file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        approval_content = f'''---
type: approval_request
action: email_send
to: {metadata.get('from', '')}
subject: {reply['subject']}
original_file: {email_file.name}
created: {datetime.now().isoformat()}
expires: {(datetime.now().replace(hour=23, minute=59)).isoformat()}
status: pending
---

# Approval Required: Send Email Reply

**To:** {metadata.get('from', '')}

**Subject:** {reply['subject']}

---

## Reply Body

{reply['body']}

---

## Original Email

**From:** {metadata.get('from', 'Unknown')}
**Subject:** {metadata.get('subject', 'No Subject')}
**Received:** {metadata.get('received', 'Unknown')}

---

## To Approve

Move this file to `/Approved` folder

The orchestrator will send the email via MCP server.

## To Reject

Move this file to `/Rejected` folder with a note.

---

*Generated by AI Employee v0.1*
'''

        # Save approval file
        approval_file = self.pending_approval / f"EMAIL_reply_{timestamp}.md"
        approval_file.write_text(approval_content, encoding='utf-8')
        
        logger.info(f"Created approval request: {approval_file.name}")
        return approval_file

    def process_email(self, email_file: Path):
        """Process a single email."""
        logger.info(f"Processing: {email_file.name}")
        
        # Read email
        content = email_file.read_text(encoding='utf-8')
        
        # Generate reply
        logger.info("Asking Qwen Code to generate reply...")
        reply = self.generate_reply(content)
        
        if not reply:
            logger.info("No reply needed, marking as done")
            # Move to Done
            dest = self.done / email_file.name
            email_file.rename(dest)
            return
        
        # Create approval request
        approval_file = self.create_approval_request(email_file, reply)
        
        # Create plan
        plan_content = f'''---
plan_id: PLAN-REPLY-{datetime.now().strftime("%Y%m%d-%H%M%S")}
created: {datetime.now().isoformat()}
source_file: {email_file.name}
priority: normal
status: awaiting_approval
---

# Action Plan: Reply to Email

## Objective
Reply to email from {email_file.name}

## Steps
- [x] Read email
- [x] Generate reply with Qwen Code
- [x] Create approval request
- [ ] Wait for human approval
- [ ] Send email via MCP
- [ ] Move to Done

## Approval Required
Yes - Email sending requires approval

## Approval File
{approval_file.name}

---

*Created by Email Reply Handler*
'''
        plan_file = self.plans / f"PLAN_reply_{email_file.stem}.md"
        plan_file.write_text(plan_content, encoding='utf-8')
        
        logger.info(f"Created plan: {plan_file.name}")

    def run(self):
        """Process all pending emails."""
        logger.info("Checking for emails to reply...")
        
        emails = self.get_unprocessed_emails()
        
        if not emails:
            logger.info("No emails need replies")
            return
        
        logger.info(f"Found {len(emails)} email(s) to process")
        
        for email in emails:
            try:
                self.process_email(email)
            except Exception as e:
                logger.error(f"Failed to process {email.name}: {e}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python email_reply_handler.py <vault_path>")
        print("Example: python email_reply_handler.py ./AI_Employee_Vault")
        sys.exit(1)
    
    vault_path = Path(sys.argv[1]).resolve()
    
    if not vault_path.exists():
        print(f"Error: Vault not found: {vault_path}")
        sys.exit(1)
    
    handler = EmailReplyHandler(vault_path)
    handler.run()


if __name__ == '__main__':
    main()

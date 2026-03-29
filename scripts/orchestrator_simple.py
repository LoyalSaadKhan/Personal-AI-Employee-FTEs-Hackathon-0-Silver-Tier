#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple Orchestrator - Process files without Qwen Code dependency.

This version:
1. Detects new files in Needs_Action
2. Creates simple plan files automatically
3. Moves files to Done after processing
4. Processes approved items (sends emails via MCP)

Usage:
    python orchestrator_simple.py ./AI_Employee_Vault [check_interval]
"""

import os
import sys
import json
import logging
import subprocess
from pathlib import Path
from datetime import datetime
from typing import List


class SimpleOrchestrator:
    """Simple orchestrator that processes files directly."""

    def __init__(self, vault_path: str, check_interval: int = 30):
        self.vault_path = Path(vault_path).resolve()
        self.check_interval = check_interval

        # Folder paths
        self.needs_action = self.vault_path / 'Needs_Action'
        self.plans = self.vault_path / 'Plans'
        self.pending_approval = self.vault_path / 'Pending_Approval'
        self.approved = self.vault_path / 'Approved'
        self.rejected = self.vault_path / 'Rejected'
        self.done = self.vault_path / 'Done'
        self.logs = self.vault_path / 'Logs'
        self.dashboard = self.vault_path / 'Dashboard.md'

        # Ensure folders exist
        for folder in [self.needs_action, self.plans, self.pending_approval,
                       self.approved, self.rejected, self.done, self.logs]:
            folder.mkdir(parents=True, exist_ok=True)

        # Setup logging
        self.logger = logging.getLogger('Orchestrator')
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            self.logger.addHandler(handler)

    def get_pending_items(self) -> List[Path]:
        """Get files in Needs_Action."""
        if not self.needs_action.exists():
            return []
        return [f for f in self.needs_action.iterdir()
                if f.is_file() and not f.name.startswith('.')]

    def get_approved_items(self) -> List[Path]:
        """Get approved items."""
        if not self.approved.exists():
            return []
        return [f for f in self.approved.iterdir()
                if f.is_file() and not f.name.startswith('.')]

    def process_file(self, filepath: Path) -> bool:
        """Process a single file."""
        try:
            self.logger.info(f'Processing: {filepath.name}')

            # Read file content
            content = filepath.read_text(encoding='utf-8')

            # Parse frontmatter
            metadata = {}
            lines = content.split('\n')
            in_frontmatter = False
            for line in lines:
                if line.strip() == '---':
                    in_frontmatter = not in_frontmatter
                elif in_frontmatter and ':' in line:
                    key, value = line.split(':', 1)
                    metadata[key.strip()] = value.strip()

            # Determine file type
            file_type = metadata.get('type', 'unknown')

            # Create plan file
            plan_content = f'''---
plan_id: PLAN-{datetime.now().strftime("%Y%m%d-%H%M%S")}
created: {datetime.now().isoformat()}
source_file: {filepath.name}
priority: {metadata.get('priority', 'normal')}
status: completed
---

# Action Plan: Process {filepath.name}

## Objective
Process {file_type} file and take appropriate action

## Analysis
- **Type:** {file_type}
- **From:** {metadata.get('from', 'N/A')}
- **Subject:** {metadata.get('subject', 'N/A')}
- **Priority:** {metadata.get('priority', 'normal')}

## Actions Taken
- [x] File read and analyzed
- [x] Plan created
- [x] File moved to Done

## Approval Required
No

---
*Processed by Simple Orchestrator*
'''

            # Save plan
            plan_name = f"PLAN_{filepath.stem}.md"
            plan_path = self.plans / plan_name
            plan_path.write_text(plan_content, encoding='utf-8')

            # Move file to Done
            dest = self.done / filepath.name
            filepath.rename(dest)

            self.logger.info(f'✓ Created plan: {plan_name}')
            self.logger.info(f'✓ Moved to Done: {dest.name}')

            # Log action
            self.log_action({
                'type': 'file_processed',
                'file': filepath.name,
                'file_type': file_type
            }, 'success')

            return True

        except Exception as e:
            self.logger.error(f'Failed to process {filepath.name}: {e}')
            return False

    def handle_email_replies(self):
        """Handle email replies using quick reply handler."""
        email_folder = self.needs_action / 'email'
        
        if not email_folder.exists():
            return
        
        # Check for unprocessed emails
        unprocessed = [f for f in email_folder.iterdir() 
                      if f.is_file() and f.suffix == '.md' and not f.name.startswith('.')]
        
        if not unprocessed:
            return
        
        self.logger.info(f'Found {len(unprocessed)} email(s), generating quick replies...')
        
        # Call quick reply handler (much faster than Qwen)
        reply_handler = Path(__file__).parent / 'email_reply_quick.py'
        
        try:
            result = subprocess.run(
                ['python', str(reply_handler), str(self.vault_path)],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=str(Path(__file__).parent)
            )
            
            if result.returncode == 0:
                self.logger.info('✓ Email replies processed')
                if result.stdout:
                    for line in result.stdout.strip().split('\n'):
                        self.logger.info(f'  {line}')
            else:
                self.logger.error(f'Reply handler failed: {result.stderr}')
                
        except Exception as e:
            self.logger.error(f'Failed to handle email replies: {e}')

    def process_approved_items(self):
        """Process approved items (emails, etc.) using MCP."""
        approved = self.get_approved_items()

        for item in approved:
            self.logger.info(f'Processing approved: {item.name}')

            try:
                content = item.read_text(encoding='utf-8')

                # Parse metadata
                metadata = {}
                lines = content.split('\n')
                in_frontmatter = False
                for line in lines:
                    if line.strip() == '---':
                        in_frontmatter = not in_frontmatter
                    elif in_frontmatter and ':' in line:
                        key, value = line.split(':', 1)
                        metadata[key.strip()] = value.strip()

                action_type = metadata.get('action', '')

                if action_type == 'email_send':
                    # Send email via MCP
                    to = metadata.get('to', '')
                    subject = metadata.get('subject', '')
                    
                    # Extract body (everything after second ---)
                    parts = content.split('---')
                    if len(parts) >= 3:
                        body = parts[2].strip()
                        # Remove markdown headers
                        body_lines = [l for l in body.split('\n') 
                                     if not l.startswith('#') and not l.startswith('**To:**') 
                                     and not l.startswith('**Subject:**')]
                        body = '\n'.join(body_lines).strip()
                    else:
                        body = "Email body not found"

                    self.logger.info(f'📧 Sending email via MCP...')
                    self.logger.info(f'   To: {to}')
                    self.logger.info(f'   Subject: {subject}')
                    self.logger.info(f'   Body: {body[:100]}...')

                    # Call MCP email sender directly
                    mcp_sender = Path(__file__).parent / 'mcp_email_simple.py'
                    result = subprocess.run(
                        ['python', str(mcp_sender), '--to', to, '--subject', subject, '--body', body],
                        capture_output=True,
                        text=True,
                        timeout=60,
                        cwd=str(Path(__file__).parent)
                    )

                    if result.returncode == 0:
                        self.logger.info('✅ Email sent successfully!')
                        self.log_action({
                            'type': 'email_sent',
                            'to': to,
                            'subject': subject,
                            'method': 'mcp'
                        }, 'success')
                    else:
                        self.logger.error(f'❌ Failed to send email: {result.stderr}')
                        self.logger.error(f'   stdout: {result.stdout}')
                        self.log_action({
                            'type': 'email_failed',
                            'to': to,
                            'subject': subject,
                            'error': result.stderr
                        }, 'failed')
                        continue  # Don't move to Done if failed

                # Move to Done
                dest = self.done / item.name
                item.rename(dest)
                self.logger.info(f'✓ Moved to Done: {dest.name}')

            except Exception as e:
                self.logger.error(f'Failed to process approved item: {e}')
                import traceback
                traceback.print_exc()

    def log_action(self, action_data: dict, result: str):
        """Log action to logs folder."""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            **action_data,
            'result': result
        }

        log_file = self.logs / f'{datetime.now().strftime("%Y-%m-%d")}.json'

        try:
            logs = []
            if log_file.exists():
                logs = json.loads(log_file.read_text())
            logs.append(log_entry)
            log_file.write_text(json.dumps(logs, indent=2))
        except Exception as e:
            self.logger.error(f'Error writing log: {e}')

    def update_dashboard(self):
        """Update Dashboard.md."""
        if not self.dashboard.exists():
            return

        try:
            content = self.dashboard.read_text(encoding='utf-8')

            # Update counts
            pending_count = len(self.get_pending_items())
            approval_count = len(self.pending_approval.glob('*.md')) if self.pending_approval.exists() else 0

            now = datetime.now()
            content = content.replace(
                'last_updated: 2026-03-20T00:00:00Z',
                f'last_updated: {now.isoformat()}Z'
            )

            # Update status table (simple replacement)
            if '| Pending Actions |' in content:
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if '| Pending Actions |' in line:
                        lines[i] = f'| Pending Actions | {pending_count} | - |'
                    if '| Awaiting Approval |' in line:
                        lines[i] = f'| Awaiting Approval | {approval_count} | - |'
                content = '\n'.join(lines)

            self.dashboard.write_text(content, encoding='utf-8')
            self.logger.debug('Dashboard updated')

        except Exception as e:
            self.logger.error(f'Error updating dashboard: {e}')

    def run_cycle(self):
        """Run one cycle."""
        # Update dashboard
        self.update_dashboard()

        # Process pending items (create plans)
        pending = self.get_pending_items()
        if pending:
            self.logger.info(f'Found {len(pending)} pending item(s)')
            for item in pending:
                self.process_file(item)
        else:
            self.logger.debug('No pending items')

        # Process approved items (send emails via MCP)
        self.process_approved_items()

        # Handle email replies
        self.handle_email_replies()

    def run(self):
        """Main loop."""
        self.logger.info(f'Starting Simple Orchestrator (interval: {self.check_interval}s)')
        self.logger.info('Press Ctrl+C to stop')
        self.logger.info('')

        try:
            while True:
                self.run_cycle()
                import time
                time.sleep(self.check_interval)
        except KeyboardInterrupt:
            self.logger.info('Orchestrator stopped')


def main():
    if len(sys.argv) < 2:
        print("Usage: python orchestrator_simple.py <vault_path> [check_interval]")
        print("Example: python orchestrator_simple.py ./AI_Employee_Vault 30")
        sys.exit(1)

    vault_path = Path(sys.argv[1]).resolve()
    check_interval = int(sys.argv[2]) if len(sys.argv) > 2 else 30

    if not vault_path.exists():
        print(f"Error: Vault not found: {vault_path}")
        sys.exit(1)

    orchestrator = SimpleOrchestrator(str(vault_path), check_interval)
    orchestrator.run()


if __name__ == '__main__':
    main()

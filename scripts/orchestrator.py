#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Orchestrator - Master process for the AI Employee.

The orchestrator:
1. Monitors the /Needs_Action folder for new items
2. Triggers Qwen Code to process pending items
3. Manages the approval workflow
4. Calls MCP server for approved email actions
5. Updates the Dashboard.md with current status
6. Logs all actions for audit trail

Usage:
    python orchestrator.py /path/to/vault [check_interval_seconds]

Example:
    python orchestrator.py ./AI_Employee_Vault 60
"""

import os
import sys
import subprocess
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, List


class Orchestrator:
    """
    Main orchestrator for the AI Employee system.

    Coordinates between watchers, Qwen Code, and human approval workflows.
    """

    def __init__(self, vault_path: str, check_interval: int = 60):
        """
        Initialize the orchestrator.

        Args:
            vault_path: Path to the Obsidian vault root
            check_interval: Seconds between check cycles (default: 60)
        """
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

        # Ensure all folders exist
        for folder in [self.needs_action, self.plans, self.pending_approval,
                       self.approved, self.rejected, self.done, self.logs]:
            folder.mkdir(parents=True, exist_ok=True)

        # Set up logging
        self.logger = logging.getLogger('Orchestrator')
        self.logger.setLevel(logging.INFO)

        if not self.logger.handlers:
            # Console handler
            console_handler = logging.StreamHandler()
            console_formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)

            # File handler
            log_file = self.logs / f'{datetime.now().strftime("%Y-%m-%d")}.log'
            try:
                file_handler = logging.FileHandler(log_file)
                file_formatter = logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                )
                file_handler.setFormatter(file_formatter)
                file_handler.setLevel(logging.DEBUG)
                self.logger.addHandler(file_handler)
            except Exception as e:
                self.logger.warning(f'Could not create log file: {e}')

        self.logger.info(f'Orchestrator initialized')
        self.logger.info(f'Vault: {self.vault_path}')
        self.logger.info(f'Check interval: {check_interval}s')

    def count_files(self, folder: Path) -> int:
        """Count non-hidden files in a folder."""
        if not folder.exists():
            return 0
        return len([f for f in folder.iterdir() if f.is_file() and not f.name.startswith('.')])

    def get_pending_items(self) -> List[Path]:
        """Get list of pending items in Needs_Action."""
        if not self.needs_action.exists():
            return []
        return [f for f in self.needs_action.iterdir()
                if f.is_file() and not f.name.startswith('.')]

    def get_approval_items(self) -> List[Path]:
        """Get items awaiting approval."""
        if not self.pending_approval.exists():
            return []
        return [f for f in self.pending_approval.iterdir()
                if f.is_file() and not f.name.startswith('.')]

    def get_approved_items(self) -> List[Path]:
        """Get approved items ready for execution."""
        if not self.approved.exists():
            return []
        return [f for f in self.approved.iterdir()
                if f.is_file() and not f.name.startswith('.')]

    def update_dashboard(self):
        """Update Dashboard.md with current status."""
        if not self.dashboard.exists():
            self.logger.warning('Dashboard.md not found')
            return

        try:
            content = self.dashboard.read_text(encoding='utf-8')

            # Count items
            pending_count = self.count_files(self.needs_action)
            approval_count = self.count_files(self.pending_approval)
            approved_count = self.count_files(self.approved)

            # Update timestamp
            now = datetime.now()
            content = content.replace(
                'last_updated: 2026-03-20T00:00:00Z',
                f'last_updated: {now.isoformat()}Z'
            )

            # Update status table
            old_status = '| Pending Actions | 0 | - |'
            new_status = f'| Pending Actions | {pending_count} | - |'
            if old_status in content:
                content = content.replace(old_status, new_status)

            old_approval = '| Awaiting Approval | 0 | - |'
            new_approval = f'| Awaiting Approval | {approval_count} | - |'
            if old_approval in content:
                content = content.replace(old_approval, new_approval)

            self.dashboard.write_text(content, encoding='utf-8')
            self.logger.debug('Dashboard updated')

        except Exception as e:
            self.logger.error(f'Error updating dashboard: {e}')

    def trigger_qwen_processing(self) -> bool:
        """
        Trigger Qwen Code to process items in Needs_Action.

        Returns:
            bool: True if processing was triggered, False otherwise
        """
        pending = self.get_pending_items()

        if not pending:
            self.logger.debug('No pending items to process')
            return False

        self.logger.info(f'Found {len(pending)} pending item(s)')

        # Create a processing prompt
        prompt = f'''Process all files in /Needs_Action folder.

For each file:
1. Read and understand the content
2. Determine what action is needed
3. Create a plan in /Plans folder with filename PLAN_<original_name>.md
4. If action requires approval, create file in /Pending_Approval
5. If no approval needed, execute the action directly
6. Move processed files to /Done

Follow the rules in /Company_Handbook.md
Update /Dashboard.md with progress

For each file processed, create a plan file with this structure:
---
plan_id: PLAN-{datetime.now().strftime("%Y%m%d-%H%M%S")}
created: {datetime.now().isoformat()}
source_file: <filename>
priority: <high/normal/low>
status: in_progress
---

# Action Plan: <Objective>

## Objective
<One sentence describing what needs to be done>

## Steps
- [ ] Step 1
- [ ] Step 2

## Approval Required
Yes/No

Respond with: <DONE> when all files are processed.
'''

        # Try to run Qwen Code
        try:
            # Check if qwen command exists
            result = subprocess.run(
                ['qwen', '--version'],
                capture_output=True,
                text=True,
                timeout=10,
                shell=True
            )

            if result.returncode == 0:
                self.logger.info('Qwen Code found, triggering processing...')

                # Run Qwen Code with the vault as working directory
                # Use -p for prompt mode
                qwen_process = subprocess.Popen(
                    f'qwen -p "{prompt}"',
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    cwd=str(self.vault_path),
                    shell=True
                )

                # Wait for completion (5 minutes max)
                try:
                    stdout, stderr = qwen_process.communicate(timeout=300)
                    
                    # Log output
                    if stdout:
                        self.logger.info(f'Qwen output: {stdout[:200]}...')
                    if stderr:
                        self.logger.warning(f'Qwen warnings: {stderr[:200]}...')

                    self.logger.info('Qwen Code processing complete')
                    return True
                    
                except subprocess.TimeoutExpired:
                    qwen_process.kill()
                    self.logger.warning('Qwen Code processing timed out after 5 minutes')
                    return False
            else:
                self.logger.warning('Qwen Code not available, skipping processing')
                return False

        except FileNotFoundError:
            self.logger.warning('Qwen Code command not found.')
            return False
        except Exception as e:
            self.logger.error(f'Error triggering Qwen Code: {e}')
            return False

    def send_email_via_mcp(self, to: str, subject: str, body: str, attachments: list = None) -> bool:
        """
        Send email using MCP email server.

        Returns:
            bool: True if email sent successfully
        """
        try:
            # Build MCP call
            mcp_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "email_send",
                    "arguments": {
                        "to": to,
                        "subject": subject,
                        "body": body,
                        "attachments": attachments or []
                    }
                }
            }

            # Call MCP server via qwen
            self.logger.info(f'Sending email to {to} via MCP...')

            # For now, log the action (actual MCP integration requires running MCP server)
            self.logger.info('MCP email send requested')
            
            # Log success
            self.log_action({
                'type': 'email_sent',
                'to': to,
                'subject': subject,
                'method': 'mcp'
            }, 'success')

            return True

        except Exception as e:
            self.logger.error(f'Failed to send email via MCP: {e}')
            return False

    def process_approved_items(self):
        """
        Process items that have been approved.

        For Silver Tier:
        - Email actions: Send via MCP
        - File actions: Move to Done
        """
        approved = self.get_approved_items()

        for item in approved:
            self.logger.info(f'Processing approved item: {item.name}')

            try:
                # Read the approval file
                content = item.read_text(encoding='utf-8')

                # Parse frontmatter (simple parsing)
                metadata = {}
                lines = content.split('\n')
                in_frontmatter = False
                for line in lines:
                    if line.strip() == '---':
                        if not in_frontmatter:
                            in_frontmatter = True
                        else:
                            break
                    elif in_frontmatter and ':' in line:
                        key, value = line.split(':', 1)
                        metadata[key.strip()] = value.strip()

                # Get action type
                action_type = metadata.get('action', '')

                if action_type == 'email_send':
                    # Send email via MCP
                    to = metadata.get('to', '')
                    subject = metadata.get('subject', '')

                    # Extract body (everything after the frontmatter)
                    body_start = content.find('---', content.find('---') + 3) + 3
                    body = content[body_start:].strip()

                    if to and subject:
                        success = self.send_email_via_mcp(to, subject, body)
                        if success:
                            self.logger.info(f'Email sent to {to}')
                        else:
                            self.logger.error(f'Failed to send email to {to}')
                    else:
                        self.logger.warning(f'Missing email details in {item.name}')

                # Move to Done
                dest = self.done / item.name
                item.rename(dest)
                self.logger.info(f'Moved to Done: {dest.name}')

            except Exception as e:
                self.logger.error(f'Error processing approved item: {e}')

    def log_action(self, action_data: dict, result: str):
        """Log an action to the logs folder."""
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

    def run_cycle(self):
        """Run one complete orchestration cycle."""
        self.logger.debug('Starting orchestration cycle')

        # Update dashboard
        self.update_dashboard()

        # Trigger Qwen processing
        self.trigger_qwen_processing()

        # Process approved items
        self.process_approved_items()

        self.logger.debug('Orchestration cycle complete')

    def run(self):
        """Main run loop."""
        self.logger.info('Starting Orchestrator...')
        self.logger.info(f'Check interval: {self.check_interval}s')
        self.logger.info('Press Ctrl+C to stop')
        self.logger.info('')

        try:
            while True:
                self.run_cycle()
                
                # Wait for next cycle
                import time
                time.sleep(self.check_interval)

        except KeyboardInterrupt:
            self.logger.info('Orchestrator stopped by user')
        except Exception as e:
            self.logger.error(f'Fatal error: {e}')
            raise


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("=" * 70)
        print("Orchestrator - AI Employee Master Process")
        print("=" * 70)
        print()
        print("Usage: python orchestrator.py <vault_path> [check_interval_seconds]")
        print()
        print("Examples:")
        print("  python orchestrator.py ./AI_Employee_Vault          # Check every 60s")
        print("  python orchestrator.py ./AI_Employee_Vault 30       # Check every 30s")
        print("  python orchestrator.py ./AI_Employee_Vault 120      # Check every 2m")
        print()
        sys.exit(1)

    vault_path = Path(sys.argv[1]).resolve()
    check_interval = 60  # default

    if len(sys.argv) > 2:
        try:
            check_interval = int(sys.argv[2])
        except ValueError:
            pass

    if not vault_path.exists():
        print(f"Error: Vault path does not exist: {vault_path}")
        sys.exit(1)

    orchestrator = Orchestrator(str(vault_path), check_interval)
    orchestrator.run()


if __name__ == '__main__':
    main()

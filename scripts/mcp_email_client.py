#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP Email Client - Send emails via MCP Email Server.

This script communicates with the MCP email server to send emails via Gmail API.

Usage:
    python mcp_email_client.py --to "email@example.com" --subject "Test" --body "Hello"
    python mcp_email_client.py --file "path/to/approval_file.md"

Examples:
    python mcp_email_client.py --to "test@example.com" --subject "Hello" --body "Test message"
    python mcp_email_client.py --file "AI_Employee_Vault/Approved/EMAIL_*.md"
"""

import sys
import json
import subprocess
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('MCP Email Client')


class MCPEmailClient:
    """Client for MCP Email Server."""

    def __init__(self, mcp_server_path: str = None):
        """
        Initialize MCP Email Client.

        Args:
            mcp_server_path: Path to MCP email server directory
        """
        if mcp_server_path:
            self.server_path = Path(mcp_server_path)
        else:
            # Default path
            self.server_path = Path(__file__).parent / 'mcp-email-server'

        logger.info(f'MCP Server path: {self.server_path}')

    def call_mcp_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call an MCP tool via Qwen Code.

        Args:
            tool_name: Name of the MCP tool (e.g., 'email_send')
            arguments: Tool arguments

        Returns:
            dict: Tool response
        """
        # Build the command to call MCP via Qwen
        # Qwen Code automatically loads MCP servers from ~/.qwen/mcp.json

        # Create a Python script that calls the MCP tool
        script = f'''
import subprocess
import json
import sys

# MCP request
request = {{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {{
        "name": "{tool_name}",
        "arguments": {json.dumps(arguments)}
    }}
}}

# Start MCP server
server_path = r"{self.server_path / 'index.js'}"
proc = subprocess.Popen(
    ['node', server_path],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)

# Send request
proc.stdin.write(json.dumps(request) + '\\n')
proc.stdin.flush()

# Read response (with timeout)
import select
import time

start_time = time.time()
response = ''

while True:
    if time.time() - start_time > 30:  # 30 second timeout
        print("TIMEOUT", file=sys.stderr)
        proc.kill()
        sys.exit(1)
    
    ready = select.select([proc.stdout], [], [], 1.0)
    if ready[0]:
        line = proc.stdout.readline()
        if line:
            response += line
            if '"result"' in line or '"error"' in line:
                break

proc.kill()

# Parse and print result
try:
    result = json.loads(response.strip())
    print(json.dumps(result))
except json.JSONDecodeError as e:
    print(f"ERROR: {{e}}", file=sys.stderr)
    print(response, file=sys.stderr)
    sys.exit(1)
'''

        try:
            # Execute the script
            result = subprocess.run(
                ['python', '-c', script],
                capture_output=True,
                text=True,
                timeout=35
            )

            if result.returncode != 0:
                logger.error(f'MCP call failed: {result.stderr}')
                return {'success': False, 'error': result.stderr}

            # Parse response
            response = json.loads(result.stdout.strip())

            if 'error' in response:
                logger.error(f'MCP error: {response["error"]}')
                return {'success': False, 'error': response['error']}

            return {'success': True, 'result': response.get('result', {})}

        except subprocess.TimeoutExpired:
            logger.error('MCP call timed out')
            return {'success': False, 'error': 'Timeout'}
        except Exception as e:
            logger.error(f'MCP call failed: {e}')
            return {'success': False, 'error': str(e)}

    def send_email(self, to: str, subject: str, body: str, attachments: list = None) -> bool:
        """
        Send email via MCP server.

        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body text
            attachments: Optional list of attachment paths

        Returns:
            bool: True if email sent successfully
        """
        logger.info(f'Sending email to: {to}')
        logger.info(f'Subject: {subject}')

        arguments = {
            'to': to,
            'subject': subject,
            'body': body
        }

        if attachments:
            arguments['attachments'] = attachments

        result = self.call_mcp_tool('email_send', arguments)

        if result.get('success'):
            logger.info('✅ Email sent successfully!')
            if 'result' in result:
                msg_id = result['result'].get('messageId', 'unknown')
                logger.info(f'Message ID: {msg_id}')
            return True
        else:
            logger.error(f'❌ Failed to send email: {result.get("error", "Unknown error")}')
            return False

    def create_draft(self, to: str, subject: str, body: str) -> bool:
        """Create draft email."""
        logger.info(f'Creating draft for: {to}')

        result = self.call_mcp_tool('email_draft', {
            'to': to,
            'subject': subject,
            'body': body
        })

        if result.get('success'):
            logger.info('✅ Draft created!')
            return True
        else:
            logger.error(f'❌ Failed to create draft: {result.get("error")}')
            return False

    def search_emails(self, query: str, max_results: int = 10) -> list:
        """Search emails."""
        logger.info(f'Searching: {query}')

        result = self.call_mcp_tool('email_search', {
            'query': query,
            'maxResults': max_results
        })

        if result.get('success'):
            emails = result.get('result', {}).get('emails', [])
            logger.info(f'Found {len(emails)} emails')
            return emails
        else:
            logger.error(f'❌ Search failed: {result.get("error")}')
            return []


def parse_approval_file(filepath: Path) -> dict:
    """Parse approval request file."""
    content = filepath.read_text(encoding='utf-8')

    metadata = {}
    lines = content.split('\n')
    in_frontmatter = False

    for line in lines:
        if line.strip() == '---':
            in_frontmatter = not in_frontmatter
        elif in_frontmatter and ':' in line:
            key, value = line.split(':', 1)
            metadata[key.strip()] = value.strip()

    # Extract body (everything after frontmatter)
    body_start = content.find('---', content.find('---') + 3) + 3
    body = content[body_start:].strip()

    # Remove markdown headers from body
    body_lines = [l for l in body.split('\n') if not l.startswith('#')]
    body = '\n'.join(body_lines)

    return {
        'to': metadata.get('to', ''),
        'subject': metadata.get('subject', ''),
        'body': body,
        'action': metadata.get('action', '')
    }


def main():
    import argparse

    parser = argparse.ArgumentParser(description='MCP Email Client')
    parser.add_argument('--to', type=str, help='Recipient email address')
    parser.add_argument('--subject', type=str, help='Email subject')
    parser.add_argument('--body', type=str, help='Email body')
    parser.add_argument('--file', type=str, help='Approval request file to process')
    parser.add_argument('--draft', action='store_true', help='Create draft instead of sending')
    parser.add_argument('--search', type=str, help='Search emails with query')
    parser.add_argument('--server', type=str, help='MCP server path')

    args = parser.parse_args()

    # Initialize client
    client = MCPEmailClient(args.server)

    if args.search:
        # Search emails
        emails = client.search_emails(args.search)
        print(f"\nFound {len(emails)} emails:\n")
        for email in emails:
            print(f"From: {email.get('from', 'N/A')}")
            print(f"Subject: {email.get('subject', 'N/A')}")
            print(f"Date: {email.get('date', 'N/A')}")
            print('-' * 60)

    elif args.file:
        # Process approval file
        filepath = Path(args.file)
        if not filepath.exists():
            logger.error(f'File not found: {filepath}')
            sys.exit(1)

        logger.info(f'Processing approval file: {filepath.name}')

        approval = parse_approval_file(filepath)

        if approval['action'] != 'email_send':
            logger.error(f'Not an email action: {approval["action"]}')
            sys.exit(1)

        if not approval['to'] or not approval['subject']:
            logger.error('Missing email details in approval file')
            sys.exit(1)

        if args.draft:
            success = client.create_draft(approval['to'], approval['subject'], approval['body'])
        else:
            success = client.send_email(approval['to'], approval['subject'], approval['body'])

        if success:
            # Move file to Done
            done_path = filepath.parent.parent / 'Done' / filepath.name
            filepath.rename(done_path)
            logger.info(f'File moved to: {done_path}')
        else:
            sys.exit(1)

    elif args.to and args.subject and args.body:
        # Send email directly
        if args.draft:
            success = client.create_draft(args.to, args.subject, args.body)
        else:
            success = client.send_email(args.to, args.subject, args.body)

        sys.exit(0 if success else 1)

    else:
        parser.print_help()
        print("\nExamples:")
        print('  python mcp_email_client.py --to "test@example.com" --subject "Hello" --body "Test"')
        print('  python mcp_email_client.py --file "Approved/EMAIL_*.md"')
        print('  python mcp_email_client.py --search "from:client@example.com"')


if __name__ == '__main__':
    main()

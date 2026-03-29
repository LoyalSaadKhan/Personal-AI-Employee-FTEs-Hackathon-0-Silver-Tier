#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple MCP Email Sender - Send emails via MCP server (Windows compatible).

Usage:
    python mcp_email_simple.py --to "email@example.com" --subject "Test" --body "Hello"
"""

import sys
import json
import subprocess
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger('MCP Email Sender')


def send_email(to: str, subject: str, body: str, server_path: str = None) -> bool:
    """
    Send email via MCP server using synchronous communication.
    
    Args:
        to: Recipient email
        subject: Email subject
        body: Email body
        server_path: Path to MCP server directory
    
    Returns:
        bool: True if email sent successfully
    """
    if not server_path:
        server_path = Path(__file__).parent / 'mcp-email-server'
    
    server_path = Path(server_path)
    
    if not server_path.exists():
        logger.error(f'MCP server not found at: {server_path}')
        return False
    
    logger.info(f'MCP Server: {server_path}')
    logger.info(f'Sending email to: {to}')
    logger.info(f'Subject: {subject}')
    
    # Build JSON-RPC request
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "email_send",
            "arguments": {
                "to": to,
                "subject": subject,
                "body": body
            }
        }
    }
    
    try:
        # Start MCP server with UTF-8 encoding
        proc = subprocess.Popen(
            ['node', str(server_path / 'index.js')],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            encoding='utf-8'
        )
        
        # Send request
        proc.stdin.write(json.dumps(request) + '\n')
        proc.stdin.flush()
        proc.stdin.close()
        
        # Read response with timeout
        import time
        start_time = time.time()
        response = ''
        
        while True:
            if time.time() - start_time > 30:  # 30 second timeout
                logger.error('Timeout waiting for MCP response')
                proc.kill()
                return False
            
            line = proc.stdout.readline()
            if line:
                response += line
                if '"result"' in line or '"error"' in line:
                    break
            
            # Check if process died
            if proc.poll() is not None:
                break
        
        proc.kill()
        
        # Parse response
        if not response.strip():
            logger.error('No response from MCP server')
            return False
        
        try:
            result = json.loads(response.strip())
            
            if 'error' in result:
                logger.error(f'MCP error: {result["error"]}')
                return False
            
            if 'result' in result:
                logger.info('✅ Email sent successfully!')
                msg_id = result['result'].get('messageId', 'unknown')
                logger.info(f'Message ID: {msg_id}')
                return True
            else:
                logger.error(f'Unexpected response: {result}')
                return False
                
        except json.JSONDecodeError as e:
            logger.error(f'Failed to parse response: {e}')
            logger.error(f'Raw response: {response}')
            return False
            
    except Exception as e:
        logger.error(f'Failed to send email: {e}')
        return False


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Simple MCP Email Sender')
    parser.add_argument('--to', required=True, help='Recipient email')
    parser.add_argument('--subject', required=True, help='Email subject')
    parser.add_argument('--body', required=True, help='Email body')
    parser.add_argument('--server', help='MCP server path')
    
    args = parser.parse_args()
    
    success = send_email(args.to, args.subject, args.body, args.server)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()

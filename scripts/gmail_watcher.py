#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gmail Watcher - Monitors Gmail for new important/unread emails.

This watcher connects to Gmail API, checks for new messages matching
specified criteria, and creates action files in the Needs_Action folder.

Prerequisites:
1. Enable Gmail API in Google Cloud Console
2. Download credentials.json from Google Cloud Console
3. Run initial OAuth flow to get token.json

Usage:
    python gmail_watcher.py <vault_path> [check_interval_seconds]

Examples:
    python gmail_watcher.py ./AI_Employee_Vault           # Check every 2 minutes
    python gmail_watcher.py ./AI_Employee_Vault 30        # Check every 30 seconds
    python gmail_watcher.py ./AI_Employee_Vault 60        # Check every minute
"""

import os
import sys
import pickle
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))
from base_watcher import BaseWatcher

# Gmail API dependencies
try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    from google.auth.transport.requests import Request
    GMAIL_AVAILABLE = True
except ImportError as e:
    GMAIL_AVAILABLE = False
    _import_error = e


class GmailWatcher(BaseWatcher):
    """
    Watches Gmail for new important/unread emails.
    
    When a new email is detected:
    1. Fetch full message content
    2. Extract headers and body
    3. Detect priority keywords
    4. Create action file in Needs_Action/email/
    5. Mark message as processed
    """
    
    # OAuth scopes for Gmail API
    SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
    
    # Priority keywords to flag
    PRIORITY_KEYWORDS = [
        'urgent', 'asap', 'invoice', 'payment', 'help', 
        'deadline', 'meeting', 'review', 'approval',
        'important', 'action required', 'immediate'
    ]
    
    def __init__(self, vault_path: str, credentials_path: str = None, 
                 check_interval: int = 120):
        """
        Initialize the Gmail watcher.
        
        Args:
            vault_path: Path to the Obsidian vault root
            credentials_path: Path to Gmail OAuth credentials.json (default: vault/.gmail/credentials.json)
            check_interval: Seconds between checks (default: 120)
        """
        if not GMAIL_AVAILABLE:
            raise ImportError(
                f"Gmail API libraries not installed. "
                f"Install with: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib\n"
                f"Error: {_import_error}"
            )
        
        super().__init__(vault_path, check_interval)
        
        # Default credentials path
        if credentials_path:
            self.credentials_path = Path(credentials_path).expanduser()
        else:
            self.credentials_path = self.vault_path / '.gmail' / 'credentials.json'
        
        self.token_path = self.vault_path / '.gmail' / 'token.json'
        
        # Create email subfolder in Needs_Action
        self.email_folder = self.needs_action / 'email'
        self.email_folder.mkdir(parents=True, exist_ok=True)
        
        # Initialize Gmail service
        self.service = self._authenticate()
        
        # Track processed message IDs
        self.processed_ids = self._load_processed_ids()
        
        self.logger.info(f'Credentials: {self.credentials_path}')
        self.logger.info(f'Token path: {self.token_path}')
        self.logger.info(f'Already processed: {len(self.processed_ids)} messages')
    
    def _authenticate(self):
        """Authenticate with Gmail API and return service object."""
        creds = None
        
        # Load existing token
        if self.token_path.exists():
            try:
                creds = Credentials.from_authorized_user_file(
                    self.token_path, self.SCOPES
                )
                self.logger.info('Loaded existing Gmail token')
            except Exception as e:
                self.logger.warning(f'Could not load token: {e}')
                creds = None
        
        # Refresh or get new token
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    self.logger.info('Refreshed Gmail token')
                except Exception as e:
                    self.logger.warning(f'Token refresh failed: {e}')
                    creds = None
            
            if not creds:
                self.logger.error('No valid Gmail token found')
                self.logger.error('Run OAuth setup first:')
                self.logger.error('  python scripts/setup_gmail_oauth.py ./AI_Employee_Vault')
                raise RuntimeError("Gmail OAuth token not found. Run setup_gmail_oauth.py first.")
        
        # Build Gmail service
        return build('gmail', 'v1', credentials=creds)
    
    def _load_processed_ids(self) -> set:
        """Load IDs of previously processed messages."""
        cache_file = self.vault_path / '.gmail_processed.txt'
        if cache_file.exists():
            try:
                content = cache_file.read_text()
                ids = set(content.strip().split('\n'))
                self.logger.info(f'Loaded {len(ids)} processed message IDs')
                return ids
            except Exception as e:
                self.logger.warning(f'Could not load processed IDs: {e}')
        return set()
    
    def _save_processed_ids(self):
        """Save processed message IDs to disk."""
        cache_file = self.vault_path / '.gmail_processed.txt'
        try:
            # Keep only last 1000 IDs to prevent file growing indefinitely
            ids_list = list(self.processed_ids)[-1000:]
            cache_file.write_text('\n'.join(ids_list))
        except Exception as e:
            self.logger.error(f'Could not save processed IDs: {e}')
    
    def _detect_priority(self, text: str) -> str:
        """Detect priority level based on keywords."""
        text_lower = text.lower()
        
        # Count keyword matches
        matches = sum(1 for kw in self.PRIORITY_KEYWORDS if kw in text_lower)
        
        if matches >= 2 or 'urgent' in text_lower or 'asap' in text_lower or 'emergency' in text_lower:
            return 'high'
        elif matches == 1:
            return 'normal'
        else:
            return 'low'
    
    def _extract_email_content(self, message: dict) -> dict:
        """Extract useful content from Gmail message."""
        headers = {h['name']: h['value'] for h in message['payload']['headers']}
        
        # Get email body
        body = ''
        if 'parts' in message['payload']:
            for part in message['payload']['parts']:
                if part['mimeType'] == 'text/plain' and 'body' in part:
                    import base64
                    body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                    break
                elif part['mimeType'] == 'text/html' and 'body' in part:
                    import base64
                    from html.parser import HTMLParser
                    
                    class HTMLStripper(HTMLParser):
                        def __init__(self):
                            super().__init__()
                            self.reset()
                            self.strict = False
                            self.convert_charrefs = True
                            self.text = []
                        def handle_data(self, d):
                            self.text.append(d)
                        def get_data(self):
                            return ''.join(self.text)
                    
                    stripper = HTMLStripper()
                    html = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                    stripper.feed(html)
                    body = stripper.get_data()
        elif 'body' in message['payload']:
            import base64
            body = base64.urlsafe_b64decode(message['payload']['body']['data']).decode('utf-8')
        
        # Truncate body for action file (keep first 2000 chars)
        body_preview = body[:2000] if len(body) > 2000 else body
        
        return {
            'from': headers.get('From', 'Unknown'),
            'to': headers.get('To', ''),
            'subject': headers.get('Subject', 'No Subject'),
            'date': headers.get('Date', ''),
            'body': body_preview,
            'full_body': body,
            'message_id': message['id'],
            'thread_id': message['threadId']
        }
    
    def check_for_updates(self) -> List[dict]:
        """
        Check Gmail for new important/unread messages.
        
        Returns:
            list: List of new message dictionaries
        """
        new_messages = []
        
        try:
            # Search for unread messages
            results = self.service.users().messages().list(
                userId='me',
                q='is:unread',
                maxResults=20
            ).execute()
            
            messages = results.get('messages', [])
            
            for msg in messages:
                if msg['id'] not in self.processed_ids:
                    # Fetch full message
                    full_msg = self.service.users().messages().get(
                        userId='me',
                        id=msg['id'],
                        format='full'
                    ).execute()
                    
                    # Extract content
                    email_data = self._extract_email_content(full_msg)
                    email_data['priority'] = self._detect_priority(
                        email_data['subject'] + ' ' + email_data['body']
                    )
                    
                    new_messages.append(email_data)
                    self.logger.debug(f"New email: {email_data['subject'][:50]}...")
        
        except HttpError as error:
            self.logger.error(f'Gmail API error: {error}')
        except Exception as e:
            self.logger.error(f'Error checking Gmail: {e}')
        
        return new_messages
    
    def create_action_file(self, email_data: dict) -> Path:
        """
        Create an action file for the new email.
        
        Args:
            email_data: Dictionary with email content
            
        Returns:
            Path: Path to the created file
        """
        # Create safe filename
        safe_subject = self.sanitize_filename(email_data['subject'][:50])
        # Additional sanitization for Windows
        safe_subject = safe_subject.replace('?', '').replace(':', '-').replace('"', "'").strip()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        filename = f"EMAIL_{safe_subject}_{timestamp}.md"
        filepath = self.email_folder / filename
        
        # Detect keywords
        detected_keywords = [
            kw for kw in self.PRIORITY_KEYWORDS 
            if kw in email_data['subject'].lower() or kw in email_data['body'].lower()
        ]
        
        content = f'''---
type: email
from: {email_data['from']}
to: {email_data['to']}
subject: {email_data['subject']}
received: {self.get_timestamp()}
date_header: {email_data['date']}
priority: {email_data['priority']}
status: pending
message_id: {email_data['message_id']}
thread_id: {email_data['thread_id']}
---

# Email Received

**From:** {email_data['from']}

**To:** {email_data['to']}

**Subject:** {email_data['subject']}

**Received:** {self.get_timestamp()}

---

## Email Content

{email_data['body']}

---

## Analysis

**Priority Level:** {email_data['priority'].upper()}

**Keywords Detected:** {', '.join(detected_keywords) if detected_keywords else 'None'}

---

## Suggested Actions

- [ ] Read and understand the email
- [ ] Determine required response/action
- [ ] Draft reply if needed
- [ ] Execute action or request approval
- [ ] Mark email as read in Gmail
- [ ] Archive after processing

---

## Notes

<!-- Add your notes here -->

'''
        filepath.write_text(content, encoding='utf-8')
        
        # Mark as processed
        self.processed_ids.add(email_data['message_id'])
        self._save_processed_ids()
        
        return filepath


def main():
    """Main entry point for running the watcher."""
    if len(sys.argv) < 2:
        print("=" * 70)
        print("Gmail Watcher - Monitor Gmail for new emails")
        print("=" * 70)
        print()
        print("Usage:")
        print("  python gmail_watcher.py <vault_path> [check_interval_seconds]")
        print()
        print("Examples:")
        print("  python gmail_watcher.py ./AI_Employee_Vault           # Check every 2 minutes")
        print("  python gmail_watcher.py ./AI_Employee_Vault 30        # Check every 30 seconds")
        print("  python gmail_watcher.py ./AI_Employee_Vault 60        # Check every minute")
        print()
        print("Setup Instructions:")
        print("1. First run OAuth setup: python scripts/setup_gmail_oauth.py ./AI_Employee_Vault")
        print("2. Then run the watcher: python gmail_watcher.py ./AI_Employee_Vault")
        print()
        sys.exit(1)
    
    vault_path = Path(sys.argv[1]).resolve()
    
    # Determine if second argument is credentials path or check interval
    credentials_path = None
    check_interval = 120  # default
    
    if len(sys.argv) > 2:
        arg2 = sys.argv[2]
        # Check if it's a number (interval) or path
        try:
            check_interval = int(arg2)
            print(f"Check interval: {check_interval} seconds")
        except ValueError:
            # It's a path
            credentials_path = Path(arg2).resolve()
            if len(sys.argv) > 3:
                try:
                    check_interval = int(sys.argv[3])
                except ValueError:
                    check_interval = 120
    
    if not vault_path.exists():
        print(f"Error: Vault path does not exist: {vault_path}")
        sys.exit(1)
    
    # Determine credentials path
    if credentials_path:
        creds_path = credentials_path
    else:
        creds_path = vault_path / '.gmail' / 'credentials.json'
    
    if not creds_path.exists():
        print(f"Error: Credentials file not found: {creds_path}")
        print()
        print("Run OAuth setup first:")
        print(f"  python scripts/setup_gmail_oauth.py {vault_path}")
        sys.exit(1)
    
    # Create and run watcher
    try:
        watcher = GmailWatcher(str(vault_path), str(creds_path), check_interval)
        watcher.run()
    except ImportError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error starting Gmail watcher: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()

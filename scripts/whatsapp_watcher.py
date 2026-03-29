#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WhatsApp Watcher - Monitors WhatsApp Web for new messages with priority keywords.

This watcher uses Playwright to automate WhatsApp Web, check for unread messages,
and create action files for messages containing priority keywords.

⚠️ IMPORTANT: Be aware of WhatsApp's Terms of Service. Use responsibly.
   - Do not use for spam or bulk messaging
   - Respect rate limits
   - Consider using WhatsApp Business API for production use

Prerequisites:
1. Install Playwright: pip install playwright
2. Install browsers: playwright install
3. Have WhatsApp Web session ready (QR code scan)

Usage:
    python whatsapp_watcher.py /path/to/vault [session_path] [check_interval]

Example:
    python whatsapp_watcher.py ./AI_Employee_Vault
    python whatsapp_watcher.py ./AI_Employee_Vault ~/.whatsapp/session 30
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))
from base_watcher import BaseWatcher

# Playwright dependencies
try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("Playwright not installed. Install with:")
    print("pip install playwright")
    print("playwright install")


class WhatsAppWatcher(BaseWatcher):
    """
    Watches WhatsApp Web for new messages containing priority keywords.
    
    When a priority message is detected:
    1. Extract message content and sender info
    2. Detect priority keywords
    3. Create action file in Needs_Action/whatsapp/
    4. Track processed messages
    """
    
    # Priority keywords to flag (case-insensitive)
    PRIORITY_KEYWORDS = [
        'urgent', 'asap', 'invoice', 'payment', 'help', 
        'deadline', 'meeting', 'review', 'approval', 'emergency',
        'important', 'quick', 'now', 'today', 'tomorrow'
    ]
    
    # WhatsApp Web URLs
    WHATSAPP_WEB_URL = 'https://web.whatsapp.com'
    
    def __init__(self, vault_path: str, session_path: str = None, 
                 check_interval: int = 30):
        """
        Initialize the WhatsApp watcher.
        
        Args:
            vault_path: Path to the Obsidian vault root
            session_path: Path to store browser session (default: vault/.whatsapp_session)
            check_interval: Seconds between checks (default: 30)
        """
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError("Playwright not installed")
        
        super().__init__(vault_path, check_interval)
        
        # Session path for persistent browser context
        if session_path:
            self.session_path = Path(session_path).expanduser()
        else:
            self.session_path = self.vault_path / '.whatsapp_session'
        
        # Create whatsapp subfolder in Needs_Action
        self.whatsapp_folder = self.needs_action / 'whatsapp'
        self.whatsapp_folder.mkdir(parents=True, exist_ok=True)
        
        # Track processed messages (chat_id + timestamp)
        self.processed_messages = self._load_processed_messages()
        
        self.logger.info(f'Session path: {self.session_path}')
        self.logger.info(f'Priority keywords: {len(self.PRIORITY_KEYWORDS)} configured')
    
    def _load_processed_messages(self) -> set:
        """Load IDs of previously processed messages."""
        cache_file = self.vault_path / '.whatsapp_processed.json'
        if cache_file.exists():
            try:
                content = cache_file.read_text()
                data = json.loads(content)
                return set(data.get('messages', []))
            except Exception as e:
                self.logger.warning(f'Could not load processed messages: {e}')
        return set()
    
    def _save_processed_messages(self):
        """Save processed message IDs to disk."""
        cache_file = self.vault_path / '.whatsapp_processed.json'
        try:
            # Keep only last 500 messages to prevent file growing indefinitely
            messages_list = list(self.processed_messages)[-500:]
            cache_file.write_text(json.dumps({'messages': messages_list}))
        except Exception as e:
            self.logger.error(f'Could not save processed messages: {e}')
    
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
    
    def _get_detected_keywords(self, text: str) -> List[str]:
        """Get list of detected priority keywords."""
        text_lower = text.lower()
        return [kw for kw in self.PRIORITY_KEYWORDS if kw in text_lower]
    
    def check_for_updates(self) -> List[dict]:
        """
        Check WhatsApp Web for new messages with priority keywords.
        
        Returns:
            list: List of new message dictionaries
        """
        new_messages = []
        
        try:
            with sync_playwright() as p:
                # Launch browser with persistent context (keeps session)
                browser = p.chromium.launch_persistent_context(
                    user_data_dir=str(self.session_path),
                    headless=True,
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--no-sandbox',
                        '--disable-dev-shm-usage'
                    ]
                )
                
                page = browser.pages[0] if browser.pages else browser.new_page()
                
                # Navigate to WhatsApp Web
                self.logger.debug('Navigating to WhatsApp Web...')
                page.goto(self.WHATSAPP_WEB_URL, timeout=60000)
                
                # Wait for chat list to load (or QR code if not logged in)
                try:
                    # Check if logged in (look for chat list)
                    page.wait_for_selector('[data-testid="chat-list"]', timeout=30000)
                except PlaywrightTimeout:
                    # Check for QR code (not logged in)
                    if page.query_selector('[data-testid="qr-code"]'):
                        self.logger.warning('WhatsApp Web not logged in. Please scan QR code.')
                        self.logger.warning(f'Session will be saved to: {self.session_path}')
                        browser.close()
                        return []
                
                # Give page time to load messages
                page.wait_for_timeout(3000)
                
                # Find unread messages
                self.logger.debug('Looking for unread messages...')
                
                # Select unread chat elements
                unread_chats = page.query_selector_all('[aria-label*="unread"]')
                
                for chat in unread_chats:
                    try:
                        # Get chat name/number
                        chat_name_elem = chat.query_selector('[dir="auto"]')
                        chat_name = chat_name_elem.inner_text() if chat_name_elem else 'Unknown'
                        
                        # Get message preview text
                        message_elem = chat.query_selector('[dir="auto"]:last-child')
                        message_text = message_elem.inner_text() if message_elem else ''
                        
                        # Check if message contains priority keywords
                        if any(kw in message_text.lower() for kw in self.PRIORITY_KEYWORDS):
                            # Create unique message ID
                            msg_id = f"{chat_name}_{datetime.now().strftime('%Y%m%d_%H')}"
                            
                            if msg_id not in self.processed_messages:
                                new_messages.append({
                                    'chat_name': chat_name,
                                    'message': message_text,
                                    'priority': self._detect_priority(message_text),
                                    'keywords': self._get_detected_keywords(message_text),
                                    'received': datetime.now().isoformat(),
                                    'msg_id': msg_id
                                })
                                self.logger.debug(f"Priority message from {chat_name}")
                        
                    except Exception as e:
                        self.logger.debug(f'Error processing chat: {e}')
                        continue
                
                browser.close()
                
        except Exception as e:
            self.logger.error(f'Error checking WhatsApp: {e}')
        
        return new_messages
    
    def create_action_file(self, message_data: dict) -> Path:
        """
        Create an action file for the WhatsApp message.
        
        Args:
            message_data: Dictionary with message content
            
        Returns:
            Path: Path to the created file
        """
        # Create safe filename
        safe_name = self.sanitize_filename(message_data['chat_name'][:30])
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        filename = f"WHATSAPP_{safe_name}_{timestamp}.md"
        filepath = self.whatsapp_folder / filename
        
        content = f'''---
type: whatsapp
from: {message_data['chat_name']}
received: {message_data['received']}
priority: {message_data['priority']}
status: pending
keywords: {', '.join(message_data['keywords'])}
msg_id: {message_data['msg_id']}
---

# WhatsApp Message Received

**From:** {message_data['chat_name']}

**Received:** {message_data['received']}

---

## Message Content

{message_data['message']}

---

## Analysis

**Priority Level:** {message_data['priority'].upper()}

**Keywords Detected:** {', '.join(message_data['keywords'])}

---

## Suggested Actions

- [ ] Read and understand the message
- [ ] Determine required response
- [ ] Draft reply if needed
- [ ] Request approval for external communication
- [ ] Send reply via WhatsApp (requires approval)
- [ ] Mark as read in WhatsApp
- [ ] Archive after processing

---

## Reply Draft (Optional)

<!-- Draft your reply here -->

---

## Notes

<!-- Add your notes here -->

'''
        filepath.write_text(content)
        
        # Mark as processed
        self.processed_messages.add(message_data['msg_id'])
        self._save_processed_messages()
        
        return filepath


def main():
    """Main entry point for running the watcher."""
    if len(sys.argv) < 2:
        print("Usage: python whatsapp_watcher.py <vault_path> [session_path] [check_interval]")
        print("\nExample:")
        print("  python whatsapp_watcher.py ./AI_Employee_Vault")
        print("  python whatsapp_watcher.py ./AI_Employee_Vault ~/.whatsapp/session 30")
        print("\nSetup Instructions:")
        print("1. Install Playwright: pip install playwright")
        print("2. Install browsers: playwright install")
        print("3. First run: Script will show QR code for WhatsApp Web login")
        print("4. Scan QR code with WhatsApp mobile app")
        print("5. Session will be saved for future runs")
        print("\n⚠️ IMPORTANT: Use responsibly and respect WhatsApp's Terms of Service")
        sys.exit(1)
    
    vault_path = Path(sys.argv[1]).resolve()
    session_path = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else None
    check_interval = int(sys.argv[3]) if len(sys.argv) > 3 else 30
    
    if not vault_path.exists():
        print(f"Error: Vault path does not exist: {vault_path}")
        sys.exit(1)
    
    # Create and run watcher
    try:
        watcher = WhatsAppWatcher(str(vault_path), str(session_path) if session_path else None, check_interval)
        watcher.run()
    except ImportError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error starting WhatsApp watcher: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()

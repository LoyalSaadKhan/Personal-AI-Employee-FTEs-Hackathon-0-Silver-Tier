#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LinkedIn Auto Poster - Post to LinkedIn automatically using browser.

This version uses improved detection and human-like interaction patterns.

Usage:
    python linkedin_auto_poster.py --post "Your post text here"
    python linkedin_auto_poster.py --file "path/to/post.txt"
    python linkedin_auto_poster.py --test    # Test connection

Example:
    python linkedin_auto_poster.py --post "Hello LinkedIn! #AI #Automation"
"""

import sys
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Optional

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("Playwright required. Install:")
    print("pip install playwright")
    print("playwright install chromium")
    sys.exit(1)


class LinkedInAutoPoster:
    """Post to LinkedIn with improved automation."""
    
    def __init__(self, vault_path: str = None):
        self.vault_path = Path(vault_path).resolve() if vault_path else Path.cwd()
        self.session_path = self.vault_path / '.linkedin' / 'session'
        self.posts_log = self.vault_path / 'Social' / 'linkedin_posts.json'
        
        # Ensure directories exist
        self.session_path.mkdir(parents=True, exist_ok=True)
        self.posts_log.parent.mkdir(parents=True, exist_ok=True)
        
        self.linkedin_url = "https://www.linkedin.com/feed/"
    
    def post(self, text: str, timeout_seconds: int = 120) -> bool:
        """
        Post to LinkedIn automatically.
        
        Args:
            text: Post content
            timeout_seconds: How long to wait for manual completion if needed
        
        Returns:
            bool: True if post was successful
        """
        print("=" * 60)
        print("LinkedIn Auto Poster")
        print("=" * 60)
        print()
        print(f"Post length: {len(text)} characters")
        print()
        
        success = False
        
        try:
            with sync_playwright() as p:
                # Launch browser
                print("Launching browser...")
                browser = p.chromium.launch_persistent_context(
                    user_data_dir=str(self.session_path),
                    headless=False,
                    viewport={'width': 1366, 'height': 768},
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--disable-features=IsolateOrigins,site-per-process',
                        '--no-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-web-security',
                        '--disable-features=VizDisplayCompositor'
                    ]
                )
                
                # Hide automation flags
                page = browser.pages[0] if browser.pages else browser.new_page()
                page.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                """)
                
                # Navigate to LinkedIn
                print("Opening LinkedIn...")
                page.goto(self.linkedin_url, timeout=60000, wait_until='domcontentloaded')
                page.wait_for_timeout(8000)  # Wait for page to load
                
                # Check if logged in
                print("Checking login status...")
                is_logged_in = self._check_logged_in(page)
                
                if not is_logged_in:
                    print("⚠️  Not logged in. Please login manually...")
                    print(f"You have {timeout_seconds} seconds")
                    
                    for i in range(timeout_seconds):
                        page.wait_for_timeout(1000)
                        if self._check_logged_in(page):
                            print("✓ Login detected!")
                            break
                        if i % 10 == 9:
                            print(f"   Waiting... ({i+1}s)")
                    else:
                        print("❌ Login timeout")
                        browser.close()
                        return False
                
                print("✓ Logged in")
                
                # Wait for page to fully load
                page.wait_for_timeout(5000)
                
                # Method 1: Click "Start a post" button
                print("Opening post editor...")
                post_opened = self._open_post_editor(page)
                
                if not post_opened:
                    print("❌ Could not open post editor")
                    browser.close()
                    return False
                
                print("✓ Post editor opened")
                page.wait_for_timeout(2000)
                
                # Enter text
                print("Entering post text...")
                text_entered = self._enter_text(page, text)
                
                if not text_entered:
                    print("❌ Could not enter text")
                    browser.close()
                    return False
                
                print("✓ Text entered")
                page.wait_for_timeout(2000)
                
                # Click Post button
                print("Submitting post...")
                submitted = self._submit_post(page)
                
                if submitted:
                    print("✓ Post submitted successfully!")
                    success = True
                else:
                    print("⚠️  Auto-submit failed, waiting for manual post...")
                    print(f"Text is entered. Please click 'Post' manually.")
                    print(f"Waiting {timeout_seconds} seconds...")
                    
                    for i in range(timeout_seconds):
                        page.wait_for_timeout(1000)
                        # Check if post was submitted (we're back on feed)
                        if self._check_logged_in(page) and page.query_selector('[data-testid="feed"]'):
                            print("✓ Post detected!")
                            success = True
                            break
                        if i % 15 == 14:
                            print(f"   Waiting... ({i+1}s)")
                
                # Log the post
                self._log_post(text, success)
                
                print()
                print("=" * 60)
                print("Done!")
                print("=" * 60)
                
                # Keep browser open briefly
                page.wait_for_timeout(3000)
                browser.close()
                
                return success
                
        except Exception as e:
            print(f"❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _check_logged_in(self, page) -> bool:
        """Check if user is logged in to LinkedIn."""
        try:
            # Look for various indicators of being logged in
            indicators = [
                '[data-testid="feed"]',
                'span:has-text("Me")',
                'button[aria-label="You"]',
                '.nav-item__link--profile'
            ]
            
            for selector in indicators:
                try:
                    if page.query_selector(selector):
                        return True
                except:
                    continue
            
            # Check URL
            if 'feed' in page.url or 'linkedin.com' in page.url and 'login' not in page.url:
                return True
            
            return False
        except:
            return False
    
    def _open_post_editor(self, page) -> bool:
        """Open the post creation dialog."""
        # Try multiple methods to open post editor
        
        # Method 1: Click "Start a post" button
        try:
            post_button = page.locator('button:has-text("Start a post")').first
            if post_button.count() > 0 and post_button.is_visible():
                post_button.click()
                page.wait_for_timeout(3000)
                return True
        except Exception as e:
            print(f"   Method 1 failed: {e}")
        
        # Method 2: Click by aria-label
        try:
            post_button = page.locator('button[aria-label="Start a post"]').first
            if post_button.count() > 0 and post_button.is_visible():
                post_button.click()
                page.wait_for_timeout(3000)
                return True
        except Exception as e:
            print(f"   Method 2 failed: {e}")
        
        # Method 3: Navigate to post URL
        try:
            print("   Trying direct navigation...")
            page.goto('https://www.linkedin.com/feed/?showUpdateForm=true', 
                     timeout=30000, wait_until='domcontentloaded')
            page.wait_for_timeout(8000)
            return True
        except Exception as e:
            print(f"   Method 3 failed: {e}")
        
        # Method 4: Try keyboard shortcut
        try:
            print("   Trying keyboard shortcut...")
            page.keyboard.press('Control+Shift+P')
            page.wait_for_timeout(3000)
            return True
        except:
            pass
        
        return False
    
    def _enter_text(self, page, text: str) -> bool:
        """Enter post text into editor."""
        # Multiple editor selectors
        editor_selectors = [
            'div[contenteditable="true"]',
            '[aria-label="What do you want to talk about?"]',
            '[placeholder*="What do you want"]',
            '.ql-editor[contenteditable="true"]',
            '.post-editor__content-editor',
            '[role="textbox"]'
        ]
        
        for selector in editor_selectors:
            try:
                print(f"   Trying selector: {selector}")
                editor = page.wait_for_selector(selector, timeout=5000)
                if editor:
                    print(f"   ✓ Found editor")
                    
                    # Scroll into view
                    editor.scroll_into_view_if_needed()
                    page.wait_for_timeout(500)
                    
                    # Click to focus
                    editor.click()
                    page.wait_for_timeout(1000)
                    
                    # Try different text entry methods
                    try:
                        # Method 1: Fill
                        editor.fill(text)
                        page.wait_for_timeout(1000)
                        
                        # Verify text was entered
                        content = editor.inner_text()
                        if len(content) > 0:
                            print(f"   ✓ Text entered ({len(content)} chars)")
                            return True
                        else:
                            print("   ⚠️  Fill didn't work, trying keyboard...")
                    except Exception as e:
                        print(f"   ⚠️  Fill failed: {e}")
                    
                    # Method 2: Keyboard typing
                    try:
                        # Clear first
                        page.keyboard.press('Control+A')
                        page.wait_for_timeout(200)
                        page.keyboard.press('Delete')
                        page.wait_for_timeout(200)
                        
                        # Type slowly
                        for char in text:
                            page.keyboard.type(char, delay=50)
                        
                        page.wait_for_timeout(1000)
                        print(f"   ✓ Text typed via keyboard")
                        return True
                    except Exception as e:
                        print(f"   ⚠️  Keyboard failed: {e}")
                    
            except Exception as e:
                print(f"   ⚠️  Selector failed: {e}")
                continue
        
        # Last resort: Take screenshot for debugging
        try:
            page.screenshot(path='linkedin_editor_debug.png')
            print("   Screenshot saved: linkedin_editor_debug.png")
        except:
            pass
        
        return False
    
    def _submit_post(self, page) -> bool:
        """Click the Post button to submit."""
        try:
            # Wait for Post button
            post_button = page.wait_for_selector('button:has-text("Post")', timeout=10000)
            
            if post_button:
                # Wait for button to be enabled
                page.wait_for_timeout(2000)
                
                # Check if enabled
                is_enabled = post_button.is_enabled()
                
                if is_enabled:
                    post_button.click()
                    page.wait_for_timeout(5000)
                    return True
                else:
                    print("   Post button not enabled")
                    return False
        except Exception as e:
            print(f"   Submit failed: {e}")
        
        return False
    
    def _log_post(self, text: str, success: bool):
        """Log post to file."""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'content': text[:200],
            'success': success,
            'method': 'browser_auto'
        }
        
        # Load existing logs
        logs = []
        if self.posts_log.exists():
            try:
                logs = json.loads(self.posts_log.read_text())
            except:
                logs = []
        
        logs.append(log_entry)
        
        # Save logs
        self.posts_log.write_text(json.dumps(logs, indent=2))


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='LinkedIn Auto Poster')
    parser.add_argument('--post', type=str, help='Post this text to LinkedIn')
    parser.add_argument('--file', type=str, help='Read post from file')
    parser.add_argument('--test', action='store_true', help='Test LinkedIn connection')
    parser.add_argument('--vault', type=str, default='./AI_Employee_Vault',
                       help='Path to vault (default: ./AI_Employee_Vault)')
    
    args = parser.parse_args()
    
    vault_path = Path(args.vault)
    if not vault_path.exists():
        vault_path = Path.cwd()
    
    poster = LinkedInAutoPoster(str(vault_path))
    
    if args.test:
        print("Testing LinkedIn connection...")
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch_persistent_context(
                    user_data_dir=str(poster.session_path),
                    headless=False,
                    viewport={'width': 1366, 'height': 768}
                )
                page = browser.pages[0] if browser.pages else browser.new_page()
                page.goto(poster.linkedin_url, timeout=60000)
                page.wait_for_timeout(5000)
                
                if poster._check_logged_in(page):
                    print("✓ Logged in to LinkedIn")
                else:
                    print("⚠️  Not logged in")
                
                browser.close()
        except Exception as e:
            print(f"❌ Error: {e}")
    
    elif args.post:
        success = poster.post(args.post)
        sys.exit(0 if success else 1)
    
    elif args.file:
        file_path = Path(args.file)
        if not file_path.exists():
            print(f"❌ File not found: {file_path}")
            sys.exit(1)
        
        text = file_path.read_text(encoding='utf-8')
        success = poster.post(text)
        sys.exit(0 if success else 1)
    
    else:
        parser.print_help()
        print()
        print("Examples:")
        print('  python linkedin_auto_poster.py --post "Hello LinkedIn! #AI"')
        print('  python linkedin_auto_poster.py --file post.txt')
        print('  python linkedin_auto_poster.py --test')


if __name__ == '__main__':
    main()

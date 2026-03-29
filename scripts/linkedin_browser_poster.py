#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LinkedIn Browser Poster - Post to LinkedIn using browser automation.

No API credentials or company page required!
Uses Playwright to automate LinkedIn web interface.

Usage:
    python linkedin_browser_poster.py --post "Your post text here"
    python linkedin_browser_poster.py --draft    # Generate AI draft
    python linkedin_browser_poster.py --list     # List recent posts

Example:
    python linkedin_browser_poster.py --post "Hello LinkedIn! #AI #Automation"
"""

import sys
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Optional

# Playwright imports
try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("Playwright not installed. Install with:")
    print("pip install playwright")
    print("playwright install")
    sys.exit(1)


class LinkedInBrowserPoster:
    """Post to LinkedIn using browser automation."""
    
    def __init__(self, vault_path: str = None):
        self.vault_path = Path(vault_path).resolve() if vault_path else Path.cwd()
        self.session_path = self.vault_path / '.linkedin' / 'browser_session'
        self.posts_folder = self.vault_path / 'Social' / 'published'
        
        # Ensure folders exist
        self.session_path.mkdir(parents=True, exist_ok=True)
        self.posts_folder.mkdir(parents=True, exist_ok=True)
        
        self.linkedin_url = "https://www.linkedin.com/feed/"
    
    def login(self, page, email: str = None, password: str = None):
        """Login to LinkedIn if not already logged in."""
        page.goto(self.linkedin_url, timeout=60000)
        page.wait_for_timeout(8000)
        
        # Check if already logged in (look for feed or Me menu)
        if page.query_selector('[data-testid="feed"]') or page.query_selector('span:has-text("Me")'):
            print("✓ Already logged in")
            return True
        
        # Check for login page
        if page.query_selector('input[id="username"]'):
            print("Login page detected")
            
            if email and password:
                # Auto-fill credentials
                page.fill('input[id="username"]', email)
                page.fill('input[id="password"]', password)
                page.click('button[type="submit"]')
                print("⚠️  Waiting for login... (complete any 2FA if required)")
                
                # Wait for login to complete
                for i in range(60):
                    page.wait_for_timeout(1000)
                    if page.query_selector('[data-testid="feed"]') or page.query_selector('span:has-text("Me")'):
                        print("✓ Login successful")
                        return True
                    if i == 30:
                        print("   Still waiting for login...")
                
                print("⚠️  Login may require manual verification")
            else:
                print("⚠️  Please log in manually in the browser...")
            
            # Wait for user to complete login (up to 3 minutes)
            print("Waiting up to 3 minutes for login...")
            for i in range(180):
                page.wait_for_timeout(1000)
                if page.query_selector('[data-testid="feed"]') or page.query_selector('span:has-text("Me")'):
                    print("✓ Login detected")
                    return True
                if i % 30 == 29:
                    print(f"   Still waiting... ({i+1}s)")
            
            print("❌ Login timeout")
            return False
        
        # Check if we're on feed already
        if page.query_selector('[data-testid="feed"]'):
            print("✓ Already on feed")
            return True
        
        print("⚠️  Waiting for page to load...")
        page.wait_for_timeout(10000)
        return True
    
    def create_post(self, text: str, wait_for_manual: bool = False) -> bool:
        """Create a post on LinkedIn using browser automation."""
        print("=" * 60)
        print("LinkedIn Browser Poster")
        print("=" * 60)
        print()
        
        try:
            with sync_playwright() as p:
                # Launch browser with persistent context (keeps session)
                browser = p.chromium.launch_persistent_context(
                    user_data_dir=str(self.session_path),
                    headless=False,  # Show browser for debugging
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--no-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-features=IsolateOrigins,site-per-process'
                    ]
                )
                
                page = browser.pages[0] if browser.pages else browser.new_page()
                
                # Set viewport to standard size
                page.set_viewport_size({'width': 1280, 'height': 800})
                
                # Navigate to LinkedIn
                print("Navigating to LinkedIn...")
                self.login(page)
                
                # Wait for feed to load
                print("Waiting for feed to load (up to 30 seconds)...")
                page.wait_for_timeout(5000)
                
                # Try to detect if we're on the feed page
                try:
                    page.wait_for_selector('[data-testid="feed"]', timeout=30000)
                    print("✓ Feed loaded")
                except PlaywrightTimeout:
                    print("⚠️  Feed selector not found, continuing anyway...")
                
                page.wait_for_timeout(3000)
                
                # Method 1: Click the "Start a post" button
                print("Looking for 'Start a post' button...")
                page.wait_for_timeout(2000)
                
                # Scroll to top to ensure button is visible
                page.evaluate('window.scrollTo(0, 0)')
                page.wait_for_timeout(1000)
                
                post_clicked = False
                
                # Try clicking with different approaches
                try:
                    # Approach 1: Click by text
                    post_button = page.locator('button:has-text("Start a post")').first
                    if post_button.count() > 0:
                        print("✓ Found 'Start a post' button")
                        post_button.click()
                        post_clicked = True
                        page.wait_for_timeout(3000)
                except Exception as e:
                    print(f"⚠️  Approach 1 failed: {e}")
                
                if not post_clicked:
                    try:
                        # Approach 2: Click by aria-label
                        post_button = page.locator('button[aria-label="Start a post"]').first
                        if post_button.count() > 0:
                            print("✓ Found post button by aria-label")
                            post_button.click()
                            post_clicked = True
                            page.wait_for_timeout(3000)
                    except Exception as e:
                        print(f"⚠️  Approach 2 failed: {e}")
                
                if not post_clicked:
                    try:
                        # Approach 3: Navigate directly to post creation
                        print("Navigating directly to post editor...")
                        page.goto('https://www.linkedin.com/feed/?showUpdateForm=true', timeout=30000)
                        page.wait_for_timeout(8000)  # Wait longer for page to load
                        post_clicked = True
                    except Exception as e:
                        print(f"⚠️  Approach 3 failed: {e}")
                
                if not post_clicked:
                    print("❌ Could not open post editor")
                    browser.close()
                    return False
                
                # Find the text editor
                print("Finding text editor...")
                page.wait_for_timeout(3000)
                
                # Take screenshot for debugging
                try:
                    page.screenshot(path=str(self.vault_path / 'linkedin_debug.png'))
                    print("Screenshot saved for debugging")
                except:
                    pass
                
                editor_found = False
                
                # Try multiple editor selectors with better waiting
                editor_selectors = [
                    'div[contenteditable="true"]',
                    '[aria-label="What do you want to talk about?"]',
                    '[placeholder*="What do you want"]',
                    '.ql-editor[contenteditable="true"]',
                ]
                
                for selector in editor_selectors:
                    try:
                        # Wait for element to appear
                        editor = page.wait_for_selector(selector, timeout=5000)
                        if editor:
                            print(f"✓ Found editor: {selector}")
                            
                            # Click to focus first
                            editor.click()
                            page.wait_for_timeout(500)
                            
                            # Clear and fill using keyboard
                            from playwright.sync_api import Keyboard
                            
                            # Select all and delete
                            page.keyboard.press('Control+A')
                            page.wait_for_timeout(200)
                            page.keyboard.press('Delete')
                            page.wait_for_timeout(200)
                            
                            # Type the text
                            editor.fill(text)
                            page.wait_for_timeout(2000)
                            
                            print(f"✓ Post text entered ({len(text)} chars)")
                            editor_found = True
                            break
                    except Exception as e:
                        print(f"⚠️  Editor not found with {selector}: {e}")
                        continue
                
                if not editor_found:
                    print("❌ Could not find text editor")
                    print("⚠️  LinkedIn may have changed their UI")
                    print("Try manual posting at: https://www.linkedin.com/feed/")
                    browser.close()
                    return False
                
                # Wait for Post button to become enabled
                print("Waiting for Post button...")
                page.wait_for_timeout(3000)
                
                # Find and click Post button
                post_submitted = False
                
                try:
                    # Look for Post button
                    post_submit = page.locator('button:has-text("Post")').first
                    
                    if post_submit.count() > 0:
                        # Check if button is enabled
                        is_enabled = post_submit.is_enabled()
                        print(f"Post button found, enabled: {is_enabled}")
                        
                        if is_enabled:
                            print("Clicking Post button...")
                            post_submit.click()
                            page.wait_for_timeout(5000)
                            post_submitted = True
                            print("✓ Post submitted!")
                        else:
                            print("⚠️  Post button not enabled")
                    else:
                        print("⚠️  Post button not found")
                        
                except Exception as e:
                    print(f"⚠️  Error clicking Post: {e}")
                
                if not post_submitted:
                    if wait_for_manual:
                        print()
                        print("=" * 60)
                        print("Manual Posting Required")
                        print("=" * 60)
                        print()
                        print("Text has been entered. Please click 'Post' manually.")
                        print("Waiting 90 seconds...")
                        print()
                        
                        # Wait for manual post
                        for i in range(90):
                            page.wait_for_timeout(1000)
                            # Check if we're back on feed
                            try:
                                if page.query_selector('[data-testid="feed"]'):
                                    print("✓ Post detected!")
                                    post_submitted = True
                                    break
                            except:
                                pass
                            
                            if i % 15 == 14:
                                print(f"   Waiting... ({i+1}s)")
                    else:
                        print("⚠️  Auto-post failed, browser will stay open")
                        page.wait_for_timeout(30000)
                
                # Log the post
                self._log_post(text, 'success' if post_submitted else 'manual_required')
                
                print()
                print("=" * 60)
                print("✅ Done!")
                print("=" * 60)
                print()
                print(f"Post logged to: {self.posts_folder}")
                print("Session saved for next time")
                
                # Keep browser open briefly
                page.wait_for_timeout(3000)
                browser.close()
                
                return True
                
        except Exception as e:
            print(f"❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
            self._log_post(text, f'failed: {e}')
            return False
    
    def _log_post(self, content: str, status: str):
        """Log post to published folder."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = self.posts_folder / f'linkedin_post_{timestamp}.json'
        
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'content': content[:500],
            'status': status,
            'method': 'browser_automation'
        }
        
        log_file.write_text(json.dumps(log_entry, indent=2))


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='LinkedIn Browser Poster')
    parser.add_argument('--post', type=str, help='Post this text to LinkedIn')
    parser.add_argument('--draft', action='store_true', help='Generate AI draft post')
    parser.add_argument('--list', action='store_true', help='List recent posts')
    parser.add_argument('--vault', type=str, default='./AI_Employee_Vault', 
                       help='Path to Obsidian vault (default: ./AI_Employee_Vault)')
    
    args = parser.parse_args()
    
    # Check if vault exists
    vault_path = Path(args.vault)
    if not vault_path.exists():
        print(f"Warning: Vault not found at {vault_path}, using current directory")
        vault_path = Path.cwd()
    
    poster = LinkedInBrowserPoster(str(vault_path))
    
    if args.post:
        success = poster.create_post(args.post, wait_for_manual=True)
        sys.exit(0 if success else 1)
    
    elif args.draft:
        # Import from linkedin_poster if available
        try:
            from linkedin_poster import LinkedInPoster
            lp = LinkedInPoster(str(vault_path))
            filepath = lp.generate_post()
            print(f"\n✅ Draft created: {filepath.name}")
            print(f"   Location: {filepath}")
            print(f"\nTo post this draft:")
            print(f"1. Open the file and copy the content")
            print(f"2. Run: python linkedin_browser_poster.py --post \"Your post text\"")
        except ImportError:
            print("linkedin_poster.py not found. Create draft manually.")
    
    elif args.list:
        posts = list(poster.posts_folder.glob('*.json'))
        print(f"\nRecent LinkedIn Posts ({len(posts)} total):\n")
        print("-" * 60)
        for post in sorted(posts, reverse=True)[:5]:
            data = json.loads(post.read_text())
            print(f"📝 {post.name}")
            print(f"   Status: {data.get('status', 'unknown')}")
            print(f"   Time: {data.get('timestamp', 'unknown')}")
            print(f"   Content: {data.get('content', '')[:100]}...")
            print()
    
    else:
        parser.print_help()
        print()
        print("Examples:")
        print("  python linkedin_browser_poster.py --post \"Hello LinkedIn! #AI\"")
        print("  python linkedin_browser_poster.py --draft")
        print("  python linkedin_browser_poster.py --list")
        print()
        print("Note: Browser will open. Login if needed, then post will be created.")


if __name__ == '__main__':
    main()

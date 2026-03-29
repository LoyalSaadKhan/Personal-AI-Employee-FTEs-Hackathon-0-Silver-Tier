#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LinkedIn Simple Poster - Semi-automated posting with manual trigger.

Workflow:
1. Opens LinkedIn in browser (you're already logged in)
2. You click "Start a post" manually
3. Script detects editor and auto-fills text
4. You click "Post" manually

This bypasses LinkedIn's automation detection.

Usage:
    python linkedin_simple_poster.py --post "Your text here"
"""

import sys
import json
from pathlib import Path
from datetime import datetime

try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("Install playwright:")
    print("pip install playwright")
    print("playwright install chromium")
    sys.exit(1)


def post_to_linkedin(text: str, vault_path: str = None):
    """Post to LinkedIn with manual trigger."""
    
    vault = Path(vault_path).resolve() if vault_path else Path.cwd()
    session_path = vault / '.linkedin' / 'session'
    session_path.mkdir(parents=True, exist_ok=True)
    
    print("=" * 70)
    print("LinkedIn Simple Poster")
    print("=" * 70)
    print()
    print("INSTRUCTIONS:")
    print("1. Browser will open LinkedIn")
    print("2. CLICK 'Start a post' button when you see it")
    print("3. Script will auto-fill your text")
    print("4. CLICK 'Post' when ready")
    print()
    print(f"Post content ({len(text)} chars):")
    print("-" * 70)
    print(text[:200] + "..." if len(text) > 200 else text)
    print("-" * 70)
    print()
    
    input("Press Enter to open browser...")
    
    try:
        with sync_playwright() as p:
            # Launch browser
            print("Launching browser...")
            browser = p.chromium.launch_persistent_context(
                user_data_dir=str(session_path),
                headless=False,
                viewport={'width': 1366, 'height': 768},
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--no-sandbox',
                ]
            )
            
            page = browser.pages[0] if browser.pages else browser.new_page()
            
            # Hide automation
            page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)
            
            # Navigate to LinkedIn
            print("Opening LinkedIn...")
            page.goto('https://www.linkedin.com/feed/', timeout=60000)
            page.wait_for_timeout(5000)
            
            print()
            print("=" * 70)
            print("ACTION REQUIRED")
            print("=" * 70)
            print()
            print("👉 CLICK 'Start a post' button on LinkedIn")
            print()
            print("Waiting for you to click... (120 seconds)")
            print()
            
            # Wait for user to click "Start a post"
            editor_found = False
            for i in range(120):
                page.wait_for_timeout(1000)
                
                # Try to find editor
                try:
                    editor = page.query_selector('div[contenteditable="true"]')
                    if editor:
                        print(f"✓ Post editor detected! ({i+1}s)")
                        editor_found = True
                        break
                except:
                    pass
                
                if i % 10 == 9:
                    print(f"   Still waiting... ({i+1}s)")
            
            if not editor_found:
                print("❌ Editor not found. Please try again.")
                print("Make sure you clicked 'Start a post'")
                browser.close()
                return False
            
            # Wait for editor to be ready
            page.wait_for_timeout(2000)
            
            # Enter text
            print("Entering text...")
            try:
                editor = page.query_selector('div[contenteditable="true"]')
                editor.click()
                page.wait_for_timeout(500)
                
                # Clear and type
                page.keyboard.press('Control+A')
                page.wait_for_timeout(200)
                page.keyboard.press('Delete')
                page.wait_for_timeout(200)
                
                # Type text
                page.keyboard.type(text, delay=30)
                page.wait_for_timeout(2000)
                
                print(f"✓ Text entered ({len(text)} chars)")
                
            except Exception as e:
                print(f"❌ Could not enter text: {e}")
                browser.close()
                return False
            
            print()
            print("=" * 70)
            print("TEXT ENTERED!")
            print("=" * 70)
            print()
            print("👉 REVIEW your post")
            print("👉 CLICK 'Post' button when ready")
            print()
            print("Waiting for you to post... (90 seconds)")
            print()
            
            # Wait for post to be submitted
            for i in range(90):
                page.wait_for_timeout(1000)
                
                # Check if we're back on feed (post submitted)
                try:
                    if page.query_selector('[data-testid="feed"]'):
                        # Give it a moment to ensure post went through
                        page.wait_for_timeout(2000)
                        if page.query_selector('[data-testid="feed"]'):
                            print("✓ Post detected!")
                            break
                except:
                    pass
                
                if i % 15 == 14:
                    print(f"   Waiting... ({i+1}s)")
            
            # Log the post
            log_post(vault, text, True)
            
            print()
            print("=" * 70)
            print("✅ DONE!")
            print("=" * 70)
            print()
            print("Post logged to: AI_Employee_Vault/Social/linkedin_posts.json")
            print()
            
            # Keep browser open briefly
            page.wait_for_timeout(3000)
            browser.close()
            
            return True
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


def log_post(vault_path: Path, text: str, success: bool):
    """Log post to file."""
    log_file = vault_path / 'Social' / 'linkedin_posts.json'
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'content': text[:200],
        'success': success,
        'method': 'simple_poster'
    }
    
    logs = []
    if log_file.exists():
        try:
            logs = json.loads(log_file.read_text())
        except:
            logs = []
    
    logs.append(log_entry)
    log_file.write_text(json.dumps(logs, indent=2))


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='LinkedIn Simple Poster')
    parser.add_argument('--post', type=str, required=True, help='Post text')
    parser.add_argument('--vault', type=str, default='./AI_Employee_Vault',
                       help='Vault path')
    
    args = parser.parse_args()
    
    success = post_to_linkedin(args.post, args.vault)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()

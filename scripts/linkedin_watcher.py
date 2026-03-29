#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LinkedIn Watcher - Monitors LinkedIn for notifications, messages, and engagement.

This watcher can:
1. Authenticate with LinkedIn OAuth
2. Monitor LinkedIn for new notifications
3. Track post engagement (likes, comments, shares)
4. Create action files for important notifications

Usage:
    python linkedin_watcher.py /path/to/vault --authenticate   # Run OAuth setup
    python linkedin_watcher.py /path/to/vault --check          # Check for updates
    python linkedin_watcher.py /path/to/vault --post          # Create and post

Example:
    python linkedin_watcher.py ./AI_Employee_Vault --authenticate
    python linkedin_watcher.py ./AI_Employee_Vault --check
"""

import sys
import json
import webbrowser
import hashlib
import base64
import os
import time
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from urllib.parse import urlencode, parse_qs
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent))

# LinkedIn OAuth URLs
LINKEDIN_AUTH_URL = "https://www.linkedin.com/oauth/v2/authorization"
LINKEDIN_TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
LINKEDIN_API_BASE = "https://api.linkedin.com/v2"

# LinkedIn API scopes
SCOPES = [
    'w_member_social',      # Post to LinkedIn
    'r_basicprofile',       # Read basic profile
    'r_emailaddress'        # Read email address
]


class LinkedInWatcher:
    """Monitor LinkedIn for updates and engagement."""
    
    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path).resolve()
        self.linkedin_folder = self.vault_path / '.linkedin'
        self.creds_file = self.linkedin_folder / 'credentials.json'
        self.token_file = self.linkedin_folder / 'token.json'
        self.notifications_folder = self.vault_path / 'Social' / 'linkedin_notifications'
        
        # Ensure folders exist
        self.linkedin_folder.mkdir(parents=True, exist_ok=True)
        self.notifications_folder.mkdir(parents=True, exist_ok=True)
        
        # Set up logging
        self.logger = logging.getLogger('LinkedInWatcher')
        self.logger.setLevel(logging.INFO)
        
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        
        # Load credentials and token
        self.credentials = None
        self.token = None
        self._load_credentials()
        self._load_token()
    
    def _load_credentials(self):
        """Load LinkedIn credentials."""
        if self.creds_file.exists():
            try:
                self.credentials = json.loads(self.creds_file.read_text())
                self.logger.info("Credentials loaded")
            except Exception as e:
                self.logger.warning(f"Could not load credentials: {e}")
    
    def _load_token(self):
        """Load LinkedIn access token."""
        if self.token_file.exists():
            try:
                self.token = json.loads(self.token_file.read_text())
                expires_at = self.token.get('expires_at', '')
                if expires_at and datetime.fromisoformat(expires_at) > datetime.now():
                    self.logger.info(f"Token loaded (expires: {expires_at})")
                else:
                    self.logger.warning("Token expired")
                    self.token = None
            except Exception as e:
                self.logger.warning(f"Could not load token: {e}")
    
    def is_authenticated(self) -> bool:
        """Check if authenticated with LinkedIn."""
        return self.token is not None
    
    def generate_pkce_pair(self):
        """Generate PKCE code verifier and challenge."""
        code_verifier = base64.urlsafe_b64encode(os.urandom(32)).rstrip(b'=').decode()
        code_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode()).digest()
        ).rstrip(b'=').decode()
        return code_verifier, code_challenge
    
    def authenticate(self) -> bool:
        """Run OAuth authentication flow."""
        print("=" * 60)
        print("LinkedIn Authentication")
        print("=" * 60)
        print()
        
        if not self.credentials:
            print("❌ ERROR: Credentials not found")
            print()
            print(f"Create credentials file: {self.creds_file}")
            print("{")
            print('  "client_id": "your_client_id",')
            print('  "client_secret": "your_client_secret",')
            print('  "redirect_uri": "http://localhost:8080"')
            print("}")
            return False
        
        class OAuthHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path.startswith('/callback'):
                    query_params = parse_qs(self.path.split('?')[1])
                    auth_code = query_params.get('code', [None])[0]
                    error = query_params.get('error', [None])[0]
                    
                    if error:
                        self.send_response(400)
                        self.send_header('Content-type', 'text/html')
                        self.end_headers()
                        self.wfile.write(f"Error: {error}".encode())
                        return
                    
                    self.server.auth_code = auth_code
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    html = """
                    <html>
                        <head><title>Authentication Successful</title></head>
                        <body>
                            <h1>✅ LinkedIn Authentication Successful!</h1>
                            <p>You can close this window and return to the terminal.</p>
                        </body>
                    </html>
                    """
                    self.wfile.write(html.encode())
                else:
                    self.send_response(404)
                    self.end_headers()
            
            def log_message(self, format, *args):
                pass
        
        # Generate PKCE
        code_verifier, code_challenge = self.generate_pkce_pair()
        
        # Build authorization URL
        auth_params = {
            'response_type': 'code',
            'client_id': self.credentials['client_id'],
            'redirect_uri': self.credentials.get('redirect_uri', 'http://localhost:8080'),
            'scope': ' '.join(SCOPES),
            'state': base64.urlsafe_b64encode(os.urandom(16)).decode().rstrip('='),
            'code_challenge': code_challenge,
            'code_challenge_method': 'S256'
        }
        
        auth_url = f"{LINKEDIN_AUTH_URL}?{urlencode(auth_params)}"
        
        print("Opening browser for LinkedIn authentication...")
        print()
        print("Please:")
        print("1. Sign in with LinkedIn")
        print("2. Grant permissions")
        print("3. Wait for 'Authentication Successful' page")
        print()
        
        webbrowser.open(auth_url)
        
        # Start server
        server = HTTPServer(('localhost', 8080), OAuthHandler)
        server.auth_code = None
        server.timeout = 120
        
        def handle_callback():
            server.handle_request()
        
        thread = threading.Thread(target=handle_callback, daemon=True)
        thread.start()
        thread.join(timeout=120)
        
        server.server_close()
        
        auth_code = server.auth_code
        
        if not auth_code:
            print("\n❌ ERROR: Authentication timeout")
            return False
        
        print("\n✓ Authorization code received")
        print("Exchanging for access token...")
        
        # Exchange for token
        try:
            import requests
            
            token_data = {
                'grant_type': 'authorization_code',
                'code': auth_code,
                'redirect_uri': self.credentials.get('redirect_uri', 'http://localhost:8080'),
                'client_id': self.credentials['client_id'],
                'client_secret': self.credentials['client_secret'],
                'code_verifier': code_verifier
            }
            
            response = requests.post(LINKEDIN_TOKEN_URL, data=token_data, timeout=30)
            response.raise_for_status()
            
            token_response = response.json()
            
            if 'access_token' not in token_response:
                print(f"❌ ERROR: No access token: {token_response}")
                return False
            
            # Save token
            access_token = token_response['access_token']
            expires_in = token_response.get('expires_in', 604800)
            refresh_token = token_response.get('refresh_token', '')
            
            token_obj = {
                'access_token': access_token,
                'expires_in': expires_in,
                'expires_at': (datetime.now() + timedelta(seconds=expires_in)).isoformat(),
                'refresh_token': refresh_token,
                'scope': ' '.join(SCOPES),
                'created_at': datetime.now().isoformat()
            }
            
            self.token_file.write_text(json.dumps(token_obj, indent=2))
            try:
                os.chmod(self.token_file, 0o600)
            except:
                pass
            
            self.token = token_obj
            self.logger.info("Token saved")
            
            print()
            print("=" * 60)
            print("✅ LinkedIn Authentication Complete!")
            print("=" * 60)
            print()
            print(f"Token saved to: {self.token_file}")
            print(f"Expires: {token_obj['expires_at']}")
            print()
            return True
            
        except Exception as e:
            print(f"❌ ERROR: {e}")
            return False
    
    def get_profile(self) -> Optional[Dict]:
        """Get current user's LinkedIn profile."""
        if not self.token:
            self.logger.error("Not authenticated")
            return None
        
        try:
            import requests
            
            headers = {
                'Authorization': f"Bearer {self.token['access_token']}",
                'X-Restli-Protocol-Version': '2.0'
            }
            
            response = requests.get(
                f"{LINKEDIN_API_BASE}/me",
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            self.logger.error(f"Failed to get profile: {e}")
            return None
    
    def create_post(self, text: str) -> bool:
        """Create a post on LinkedIn."""
        if not self.token:
            self.logger.error("Not authenticated")
            return False
        
        try:
            import requests
            
            headers = {
                'Authorization': f"Bearer {self.token['access_token']}",
                'X-Restli-Protocol-Version': '2.0',
                'Content-Type': 'application/json',
                'linkedin-version': '202402'
            }
            
            # Create post
            post_data = {
                "author": f"urn:li:person:{self.get_profile().get('id', '')}",
                "lifecycleState": "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {
                            "text": text
                        },
                        "shareMediaCategory": "NONE"
                    }
                },
                "visibility": {
                    "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
                }
            }
            
            response = requests.post(
                f"{LINKEDIN_API_BASE}/ugcPosts",
                headers=headers,
                json=post_data,
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            post_id = result.get('id', 'unknown')
            
            self.logger.info(f"Post created: {post_id}")
            
            # Log post
            self._log_post(post_id, text, 'success')
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create post: {e}")
            self._log_post('error', str(e), 'failed')
            return False
    
    def _log_post(self, post_id: str, content: str, status: str):
        """Log post to published folder."""
        log_file = self.notifications_folder / f'post_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'post_id': post_id,
            'content': content[:200],
            'status': status
        }
        
        log_file.write_text(json.dumps(log_entry, indent=2))
    
    def check_notifications(self) -> List[Dict]:
        """Check for new LinkedIn notifications."""
        # For Silver Tier, this is a placeholder
        # Full notification monitoring requires additional API permissions
        
        self.logger.info("Notification checking is limited in Silver Tier")
        self.logger.info("Manual monitoring recommended via LinkedIn.com")
        
        return []
    
    def create_notification_file(self, notification: Dict) -> Path:
        """Create action file for notification."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"LINKEDIN_NOTIFICATION_{timestamp}.md"
        filepath = self.notifications_folder / filename
        
        content = f'''---
type: linkedin_notification
received: {datetime.now().isoformat()}
notification_type: {notification.get('type', 'unknown')}
status: pending
---

# LinkedIn Notification

**Type:** {notification.get('type', 'Unknown')}

**Received:** {datetime.now().isoformat()}

---

## Content

{notification.get('content', 'No content')}

---

## Suggested Actions

- [ ] Review notification
- [ ] Respond if needed
- [ ] Engage with comment/like
- [ ] Archive after processing

---

## Notes

<!-- Add notes here -->

'''
        filepath.write_text(content)
        return filepath


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='LinkedIn Watcher')
    parser.add_argument('vault_path', help='Path to Obsidian vault')
    parser.add_argument('--authenticate', action='store_true', help='Run OAuth authentication')
    parser.add_argument('--check', action='store_true', help='Check for notifications')
    parser.add_argument('--post', type=str, help='Create post with given text')
    parser.add_argument('--status', action='store_true', help='Check authentication status')
    
    args = parser.parse_args()
    
    vault_path = Path(args.vault_path).resolve()
    
    if not vault_path.exists():
        print(f"Error: Vault not found: {vault_path}")
        sys.exit(1)
    
    watcher = LinkedInWatcher(str(vault_path))
    
    if args.authenticate:
        success = watcher.authenticate()
        sys.exit(0 if success else 1)
    
    elif args.status:
        if watcher.is_authenticated():
            print("✅ Authenticated with LinkedIn")
            if watcher.token:
                print(f"   Token expires: {watcher.token.get('expires_at', 'unknown')}")
        else:
            print("❌ Not authenticated")
            print("   Run: python linkedin_watcher.py --authenticate")
    
    elif args.check:
        if not watcher.is_authenticated():
            print("❌ Not authenticated. Run --authenticate first.")
            sys.exit(1)
        
        print("Checking LinkedIn notifications...")
        notifications = watcher.check_notifications()
        
        if notifications:
            print(f"Found {len(notifications)} notifications")
            for notif in notifications:
                filepath = watcher.create_notification_file(notif)
                print(f"  Created: {filepath.name}")
        else:
            print("No new notifications")
    
    elif args.post:
        if not watcher.is_authenticated():
            print("❌ Not authenticated. Run --authenticate first.")
            sys.exit(1)
        
        print("Creating LinkedIn post...")
        success = watcher.create_post(args.post)
        
        if success:
            print("✅ Post created successfully")
        else:
            print("❌ Failed to create post")
    
    else:
        parser.print_help()
        print()
        print("Examples:")
        print("  python linkedin_watcher.py ./AI_Employee_Vault --authenticate")
        print("  python linkedin_watcher.py ./AI_Employee_Vault --status")
        print("  python linkedin_watcher.py ./AI_Employee_Vault --check")
        print('  python linkedin_watcher.py ./AI_Employee_Vault --post "Hello LinkedIn!"')


if __name__ == '__main__':
    main()

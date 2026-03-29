#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LinkedIn OAuth Setup - Run once to authenticate with LinkedIn API.

This script will:
1. Open a browser window
2. Ask you to sign in with LinkedIn
3. Grant permissions to the AI Employee
4. Save the token to the vault for future use

Prerequisites:
1. Create LinkedIn app at: https://www.linkedin.com/developers/apps
2. Get Client ID and Client Secret
3. Save credentials to AI_Employee_Vault/.linkedin/credentials.json

Usage:
    python setup_linkedin_oauth.py /path/to/vault

Example:
    python setup_linkedin_oauth.py ./AI_Employee_Vault
"""

import sys
import json
import webbrowser
import hashlib
import base64
import os
from pathlib import Path
from datetime import datetime, timedelta
from urllib.parse import urlencode, parse_qs
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

# LinkedIn OAuth URLs
LINKEDIN_AUTH_URL = "https://www.linkedin.com/oauth/v2/authorization"
LINKEDIN_TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"

# LinkedIn API scopes
SCOPES = [
    'w_member_social',      # Post to LinkedIn
    'r_basicprofile',       # Read basic profile
    'r_emailaddress'        # Read email address
]


class OAuthHandler(BaseHTTPRequestHandler):
    """Handle OAuth callback from LinkedIn."""
    
    def do_GET(self):
        """Handle GET request (OAuth callback)."""
        if self.path.startswith('/callback'):
            # Parse authorization code from URL
            query_params = parse_qs(self.path.split('?')[1])
            auth_code = query_params.get('code', [None])[0]
            error = query_params.get('error', [None])[0]
            
            if error:
                self.send_response(400)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(f"Error: {error}".encode())
                return
            
            # Store auth code for main thread
            self.server.auth_code = auth_code
            
            # Send success page
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
        """Suppress logging."""
        pass


def generate_pkce_pair():
    """Generate PKCE code verifier and challenge."""
    # Generate random code verifier
    code_verifier = base64.urlsafe_b64encode(os.urandom(32)).rstrip(b'=').decode()
    
    # Generate code challenge from verifier
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode()).digest()
    ).rstrip(b'=').decode()
    
    return code_verifier, code_challenge


def setup_linkedin_oauth(vault_path: str):
    """Set up LinkedIn OAuth and save token."""
    vault = Path(vault_path).resolve()
    creds_folder = vault / '.linkedin'
    creds_file = creds_folder / 'credentials.json'
    token_file = creds_folder / 'token.json'
    
    # Ensure folder exists
    creds_folder.mkdir(parents=True, exist_ok=True)
    
    print("=" * 60)
    print("LinkedIn OAuth Setup for AI Employee")
    print("=" * 60)
    print()
    print(f"Credentials: {creds_file}")
    print(f"Token will be saved to: {token_file}")
    print()
    
    # Check if credentials file exists
    if not creds_file.exists():
        print(f"❌ ERROR: Credentials file not found: {creds_file}")
        print()
        print("Please create LinkedIn app and save credentials:")
        print("1. Go to: https://www.linkedin.com/developers/apps")
        print("2. Click 'Create app'")
        print("3. Fill in app details (requires LinkedIn Page)")
        print("4. Go to 'Auth' tab and copy Client ID & Secret")
        print("5. Create file with this content:")
        print()
        print(f"   {creds_file}")
        print("   {")
        print("     \"client_id\": \"your_client_id_here\",")
        print("     \"client_secret\": \"your_client_secret_here\",")
        print("     \"redirect_uri\": \"http://localhost:8080\"")
        print("   }")
        print()
        return False
    
    # Load credentials
    print("Loading credentials...")
    try:
        creds = json.loads(creds_file.read_text())
        client_id = creds.get('client_id')
        client_secret = creds.get('client_secret')
        redirect_uri = creds.get('redirect_uri', 'http://localhost:8080')
        
        if not client_id or not client_secret:
            print("❌ ERROR: Client ID or Secret missing in credentials file")
            return False
            
        print("✓ Credentials loaded")
    except Exception as e:
        print(f"❌ ERROR: Could not load credentials: {e}")
        return False
    
    # Check for existing token
    if token_file.exists():
        print("\n⚠️  Existing token found!")
        try:
            existing_token = json.loads(token_file.read_text())
            expires_at = existing_token.get('expires_at', '')
            if expires_at and datetime.fromisoformat(expires_at) > datetime.now():
                print(f"✓ Valid token exists (expires: {expires_at})")
                response = input("Do you want to refresh it? (y/n): ")
                if response.lower() != 'y':
                    print("\n✓ Using existing token")
                    return True
            else:
                print("⚠️  Token expired, will refresh")
        except:
            print("⚠️  Could not read existing token")
    
    print()
    print("=" * 60)
    print("Step 1: Authorize Application")
    print("=" * 60)
    print()
    
    # Generate PKCE
    code_verifier, code_challenge = generate_pkce_pair()
    
    # Build authorization URL
    auth_params = {
        'response_type': 'code',
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'scope': ' '.join(SCOPES),
        'state': base64.urlsafe_b64encode(os.urandom(16)).decode().rstrip('='),
        'code_challenge': code_challenge,
        'code_challenge_method': 'S256'
    }
    
    auth_url = f"{LINKEDIN_AUTH_URL}?{urlencode(auth_params)}"
    
    print("Opening browser for LinkedIn authentication...")
    print()
    print("Please:")
    print("1. Sign in with your LinkedIn account")
    print("2. Grant permissions to the AI Employee")
    print("3. You'll see 'Authentication Successful' page")
    print("4. This script will automatically continue")
    print()
    
    # Open browser
    webbrowser.open(auth_url)
    
    # Start local server to receive callback
    print("Waiting for LinkedIn callback...")
    server = HTTPServer(('localhost', 8080), OAuthHandler)
    server.auth_code = None
    server.timeout = 120  # 2 minute timeout
    
    # Handle callback in separate thread
    def handle_callback():
        server.handle_request()
    
    thread = threading.Thread(target=handle_callback)
    thread.daemon = True
    thread.start()
    thread.join(timeout=120)
    
    server.server_close()
    
    auth_code = server.auth_code
    
    if not auth_code:
        print("\n❌ ERROR: Authentication timeout or cancelled")
        print("Please try again")
        return False
    
    print("\n✓ Authorization code received")
    print()
    print("=" * 60)
    print("Step 2: Exchange Code for Access Token")
    print("=" * 60)
    print()
    
    # Exchange authorization code for access token
    import requests
    
    token_data = {
        'grant_type': 'authorization_code',
        'code': auth_code,
        'redirect_uri': redirect_uri,
        'client_id': client_id,
        'client_secret': client_secret,
        'code_verifier': code_verifier
    }
    
    try:
        response = requests.post(LINKEDIN_TOKEN_URL, data=token_data)
        response.raise_for_status()
        
        token_response = response.json()
        
        if 'access_token' not in token_response:
            print(f"❌ ERROR: No access token in response: {token_response}")
            return False
        
        # Create token object
        access_token = token_response['access_token']
        expires_in = token_response.get('expires_in', 604800)  # Default 7 days
        refresh_token = token_response.get('refresh_token', '')
        
        token_obj = {
            'access_token': access_token,
            'expires_in': expires_in,
            'expires_at': (datetime.now() + timedelta(seconds=expires_in)).isoformat(),
            'refresh_token': refresh_token,
            'scope': ' '.join(SCOPES),
            'created_at': datetime.now().isoformat()
        }
        
        # Save token
        token_file.write_text(json.dumps(token_obj, indent=2))
        
        # Set restrictive permissions
        try:
            os.chmod(token_file, 0o600)
        except:
            pass  # Ignore on Windows
        
        print("✓ Access token received and saved!")
        print()
        print("=" * 60)
        print("LinkedIn OAuth Setup Complete!")
        print("=" * 60)
        print()
        print(f"Token saved to: {token_file}")
        print(f"Expires at: {token_obj['expires_at']}")
        print()
        print("You can now use LinkedIn poster with auto-publish:")
        print(f"  python scripts/linkedin_poster.py {vault_path} --publish")
        print()
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ ERROR: Token exchange failed: {e}")
        return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


def main():
    if len(sys.argv) < 2:
        print("Usage: python setup_linkedin_oauth.py <vault_path>")
        print()
        print("Example:")
        print("  python setup_linkedin_oauth.py ./AI_Employee_Vault")
        print()
        print("Prerequisites:")
        print("1. Create LinkedIn app: https://www.linkedin.com/developers/apps")
        print("2. Save credentials to: AI_Employee_Vault/.linkedin/credentials.json")
        print()
        print("Credentials file format:")
        print("  {")
        print("    \"client_id\": \"your_client_id\",")
        print("    \"client_secret\": \"your_client_secret\",")
        print("    \"redirect_uri\": \"http://localhost:8080\"")
        print("  }")
        sys.exit(1)
    
    vault_path = sys.argv[1]
    
    success = setup_linkedin_oauth(vault_path)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()

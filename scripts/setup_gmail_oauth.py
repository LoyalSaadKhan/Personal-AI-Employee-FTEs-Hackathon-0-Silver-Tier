#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gmail OAuth Setup - Run once to authenticate with Gmail API.

This script will:
1. Open a browser window
2. Ask you to sign in with Google
3. Save the token to the vault for future use

Usage:
    python setup_gmail_oauth.py /path/to/vault /path/to/credentials.json

Example:
    python setup_gmail_oauth.py ./AI_Employee_Vault ./AI_Employee_Vault/.gmail/credentials.json
"""

import sys
import os
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle

# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']


def setup_gmail_oauth(vault_path: str, credentials_path: str):
    """Set up Gmail OAuth and save token."""
    vault = Path(vault_path).resolve()
    creds_file = Path(credentials_path).resolve()
    token_file = vault / '.gmail' / 'token.json'
    
    # Ensure .gmail folder exists
    token_file.parent.mkdir(parents=True, exist_ok=True)
    
    print("=" * 60)
    print("Gmail OAuth Setup for AI Employee")
    print("=" * 60)
    print()
    print(f"Credentials: {creds_file}")
    print(f"Token will be saved to: {token_file}")
    print()
    
    # Check if credentials file exists
    if not creds_file.exists():
        print(f"ERROR: Credentials file not found: {creds_file}")
        print("Make sure credentials.json exists in the specified location.")
        return False
    
    creds = None
    
    # Try to load existing token
    if token_file.exists():
        print("Loading existing token...")
        try:
            creds = Credentials.from_authorized_user_file(token_file, SCOPES)
            print("✓ Existing token loaded")
        except Exception as e:
            print(f"Could not load existing token: {e}")
            creds = None
    
    # Refresh or get new token
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Refreshing expired token...")
            try:
                creds.refresh(Request())
                print("✓ Token refreshed successfully")
            except Exception as e:
                print(f"Token refresh failed: {e}")
                creds = None
        
        if not creds:
            print()
            print("=" * 60)
            print("OAuth Authentication Required")
            print("=" * 60)
            print()
            print("A browser window will open. Please:")
            print("1. Sign in with your Google account")
            print("2. Grant permissions to the AI Employee")
            print("3. The browser will show 'Authentication successful'")
            print("4. This script will save the token automatically")
            print()
            input("Press Enter to open the browser...")
            
            try:
                flow = InstalledAppFlow.from_client_secrets_file(
                    creds_file, SCOPES
                )
                creds = flow.run_local_server(port=0, open_browser=True)
                print()
                print("✓ OAuth successful!")
                
            except Exception as e:
                print()
                print(f"ERROR: OAuth failed: {e}")
                print("Please try again or check your credentials.")
                return False
    
    # Save the token
    print()
    print("Saving token...")
    try:
        token_file.write_text(creds.to_json())
        
        # Set restrictive permissions (Windows doesn't support chmod well)
        try:
            os.chmod(token_file, 0o600)
        except:
            pass  # Ignore on Windows
        
        print(f"✓ Token saved to: {token_file}")
        print()
        print("=" * 60)
        print("Gmail OAuth Setup Complete!")
        print("=" * 60)
        print()
        print("You can now run the Gmail Watcher:")
        print(f"  python scripts/gmail_watcher.py {vault_path}")
        print()
        return True
        
    except Exception as e:
        print(f"ERROR: Could not save token: {e}")
        return False


def main():
    if len(sys.argv) < 3:
        print("Usage: python setup_gmail_oauth.py <vault_path> <credentials_path>")
        print()
        print("Example:")
        print("  python setup_gmail_oauth.py ./AI_Employee_Vault ./AI_Employee_Vault/.gmail/credentials.json")
        sys.exit(1)
    
    vault_path = sys.argv[1]
    credentials_path = sys.argv[2]
    
    success = setup_gmail_oauth(vault_path, credentials_path)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()

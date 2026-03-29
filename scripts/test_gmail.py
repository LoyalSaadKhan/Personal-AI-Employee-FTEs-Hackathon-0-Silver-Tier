#!/usr/bin/env python3
"""Test Gmail API connection."""

import sys
from pathlib import Path

vault_path = Path('./AI_Employee_Vault').resolve()
creds_path = vault_path / '.gmail' / 'credentials.json'
token_path = vault_path / '.gmail' / 'token.json'

print("=" * 60)
print("Gmail API Connection Test")
print("=" * 60)
print()

# Check files exist
print("Checking files...")
print(f"  Credentials: {creds_path.exists()}")
print(f"  Token: {token_path.exists()}")

if not creds_path.exists():
    print("❌ Credentials file not found!")
    sys.exit(1)

if not token_path.exists():
    print("❌ Token file not found!")
    print("   Run: python scripts/setup_gmail_oauth.py ./AI_Employee_Vault")
    sys.exit(1)

# Try to connect
print()
print("Testing Gmail API connection...")

try:
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    from google.auth.transport.requests import Request
    
    # Load token
    creds = Credentials.from_authorized_user_file(token_path, [
        'https://www.googleapis.com/auth/gmail.readonly'
    ])
    
    # Check if token is valid
    if not creds.valid:
        print("⚠️  Token expired, trying to refresh...")
        if creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                print("✓ Token refreshed!")
                # Save updated token
                token_path.write_text(creds.to_json())
            except Exception as e:
                print(f"❌ Token refresh failed: {e}")
                print("   Run: python scripts/setup_gmail_oauth.py ./AI_Employee_Vault")
                sys.exit(1)
        else:
            print("❌ Token invalid!")
            print("   Run: python scripts/setup_gmail_oauth.py ./AI_Employee_Vault")
            sys.exit(1)
    
    print("✓ Token is valid")
    
    # Build Gmail service
    service = build('gmail', 'v1', credentials=creds)
    
    # Get profile
    print()
    print("Fetching Gmail profile...")
    profile = service.users().getProfile(userId='me').execute()
    print(f"✓ Connected to: {profile['emailAddress']}")
    
    # Check for unread emails
    print()
    print("Checking for unread emails...")
    results = service.users().messages().list(
        userId='me',
        q='is:unread',
        maxResults=5
    ).execute()
    
    messages = results.get('messages', [])
    
    if messages:
        print(f"✓ Found {len(messages)} unread email(s)")
        print()
        print("Recent unread emails:")
        for msg in messages[:3]:
            message = service.users().messages().get(
                userId='me', 
                id=msg['id'],
                format='metadata',
                metadataHeaders=['From', 'Subject', 'Date']
            ).execute()
            
            headers = {h['name']: h['value'] for h in message['payload']['headers']}
            print(f"  - From: {headers.get('From', 'Unknown')}")
            print(f"    Subject: {headers.get('Subject', 'No Subject')}")
            print(f"    Date: {headers.get('Date', 'Unknown')}")
            print()
    else:
        print("⚠️  No unread emails found")
        print()
        print("Tips:")
        print("  - Make sure emails are marked as UNREAD")
        print("  - Gmail may mark emails as important automatically")
        print("  - Try sending yourself a test email")
    
    # Check for important emails
    print()
    print("Checking for important emails...")
    results = service.users().messages().list(
        userId='me',
        q='is:important is:unread',
        maxResults=5
    ).execute()
    
    messages = results.get('messages', [])
    print(f"Found {len(messages)} important + unread email(s)")
    
    print()
    print("=" * 60)
    print("✅ Gmail API Connection: SUCCESS")
    print("=" * 60)
    
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

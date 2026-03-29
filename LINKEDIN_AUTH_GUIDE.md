# LinkedIn Authentication Guide

## 🔐 Setup LinkedIn OAuth for AI Employee

This guide walks you through authenticating with LinkedIn API so the AI Employee can automatically post to LinkedIn.

---

## 📋 Prerequisites

### 1. LinkedIn Company Page (Required)

LinkedIn requires you to have a **Company Page** to create an app.

**If you don't have one:**
1. Go to: https://www.linkedin.com/company/setup/new/
2. Fill in:
   - **Company Name:** Your business name
   - **LinkedIn Public URL:** linkedin.com/company/your-company
   - **Website:** Your website URL
   - **Industry:** Select appropriate
   - **Company Size:** Select appropriate
3. Click **Create page**

---

## 🏗️ Step 1: Create LinkedIn App

1. **Go to LinkedIn Developer Portal:**
   https://www.linkedin.com/developers/apps

2. **Click "Create app"**

3. **Fill in app details:**
   ```
   App name: AI Employee
   Company Page: [Select your page from dropdown]
   App logo: Upload any 100x100px image
   ```

4. **Accept terms and click "Create"**

---

## 🔑 Step 2: Get Credentials

1. **Go to "Auth" tab** in your app

2. **Copy these values:**
   - **Client ID** (long string)
   - **Client Secret** (click "Show" to reveal)

3. **Add Redirect URL:**
   - Click "Add redirect URL"
   - Enter: `http://localhost:8080`
   - Click "Save"

---

## 📁 Step 3: Save Credentials File

Create folder and credentials file:

```bash
# Create folder
mkdir AI_Employee_Vault\.linkedin

# Create credentials.json
notepad AI_Employee_Vault\.linkedin\credentials.json
```

**Paste this content (replace with your values):**

```json
{
  "client_id": "86xxxxxxxxxxxxxx",
  "client_secret": "GOCSPX-xxxxxxxxxxxxxxxxxxxx",
  "redirect_uri": "http://localhost:8080"
}
```

**Save the file.**

---

## 🔐 Step 4: Run OAuth Setup

```bash
# Navigate to project directory
cd "C:\Users\Jawaria Noor\Desktop\Personal-AI-Employee-FTEs\Personal-AI-Employee-FTEs"

# Run OAuth setup
python scripts/setup_linkedin_oauth.py ./AI_Employee_Vault
```

**What happens:**
1. Browser opens with LinkedIn sign-in
2. Sign in with your LinkedIn account
3. Grant permissions to AI Employee
4. Browser shows "Authentication Successful"
5. Token is saved to `AI_Employee_Vault/.linkedin/token.json`

---

## ✅ Step 5: Verify Authentication

```bash
# Check if token was created
dir AI_Employee_Vault\.linkedin\

# Should see:
# credentials.json
# token.json
```

**View token (optional):**
```bash
type AI_Employee_Vault\.linkedin\token.json
```

---

## 🚀 Step 6: Use LinkedIn Poster

### Generate Draft Post

```bash
python scripts/linkedin_poster.py ./AI_Employee_Vault --draft
```

### Publish to LinkedIn

**Option A: Manual Posting (Silver Tier)**
```bash
python scripts/linkedin_poster.py ./AI_Employee_Vault --publish

# Then manually:
# 1. Open the published file
# 2. Copy content
# 3. Go to LinkedIn.com
# 4. Paste and post
```

**Option B: Auto-Posting (After OAuth)**
```bash
# The poster will automatically use the OAuth token
# to post directly to LinkedIn
python scripts/linkedin_poster.py ./AI_Employee_Vault --publish --auto
```

---

## 📊 LinkedIn API Permissions

The AI Employee requests these permissions:

| Permission | Scope | Purpose |
|------------|-------|---------|
| Post to LinkedIn | `w_member_social` | Create posts on your behalf |
| Read Profile | `r_basicprofile` | Verify account |
| Read Email | `r_emailaddress` | Account verification |

---

## 🔄 Token Management

### Check Token Status

```bash
python -c "import json; t=json.load(open('AI_Employee_Vault/.linkedin/token.json')); print(f'Expires: {t.get(\"expires_at\", \"unknown\")}')"
```

### Refresh Token

Tokens expire after 60 days. To refresh:

```bash
python scripts/setup_linkedin_oauth.py ./AI_Employee_Vault
```

This will get a new token (old one is overwritten).

---

## 🐛 Troubleshooting

### Error: "Credentials file not found"

**Solution:**
```bash
# Verify file exists
dir AI_Employee_Vault\.linkedin\credentials.json

# If missing, create it (see Step 3)
```

### Error: "Client ID or Secret missing"

**Solution:**
- Open `AI_Employee_Vault\.linkedin\credentials.json`
- Verify `client_id` and `client_secret` are present
- No extra spaces or quotes

### Error: "LinkedIn Page required"

**Solution:**
1. Create LinkedIn Company Page first (see Prerequisites)
2. Wait 5 minutes for page to propagate
3. Try creating app again

### Error: "Redirect URL mismatch"

**Solution:**
- In LinkedIn app settings, ensure redirect URL is exactly: `http://localhost:8080`
- No trailing slash
- Use http, not https

### Browser doesn't open

**Solution:**
- Copy the URL from terminal
- Paste into browser manually
- Complete authentication

---

## 📁 File Structure

```
AI_Employee_Vault/
└── .linkedin/
    ├── credentials.json          # Your app credentials (keep secret!)
    └── token.json                # OAuth access token (keep secret!)
```

**⚠️ Security:**
- NEVER commit these files to Git
- NEVER share these files publicly
- Add to `.gitignore`:
  ```
  .linkedin/credentials.json
  .linkedin/token.json
  ```

---

## 🎯 Quick Reference

| Task | Command |
|------|---------|
| Create LinkedIn app | https://www.linkedin.com/developers/apps |
| Create credentials file | `AI_Employee_Vault/.linkedin/credentials.json` |
| Run OAuth setup | `python scripts/setup_linkedin_oauth.py ./AI_Employee_Vault` |
| Generate post | `python scripts/linkedin_poster.py ./AI_Employee_Vault --draft` |
| Publish post | `python scripts/linkedin_poster.py ./AI_Employee_Vault --publish` |
| Check token | `type AI_Employee_Vault\.linkedin\token.json` |
| Refresh token | Run OAuth setup again |

---

## 📞 Need Help?

1. **Check LinkedIn Developer Docs:**
   https://learn.microsoft.com/en-us/linkedin/shared/authentication/authentication

2. **Verify App Status:**
   - Go to https://www.linkedin.com/developers/apps
   - Select your app
   - Check "Auth" tab for settings

3. **Test API Access:**
   ```bash
   # After OAuth, test token
   curl -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
        https://api.linkedin.com/v2/me
   ```

---

**LinkedIn OAuth Setup Complete!** 🎉

*Your AI Employee can now post to LinkedIn automatically.*

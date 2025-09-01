# Google Service Account Setup

## ⚠️ SECURITY WARNING ⚠️

**NEVER commit real service account credentials to version control!**

The `service-account-key.json` file contains sensitive credentials and should be kept secure.

## Setup Instructions

1. **Create a Google Cloud Service Account:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Navigate to IAM & Admin > Service Accounts
   - Create a new service account or use an existing one
   - Download the JSON key file

2. **Place the credentials file:**
   ```bash
   # Copy your downloaded service account key to:
   cp ~/Downloads/your-service-account-key.json backend/service-account-key.json
   ```

3. **Verify the file is ignored:**
   ```bash
   # Check that the file is not tracked by git
   git status backend/service-account-key.json
   # Should show: "Untracked files"
   ```

4. **Set up environment variables (alternative):**
   Instead of using a file, you can set environment variables:
   ```bash
   export GOOGLE_SERVICE_ACCOUNT_EMAIL="your-service-account@project.iam.gserviceaccount.com"
   export GOOGLE_SERVICE_ACCOUNT_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
   ```

## File Structure

- `service-account-key.template.json` - Template showing required fields (safe to commit)
- `service-account-key.json` - Your actual credentials (NEVER commit this!)
- `.gitignore` - Ensures credentials are not accidentally committed

## Troubleshooting

If you see the credentials file in `git status`, it means it was accidentally added. Remove it:

```bash
git rm --cached backend/service-account-key.json
git commit -m "Remove accidentally committed service account credentials"
```

## Security Best Practices

1. **Rotate keys regularly** - Generate new service account keys every 90 days
2. **Limit permissions** - Only grant the minimum required permissions
3. **Monitor usage** - Check Google Cloud audit logs for unusual activity
4. **Use environment variables** - Prefer environment variables over files in production
5. **Secure storage** - Store production credentials in secure secret management systems

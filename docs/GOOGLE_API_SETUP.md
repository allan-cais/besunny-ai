# Google API Integration Setup Guide

## What You've Already Done ✅
- Google OAuth client setup
- Gmail API enabled  
- Service account created

## What You Need to Do Now 🔧

### 1. Download Service Account Key
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to **IAM & Admin** → **Service Accounts**
3. Find your service account and click on it
4. Go to **Keys** tab
5. Click **Add Key** → **Create new key**
6. Choose **JSON** format
7. Download the key file

### 2. Place the Key File
```bash
# Place the downloaded JSON file in your backend directory
# Example: backend/google-credentials.json
```

### 3. Update Environment Variables
Add these to your `backend/.env` file:

```env
# Google Cloud Configuration
GOOGLE_PROJECT_ID=your-project-id-here
GOOGLE_CLIENT_ID=your-oauth-client-id
GOOGLE_CLIENT_SECRET=your-oauth-client-secret
GOOGLE_SERVICE_ACCOUNT_KEY_PATH=./google-credentials.json

# Webhook Configuration (for local development)
WEBHOOK_BASE_URL=http://localhost:8000

# For production, use your actual domain:
# WEBHOOK_BASE_URL=https://your-domain.com
```

### 4. Install Required Python Packages
```bash
cd backend
pip install google-api-python-client google-auth
```

### 5. Test the Integration
```bash
# Test the email processing service
python test_virtual_email_processing.py

# Start the backend server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 6. Test API Endpoints
```bash
# Test Gmail watch setup (requires authentication)
curl -X POST http://localhost:8000/api/v1/gmail-watches/setup \
  -H "Authorization: Bearer YOUR_TOKEN"

# Test webhook endpoint
curl -X POST http://localhost:8000/api/v1/webhooks/gmail-test
```

## OAuth Consent Screen Configuration

Make sure your OAuth consent screen includes these scopes:
- `https://www.googleapis.com/auth/gmail.readonly`
- `https://www.googleapis.com/auth/gmail.modify` 
- `https://www.googleapis.com/auth/gmail.watch`

## Service Account Permissions

Your service account needs these roles:
- **Gmail API** access
- **Service Account Token Creator** (if using domain-wide delegation)

## Common Issues & Solutions

### Issue: "Google service account key path not configured"
**Solution**: Check your `.env` file and make sure `GOOGLE_SERVICE_ACCOUNT_KEY_PATH` is set correctly.

### Issue: "Invalid credentials"
**Solution**: Verify the service account key file path and ensure the file is readable.

### Issue: "Insufficient permissions"
**Solution**: Make sure your service account has the necessary Gmail API permissions.

### Issue: "Webhook not receiving notifications"
**Solution**: 
1. Check that `WEBHOOK_BASE_URL` is accessible from the internet
2. Verify Gmail watches are created successfully
3. Check the webhook endpoint is responding

## Next Steps After Setup

Once this is working:
1. **Test email processing** by sending an email to `ai+testuser@besunny.ai`
2. **Verify webhook receives** the Gmail notification
3. **Check document creation** in your Supabase database
4. **Move to Part 2**: Drive file processing

## Security Notes

- Keep your service account key file secure
- Don't commit the key file to version control
- Use environment variables for sensitive configuration
- Consider using Google Cloud Secret Manager for production

---

**Status**: Ready for testing once environment variables are set ✅

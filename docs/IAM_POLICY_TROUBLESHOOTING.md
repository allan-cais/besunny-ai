# IAM Policy Troubleshooting Guide

## Domain Restricted Sharing Error

### Error Message
```
The 'Domain Restricted Sharing' organization policy (constraints/iam.allowedPolicyMemberDomains) is enforced. 
Only principals in allowed domains can be added as principals in the policy.
```

### What This Means
Your Google Cloud organization has a security policy that restricts which domains can be added to IAM policies. This prevents setting up Gmail API webhooks that require Pub/Sub topic permissions.

### Root Cause
The organization policy `constraints/iam.allowedPolicyMemberDomains` is enabled and doesn't include the necessary domains for Google Cloud service accounts.

### Solutions

#### Option 1: Update Organization Policy (Recommended)

1. **Access Organization Policies**:
   - Go to [Google Cloud Console > IAM & Admin > Organization Policies](https://console.cloud.google.com/iam-admin/orgpolicies)
   - Select your organization (not just the project)

2. **Find Domain Restricted Sharing Policy**:
   - Search for `constraints/iam.allowedPolicyMemberDomains`
   - Click on it to edit

3. **Add Required Domains**:
   - Add `*.iam.gserviceaccount.com` to allow all Google Cloud service accounts
   - Or add your specific project domain: `sunny-ai-468016.iam.gserviceaccount.com`

4. **Save Changes**:
   - Click "Set Policy" to apply the changes
   - Wait 5-10 minutes for changes to propagate

#### Option 2: Create New Project (Quick Fix)

If you can't modify the organization policy:

1. **Create New Project**:
   ```bash
   gcloud projects create sunny-ai-gmail-$(date +%s) --name="Sunny AI Gmail Integration"
   ```

2. **Update Configuration**:
   ```python
   # In your config files, change the project ID
   topic_name = "projects/YOUR_NEW_PROJECT_ID/topics/gmail-notifications"
   ```

3. **Enable Required APIs**:
   - Gmail API
   - Pub/Sub API
   - Google Drive API

4. **Set Up Service Account**:
   - Create new service account in the new project
   - Download new credentials
   - Update your environment variables

#### Option 3: Contact Organization Admin

If you don't have permission to modify organization policies:

1. **Contact your Google Workspace administrator**
2. **Request to add `*.iam.gserviceaccount.com` to allowed domains**
3. **Or request permission to modify organization policies**

### Required Service Account Permissions

Your service account needs these roles:

1. **Pub/Sub Publisher** (`roles/pubsub.publisher`)
2. **Gmail API Admin** (`roles/gmail.admin`)
3. **Service Account Token Creator** (`roles/iam.serviceAccountTokenCreator`)

### Verification Steps

After making changes:

1. **Test Pub/Sub Access**:
   ```bash
   cd backend
   python test_pubsub_access.py
   ```

2. **Test Gmail Watch Setup**:
   ```bash
   cd backend
   python test_gmail_watch_setup.py
   ```

3. **Check API Endpoint**:
   ```bash
   curl -X POST http://localhost:8000/api/v1/gmail/watch/setup \
     -H "X-Admin-Token: YOUR_ADMIN_TOKEN"
   ```

### Environment Variables

Ensure these are set correctly:

```env
GOOGLE_PROJECT_ID=your-project-id
GOOGLE_SERVICE_ACCOUNT_KEY_BASE64=your-base64-encoded-key
WEBHOOK_BASE_URL=http://localhost:8000
```

### Common Issues

1. **Domain Delegation Not Enabled**:
   - Go to Google Workspace Admin > Security > API Controls > Domain-wide Delegation
   - Add your service account client ID

2. **APIs Not Enabled**:
   - Enable Gmail API, Pub/Sub API, and Google Drive API in your project

3. **Service Account Key Issues**:
   - Ensure the key is properly base64 encoded
   - Check that the key hasn't expired or been revoked

### Getting Help

If you continue to have issues:

1. **Check Google Cloud Console logs** for detailed error messages
2. **Review service account permissions** in IAM & Admin
3. **Verify organization policies** are correctly configured
4. **Contact Google Cloud Support** if the issue persists

### Prevention

To avoid this issue in the future:

1. **Plan ahead** when setting up new Google Cloud projects
2. **Document organization policies** that affect your projects
3. **Use separate projects** for different integrations if needed
4. **Regularly review** service account permissions and policies

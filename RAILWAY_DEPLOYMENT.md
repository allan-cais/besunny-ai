# Railway Deployment Guide for BeSunny AI

This guide will help you deploy the BeSunny AI frontend to Railway.com.

## Prerequisites

- A Railway account
- Your Supabase project URL and API keys
- Google OAuth credentials (if using Google integration)

## Quick Deployment

1. **Connect your repository to Railway:**
   - Go to [Railway.app](https://railway.app)
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your `besunny-ai` repository

2. **Configure environment variables:**
   In your Railway project dashboard, add these environment variables:
   ```
   NODE_ENV=production
   PORT=3000
   VITE_SUPABASE_URL=https://your-project.supabase.co
   VITE_SUPABASE_ANON_KEY=your-anon-key
   VITE_GOOGLE_CLIENT_ID=your-google-client-id
   VITE_GOOGLE_CLIENT_SECRET=your-google-client-secret
   ```

3. **Deploy:**
   - Railway will automatically detect the configuration and start building
   - The build process will use Nixpacks to install Node.js and build your app
   - Once built, it will start the app using `npm start`

## Configuration Files

### `railway.toml` (Primary Configuration)
This file tells Railway how to build and deploy your app:
- Uses Nixpacks builder
- Builds with `npm run build`
- Starts with `npm start`
- Includes health checks and restart policies

### `nixpacks.toml` (Build Configuration)
This file ensures Railway uses the correct Node.js runtime:
- Installs Node.js and npm
- Runs `npm ci --only=production` for dependencies
- Builds with `npm run build`
- Starts with `npm start`

### `Dockerfile` (Alternative)
If you prefer Docker deployment, uncomment the Dockerfile section in `railway.toml`.

## Troubleshooting

### Build Errors
If you encounter build errors:

1. **Check the build logs** in Railway dashboard
2. **Verify environment variables** are set correctly
3. **Ensure all dependencies** are in `package.json`
4. **Check Node.js version** compatibility

### Runtime Errors
If the app fails to start:

1. **Check the logs** in Railway dashboard
2. **Verify PORT environment variable** is set
3. **Check if the app is binding** to the correct host/port
4. **Verify environment variables** are accessible

### Common Issues

1. **Module not found errors:** Ensure all imports are correct and files exist
2. **Port binding issues:** Check if the app is binding to `0.0.0.0` and using the `PORT` env var
3. **Environment variable issues:** Ensure all `VITE_*` variables are set in Railway

## Environment Variables Reference

| Variable | Description | Required |
|----------|-------------|----------|
| `NODE_ENV` | Environment mode | Yes |
| `PORT` | Port to bind to | Yes |
| `VITE_SUPABASE_URL` | Supabase project URL | Yes |
| `VITE_SUPABASE_ANON_KEY` | Supabase anonymous key | Yes |
| `VITE_GOOGLE_CLIENT_ID` | Google OAuth client ID | If using Google |
| `VITE_GOOGLE_CLIENT_SECRET` | Google OAuth client secret | If using Google |

## Custom Domains

To add a custom domain:

1. Go to your Railway project dashboard
2. Click on "Settings" → "Domains"
3. Add your custom domain
4. Configure DNS records as instructed

## Monitoring

Railway provides:
- **Build logs** for debugging deployment issues
- **Runtime logs** for debugging runtime issues
- **Metrics** for performance monitoring
- **Health checks** for uptime monitoring

## Support

If you encounter issues:
1. Check the Railway documentation
2. Review the build and runtime logs
3. Verify your configuration files
4. Check the troubleshooting section above

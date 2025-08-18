# Railway Port Configuration Guide

## 🚀 **Port Settings for Each Service**

### **Frontend Service**
- **Port Setting:** `$PORT` (Railway auto-assigns)
- **Start Command:** `npx serve -s dist -l $PORT`
- **What Happens:** Railway assigns an available port automatically

### **Backend Service**
- **Port Setting:** `$PORT` (Railway auto-assigns)
- **Start Command:** `cd backend && python start.py`
- **What Happens:** Railway assigns an available port automatically

## 🔧 **Why Use `$PORT` Instead of Fixed Ports?**

1. **Automatic Assignment:** Railway finds available ports
2. **No Conflicts:** Multiple services can run simultaneously
3. **Dynamic Scaling:** Works with Railway's scaling features
4. **Best Practice:** Railway's recommended approach
5. **Environment Agnostic:** Works in dev, staging, and production

## 📋 **Current Configuration**

### **Frontend Service:**
```toml
[deploy]
startCommand = "npx serve -s dist -l $PORT"
```

### **Backend Service:**
```toml
[deploy.envs]
HOST = "0.0.0.0"
PORT = "$PORT"
```

## 🎯 **What You Need to Do in Railway Dashboard**

### **Frontend Service:**
1. **No manual port setting needed**
2. Railway will automatically assign a port
3. The service will be available at: `https://your-frontend-service.railway.app`

### **Backend Service:**
1. **No manual port setting needed**
2. Railway will automatically assign a port
3. The service will be available at: `https://your-backend-service.railway.app`

## 🔍 **How Railway Port Assignment Works**

1. **Deployment:** Railway deploys your service
2. **Port Assignment:** Railway finds an available port (e.g., 3000, 8000, 8080)
3. **Environment Variable:** Sets `$PORT` to the assigned port
4. **Service Start:** Your app starts using `$PORT`
5. **External URL:** Railway provides a public URL

## 💡 **Benefits of This Approach**

- ✅ **No Port Conflicts:** Multiple services can run
- ✅ **Automatic Scaling:** Works with Railway's scaling
- ✅ **Environment Independent:** Same config works everywhere
- ✅ **Best Practice:** Follows Railway recommendations
- ✅ **Zero Configuration:** No manual port management needed

## ⚠️ **Important Notes**

- **Don't set fixed ports** like `8000` or `3000`
- **Always use `$PORT`** environment variable
- **Railway handles port assignment** automatically
- **Your app will work** regardless of the assigned port

## 🚀 **Deployment Commands**

```bash
# Frontend (uses $PORT automatically)
railway up --service frontend --config .railway/railway-frontend.toml

# Backend (uses $PORT automatically)  
railway up --service backend --config .railway/railway-backend.toml
```

## 🎉 **Result**

After deployment:
- **Frontend:** Available at `https://your-frontend-service.railway.app`
- **Backend:** Available at `https://your-backend-service.railway.app`
- **No port configuration needed** in Railway dashboard
- **Both services work independently** with auto-assigned ports

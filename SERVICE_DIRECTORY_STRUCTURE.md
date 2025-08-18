# Service Directory Structure

## 🎯 **Directory Configuration for Each Service**

### **Frontend Service**
**Root Directory:** `.` (project root)
**Working Directory:** `.` (project root)
**Build Source:** `.` (project root)

**What This Means:**
- Railway will read from the project root
- All build commands run from the project root
- Frontend files are served from the project root
- Build output goes to `dist/` directory

**Files Included:**
```
besunny-ai/
├── src/                    ← React source code
├── public/                 ← Static assets
├── package.json            ← Node.js dependencies
├── vite.config.ts          ← Build configuration
├── tailwind.config.ts      ← Styling configuration
├── tsconfig*.json          ← TypeScript configuration
└── dist/                   ← Build output (created during build)
```

**Files Excluded:**
- `backend/**` - All backend code
- `supabase/**` - Supabase functions
- `database/**` - Database migrations
- `docs/**` - Documentation
- `*.md` - Markdown files
- `Dockerfile*` - Docker files
- `railway*.toml` - Railway configs
- `deploy-*.sh` - Deployment scripts

---

### **Backend Service**
**Root Directory:** `.` (project root)
**Working Directory:** `backend/` (backend subdirectory)
**Build Source:** `.` (project root)

**What This Means:**
- Railway will read from the project root
- Build commands run from the project root
- **Service runs from `backend/` directory**
- Python files are executed from `backend/` directory

**Files Included:**
```
besunny-ai/
├── backend/                ← Backend source code
│   ├── app/                ← FastAPI application
│   ├── requirements.txt    ← Python dependencies
│   ├── start.py           ← Entry point
│   └── ...                ← Other backend files
└── ...                     ← Other project files (excluded from build)
```

**Files Excluded:**
- `src/**` - Frontend source code
- `public/**` - Frontend static assets
- `package*.json` - Node.js files
- `vite.config.ts` - Frontend build config
- `tailwind.config.ts` - Frontend styling
- `tsconfig*.json` - Frontend TypeScript
- `*.md` - Documentation
- `Dockerfile*` - Docker files
- `railway*.toml` - Railway configs
- `deploy-*.sh` - Deployment scripts
- `node_modules/**` - Node.js dependencies
- `dist/**` - Frontend build output

---

## 🔧 **Why This Configuration Works**

### **Frontend Service:**
1. **Reads from root:** Can access `package.json`, `src/`, `public/`
2. **Builds from root:** `npm install && npm run build:production`
3. **Serves from root:** `npx serve -s dist -l $PORT`
4. **Excludes backend:** Won't see Python files

### **Backend Service:**
1. **Reads from root:** Can access `backend/` directory
2. **Builds from root:** `pip install -r requirements.txt`
3. **Runs from backend:** `cd backend && python start.py`
4. **Excludes frontend:** Won't see Node.js files

---

## 🚀 **Deployment Commands**

### **Frontend:**
```bash
railway up --service frontend --config .railway/railway-frontend.toml
```

### **Backend:**
```bash
railway up --service backend --config .railway/railway-backend.toml
```

---

## 💡 **Key Benefits**

1. **Clear Separation:** Each service only sees relevant files
2. **No Conflicts:** Frontend won't try to build Python code
3. **Proper Context:** Backend runs from correct directory
4. **Efficient Builds:** Only necessary files are included
5. **Railway Compatible:** Uses Railway's expected directory structure

---

## ⚠️ **Important Notes**

- **Frontend working directory:** `.` (root) - serves static files
- **Backend working directory:** `backend/` - runs Python code
- **Build source:** Both use `.` (root) but exclude different files
- **Service isolation:** Each service only sees its own technology stack

# 🌐 GitHub Pages + VCL Server Deployment

## **New Deployment Architecture**

Your Mini-task AI Tutor application is now deployed using a hybrid approach:

### **Frontend: GitHub Pages**
- **URL**: https://daksh204singh.github.io/mini-task-botbuilder
- **Technology**: React + TypeScript
- **Deployment**: Automatic via GitHub Actions
- **Benefits**: 
  - ✅ Publicly accessible worldwide
  - ✅ No firewall restrictions
  - ✅ Free hosting
  - ✅ Automatic SSL/HTTPS

### **Backend: VCL Server**
- **Server**: `152.7.177.154:8000`
- **Technology**: FastAPI + Python
- **Features**: 
  - ✅ Enhanced RAG system with FAISS
  - ✅ SQLite database with 18 vectors
  - ✅ Gemini AI integration
  - ✅ Session management

## **How It Works**

1. **Frontend** (GitHub Pages) makes API calls to **Backend** (VCL Server)
2. **CORS** is configured to allow cross-origin requests
3. **Firewall rules** allow external access to port 8000
4. **GitHub Actions** automatically builds and deploys frontend changes

## **Access URLs**

### **Production Application**
- **Frontend**: https://daksh204singh.github.io/mini-task-botbuilder
- **Backend API**: http://152.7.177.154:8000
- **Health Check**: http://152.7.177.154:8000/health

### **Development**
- **Local Frontend**: http://localhost:3000
- **Local Backend**: http://localhost:8000

## **Deployment Process**

### **Frontend Deployment**
1. Push changes to `feat/rag` branch
2. GitHub Actions automatically:
   - Installs Node.js dependencies
   - Builds the React app
   - Deploys to GitHub Pages

### **Backend Deployment**
1. SSH to VCL server: `ssh dsingh23@152.7.177.154`
2. Restart service: `sudo systemctl restart mini-task-backend`
3. Check status: `sudo systemctl status mini-task-backend`

## **Configuration Files**

### **Frontend Configuration**
- `frontend/package.json`: Added `homepage` field
- `frontend/src/App.tsx`: Updated API base URL
- `.github/workflows/deploy-frontend.yml`: GitHub Actions workflow

### **Backend Configuration**
- `backend/main.py`: Updated CORS origins
- Firewall rules: Allow ports 80, 443, 8000

## **Monitoring & Maintenance**

### **Frontend Monitoring**
- Check GitHub Actions: https://github.com/daksh204singh/mini-task-botbuilder/actions
- View deployment logs in the Actions tab

### **Backend Monitoring**
```bash
# Check backend status
ssh dsingh23@152.7.177.154 "sudo systemctl status mini-task-backend"

# View logs
ssh dsingh23@152.7.177.154 "sudo journalctl -u mini-task-backend -f"

# Test API
curl http://152.7.177.154:8000/health
```

## **Troubleshooting**

### **Frontend Issues**
1. Check GitHub Actions for build errors
2. Verify `homepage` field in `package.json`
3. Test locally: `npm start`

### **Backend Issues**
1. Check service status on VCL server
2. Verify firewall rules: `sudo iptables -L INPUT -n`
3. Test API endpoints locally

### **CORS Issues**
1. Verify CORS origins in `backend/main.py`
2. Check browser console for CORS errors
3. Test with different origins

## **Next Steps**

1. **Enable GitHub Pages** in repository settings
2. **Test the application** at the GitHub Pages URL
3. **Monitor performance** and user experience
4. **Consider custom domain** for production use

## **Benefits of This Setup**

✅ **Public Access**: No firewall restrictions  
✅ **Scalability**: GitHub Pages handles traffic automatically  
✅ **Reliability**: Separate frontend/backend deployment  
✅ **Cost**: Free hosting for both components  
✅ **Security**: HTTPS for frontend, controlled backend access  
✅ **Maintenance**: Easy updates and rollbacks

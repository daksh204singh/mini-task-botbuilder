# 🚀 Development Guide

## **Environment Configuration**

The Mini-task frontend supports multiple development modes to work with different backend configurations.

## **Available Modes**

### **1. Local Development (Default)**
- **Frontend**: `http://localhost:3000`
- **Backend**: `http://localhost:8000`
- **Use Case**: Full local development with local backend

```bash
# Start with local backend
npm run dev
# or
./scripts/dev.sh
```

### **2. Local Frontend + Production Backend**
- **Frontend**: `http://localhost:3000`
- **Backend**: `http://152.7.177.154:8000` (VCL Server)
- **Use Case**: Test frontend changes against production backend

```bash
# Start with production backend
npm run dev:prod
# or
./scripts/prod-local.sh
```

### **3. Production Build**
- **Frontend**: GitHub Pages
- **Backend**: `http://152.7.177.154:8000` (VCL Server)
- **Use Case**: Production deployment

```bash
# Build for production
npm run build:prod
```

## **Environment Variables**

The application automatically detects the environment and uses the appropriate backend URL:

- **Development**: Uses `localhost:8000`
- **GitHub Pages**: Uses `152.7.177.154:8000`
- **Custom**: Set `REACT_APP_USE_PROD_BACKEND=true` to force production backend

## **Configuration Files**

- `src/config.ts` - Main configuration logic
- `.env.development` - Development environment variables
- `.env.production` - Production environment variables

## **Quick Start**

1. **For local development**:
   ```bash
   cd frontend
   npm run dev
   ```

2. **For testing against production backend**:
   ```bash
   cd frontend
   npm run dev:prod
   ```

3. **For production build**:
   ```bash
   cd frontend
   npm run build:prod
   ```

## **Backend Requirements**

### **Local Backend**
- Must be running on `http://localhost:8000`
- Start with: `cd backend && python run.py`

### **Production Backend**
- Running on VCL server: `http://152.7.177.154:8000`
- Status check: `curl http://152.7.177.154:8000/health`

## **Troubleshooting**

### **CORS Issues**
- Ensure backend CORS is configured for your frontend URL
- Check browser console for CORS errors

### **Connection Issues**
- Verify backend is running on the expected port
- Check firewall settings for production backend

### **Environment Detection**
- Check browser console for logged API URL
- Verify `NODE_ENV` and `REACT_APP_USE_PROD_BACKEND` values

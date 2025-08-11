# 🚀 Mini-task Frontend Development Guide

## **Development Modes**

The frontend supports different development modes for testing with local or production backends.

### **Local Development Mode**
```bash
cd frontend
npm run dev
```
- **Frontend**: `http://localhost:3000`
- **Backend**: `http://localhost:8000`
- **Use Case**: Full local development with local backend

### **Production Backend Mode**
```bash
cd frontend
npm run dev:prod
```
- **Frontend**: `http://localhost:3000`
- **Backend**: `http://152.7.177.154:8000` (VCL Server)
- **Use Case**: Test frontend locally with production backend

### **Standard Mode**
```bash
cd frontend
npm start
```
- **Frontend**: `http://localhost:3000`
- **Backend**: `http://localhost:8000` (default)
- **Use Case**: Standard React development

## **Environment Variables**

### **REACT_APP_USE_PROD_BACKEND**
- `false` (default): Use localhost backend
- `true`: Use VCL server backend

## **Configuration**

The API URL is automatically configured based on environment variables in `src/config.ts`:

```typescript
// Check if we're running locally but want to use production backend
if (process.env.REACT_APP_USE_PROD_BACKEND === 'true') {
  return 'http://152.7.177.154:8000';
}

// Default to localhost for development
return 'http://localhost:8000';
```

## **Deployment**

### **VCL Server Deployment**
The backend is deployed on the VCL server at `152.7.177.154:8000` and is accessible for testing.

### **Local Development**
For full local development, run both frontend and backend locally:

```bash
# Terminal 1: Backend
cd backend
python main.py

# Terminal 2: Frontend
cd frontend
npm run dev
```

## **Troubleshooting**

### **Backend Connection Issues**
- Check if backend is running on localhost:8000
- Verify VCL server is accessible at 152.7.177.154:8000
- Check browser console for API URL configuration

### **Environment Issues**
- Clear browser cache if switching between modes
- Restart development server after changing environment variables
- Check browser console for logged API URL

## **API Configuration Debugging**

The application logs configuration details to the browser console:
- Environment variables
- Selected API URL
- Full API endpoint examples

Check the browser console (F12) for debugging information.

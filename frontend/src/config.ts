// Environment-based configuration
const getApiBaseUrl = (): string => {
  console.log('🔍 Config Debug Info:');
  console.log('  - NODE_ENV:', process.env.NODE_ENV);
  console.log('  - REACT_APP_USE_PROD_BACKEND:', process.env.REACT_APP_USE_PROD_BACKEND);
  console.log('  - REACT_APP_BACKEND_URL:', process.env.REACT_APP_BACKEND_URL);

  // If a backend URL is provided (e.g., from GitHub Actions secrets), use it
  if (process.env.REACT_APP_BACKEND_URL) {
    console.log('✅ Using custom backend URL:', process.env.REACT_APP_BACKEND_URL);
    return process.env.REACT_APP_BACKEND_URL;
  }

  // Optionally allow forcing prod backend while running locally
  if (process.env.REACT_APP_USE_PROD_BACKEND === 'true') {
    console.log('✅ Using production backend config (REACT_APP_USE_PROD_BACKEND=true)');
    // You can optionally change this default, but ideally provide REACT_APP_BACKEND_URL
    return 'http://localhost:8000';
  }

  // Default to localhost for development
  console.log('✅ Using development config: http://localhost:8000');
  return 'http://localhost:8000';
};

export const API_BASE_URL = getApiBaseUrl();

// Log the final API URL for debugging
console.log('🚀 Final API Base URL:', API_BASE_URL);
console.log('🌐 Full API URL example:', `${API_BASE_URL}/session`);

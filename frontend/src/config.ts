// Environment-based configuration
const getApiBaseUrl = (): string => {
  console.log('🔍 Config Debug Info:');
  console.log('  - NODE_ENV:', process.env.NODE_ENV);
  console.log('  - Hostname:', window.location.hostname);
  console.log('  - Protocol:', window.location.protocol);
  console.log('  - REACT_APP_USE_PROD_BACKEND:', process.env.REACT_APP_USE_PROD_BACKEND);
  
  // Check if we're in development mode
  if (process.env.NODE_ENV === 'development') {
    console.log('✅ Using development config: http://localhost:8000');
    return 'http://localhost:8000';
  }
  
  // Check if we're running on GitHub Pages (HTTPS)
  if (window.location.hostname === 'daksh204singh.github.io' || window.location.protocol === 'https:') {
    console.log('✅ Using GitHub Pages config with HTTP (will show warning)');
    // For now, use HTTP directly - browser will show a warning but allow it
    // This is a temporary solution until we get a proper domain with SSL
    return 'http://152.7.177.154:8000';
  }
  
  // Check if we're running locally but want to use production backend
  if (process.env.REACT_APP_USE_PROD_BACKEND === 'true') {
    console.log('✅ Using production backend config: http://152.7.177.154:8000');
    return 'http://152.7.177.154:8000';
  }
  
  // Default to localhost for development
  console.log('✅ Using default config: http://localhost:8000');
  return 'http://localhost:8000';
};

export const API_BASE_URL = getApiBaseUrl();

// Log the final API URL for debugging
console.log('🚀 Final API Base URL:', API_BASE_URL);
console.log('🌐 Full API URL example:', `${API_BASE_URL}/session`);

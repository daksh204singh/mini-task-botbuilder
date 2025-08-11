// Environment-based configuration
const getApiBaseUrl = (): string => {
  // Check if we're in development mode
  if (process.env.NODE_ENV === 'development') {
    return 'http://localhost:8000';
  }
  
  // Check if we're running on GitHub Pages
  if (window.location.hostname === 'daksh204singh.github.io') {
    return 'http://152.7.177.154:8000';
  }
  
  // Check if we're running locally but want to use production backend
  if (process.env.REACT_APP_USE_PROD_BACKEND === 'true') {
    return 'http://152.7.177.154:8000';
  }
  
  // Default to localhost for development
  return 'http://localhost:8000';
};

export const API_BASE_URL = getApiBaseUrl();

// Log the API URL for debugging
console.log('Environment:', process.env.NODE_ENV);
console.log('API Base URL:', API_BASE_URL);
console.log('Hostname:', window.location.hostname);

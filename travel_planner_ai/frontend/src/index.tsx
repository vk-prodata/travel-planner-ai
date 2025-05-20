import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';
import { AuthProvider } from './contexts/AuthContext';
import { HelmetProvider } from 'react-helmet-async';
import 'bootstrap/dist/css/bootstrap.min.css';

const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);

console.log('Environment check:', {
  nodeEnv: process.env.NODE_ENV,
  clientId: process.env.REACT_APP_GOOGLE_CLIENT_ID,
});

root.render(
  <React.StrictMode>
    <HelmetProvider>
      <AuthProvider>
        <App />
      </AuthProvider>
    </HelmetProvider>
  </React.StrictMode>
);
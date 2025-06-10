/**
 * Debug utilities for OAuth troubleshooting
 */

import { buildGoogleAuthUrl } from './authHelpers';
import { getBrowserInfo } from './browserDetection';

export const debugOAuthConfiguration = () => {
  const clientId = process.env.REACT_APP_GOOGLE_CLIENT_ID;
  const currentDomain = window.location.origin;
  const browserInfo = getBrowserInfo();
  
  console.log('=== OAuth Debug Information ===');
  console.log('Client ID:', clientId ? `${clientId.substring(0, 20)}...` : 'MISSING');
  console.log('Current Domain:', currentDomain);
  console.log('Expected Redirect URI:', `${currentDomain}/auth/callback`);
  console.log('Browser Info:', browserInfo);
  
  if (clientId) {
    const testUrl = buildGoogleAuthUrl(clientId, window.location.href);
    console.log('Generated OAuth URL:', testUrl);
    
    // Extract and validate parameters
    const url = new URL(testUrl);
    const params = {
      client_id: url.searchParams.get('client_id'),
      redirect_uri: url.searchParams.get('redirect_uri'),
      scope: url.searchParams.get('scope'),
      response_type: url.searchParams.get('response_type'),
      state: url.searchParams.get('state'),
      access_type: url.searchParams.get('access_type'),
      prompt: url.searchParams.get('prompt')
    };
    
    console.log('OAuth Parameters:', params);
    
    // Validation checks
    console.log('=== Validation Checks ===');
    console.log('✓ Client ID present:', !!params.client_id);
    console.log('✓ Redirect URI format:', params.redirect_uri?.includes('/auth/callback'));
    console.log('✓ Required scopes:', params.scope?.includes('email profile openid'));
    console.log('✓ Response type:', params.response_type === 'code');
    
    return {
      isValid: !!(params.client_id && params.redirect_uri?.includes('/auth/callback')),
      params,
      redirectUri: params.redirect_uri,
      domain: currentDomain
    };
  }
  
  return { isValid: false, error: 'Client ID missing' };
};

export const validateGoogleCloudConsoleSetup = () => {
  const currentDomain = window.location.origin;
  const requiredRedirectUri = `${currentDomain}/auth/callback`;
  
  console.log('=== Google Cloud Console Setup Requirements ===');
  console.log('1. Go to: https://console.cloud.google.com/');
  console.log('2. Navigate to: APIs & Services → Credentials');
  console.log('3. Edit your OAuth 2.0 Client ID');
  console.log('4. Add this to "Authorized redirect URIs":');
  console.log(`   ${requiredRedirectUri}`);
  console.log('');
  console.log('Current domain detected:', currentDomain);
  console.log('Required redirect URI:', requiredRedirectUri);
  
  return requiredRedirectUri;
};

export const testOAuthRedirect = () => {
  console.log('=== Testing OAuth Redirect ===');
  
  try {
    const debug = debugOAuthConfiguration();
    if (debug.isValid) {
      console.log('✅ OAuth configuration appears valid');
      console.log('If you still get errors, check Google Cloud Console setup');
      validateGoogleCloudConsoleSetup();
    } else {
      console.log('❌ OAuth configuration has issues:', debug.error);
    }
    return debug;
  } catch (error) {
    console.error('❌ Error testing OAuth configuration:', error);
    return { isValid: false, error: error instanceof Error ? error.message : 'Unknown error' };
  }
}; 
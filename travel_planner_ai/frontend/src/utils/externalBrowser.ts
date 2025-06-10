/**
 * Professional External Browser Utilities
 * Ensures links always open in external browsers when shared through social platforms
 */

export interface ExternalBrowserOptions {
  url?: string;
  fallbackMessage?: string;
  trackingParams?: Record<string, string>;
  forceMethod?: 'window' | 'link' | 'redirect' | 'deeplink';
}

export interface BrowserCapabilities {
  supportsWindowOpen: boolean;
  supportsClipboard: boolean;
  supportsDeepLinks: boolean;
  isEmbedded: boolean;
  platform: string;
}

/**
 * Detect browser capabilities for optimal external opening strategy
 */
export const detectBrowserCapabilities = (): BrowserCapabilities => {
  const userAgent = navigator.userAgent.toLowerCase();
  
  const isEmbedded = userAgent.includes('webview') || 
                    userAgent.includes('wv') ||
                    userAgent.includes('telegram') ||
                    userAgent.includes('whatsapp') ||
                    userAgent.includes('instagram') ||
                    userAgent.includes('facebook') ||
                    userAgent.includes('twitter') ||
                    userAgent.includes('line') ||
                    userAgent.includes('snapchat') ||
                    userAgent.includes('tiktok') ||
                    userAgent.includes('linkedin');
  
  let platform = 'unknown';
  if (userAgent.includes('telegram')) platform = 'telegram';
  else if (userAgent.includes('whatsapp')) platform = 'whatsapp';
  else if (userAgent.includes('instagram')) platform = 'instagram';
  else if (userAgent.includes('facebook')) platform = 'facebook';
  else if (userAgent.includes('twitter')) platform = 'twitter';
  else if (userAgent.includes('line')) platform = 'line';
  else if (!isEmbedded) platform = 'browser';
  
  return {
    supportsWindowOpen: typeof window !== 'undefined' && !!window.open,
    supportsClipboard: typeof navigator !== 'undefined' && !!navigator.clipboard,
    supportsDeepLinks: platform !== 'unknown',
    isEmbedded,
    platform
  };
};

/**
 * Professional external browser opening with multiple fallback methods
 */
export const openInExternalBrowser = async (options: ExternalBrowserOptions = {}): Promise<boolean> => {
  const {
    url = window.location.href,
    fallbackMessage = 'Please open this link in your browser',
    trackingParams = {},
    forceMethod
  } = options;
  
  const capabilities = detectBrowserCapabilities();
  
  // Add tracking parameters
  const urlObj = new URL(url);
  urlObj.searchParams.set('utm_source', 'external_redirect');
  urlObj.searchParams.set('utm_medium', capabilities.platform);
  
  Object.entries(trackingParams).forEach(([key, value]) => {
    urlObj.searchParams.set(key, value);
  });
  
  const finalUrl = urlObj.toString();
  
  console.log('[EXTERNAL_BROWSER] Opening:', {
    url: finalUrl,
    capabilities,
    forceMethod
  });
  
  // Method selection based on force method or capabilities
  const methods = forceMethod ? [forceMethod] : ['window', 'link', 'deeplink', 'redirect'];
  
  for (const method of methods) {
    try {
      const success = await attemptMethod(method, finalUrl, capabilities);
      if (success) {
        console.log(`[EXTERNAL_BROWSER] Success with method: ${method}`);
        return true;
      }
    } catch (error) {
      console.warn(`[EXTERNAL_BROWSER] Method ${method} failed:`, error);
    }
  }
  
  // Ultimate fallback - copy to clipboard
  if (capabilities.supportsClipboard) {
    try {
      await navigator.clipboard.writeText(finalUrl);
      alert(`${fallbackMessage}\n\nLink copied to clipboard: ${finalUrl}`);
      return true;
    } catch (error) {
      console.error('[EXTERNAL_BROWSER] Clipboard fallback failed:', error);
    }
  }
  
  // Final fallback - prompt user
  alert(`${fallbackMessage}\n\nPlease copy this link: ${finalUrl}`);
  return false;
};

/**
 * Attempt specific opening method
 */
const attemptMethod = async (
  method: string, 
  url: string, 
  capabilities: BrowserCapabilities
): Promise<boolean> => {
  switch (method) {
    case 'window':
      return attemptWindowOpen(url);
    
    case 'link':
      return attemptLinkClick(url);
    
    case 'deeplink':
      return attemptDeepLink(url, capabilities.platform);
    
    case 'redirect':
      return attemptRedirect(url);
    
    default:
      return false;
  }
};

/**
 * Method 1: Enhanced window.open with aggressive parameters
 */
const attemptWindowOpen = (url: string): Promise<boolean> => {
  return new Promise((resolve) => {
    try {
      const windowFeatures = [
        'noopener=yes',
        'noreferrer=yes',
        'menubar=yes',
        'toolbar=yes',
        'location=yes',
        'status=yes',
        'scrollbars=yes',
        'resizable=yes',
        'width=800',
        'height=600'
      ].join(',');
      
      const opened = window.open(url, '_blank', windowFeatures);
      
      if (opened && !opened.closed) {
        // Check if window actually opened
        setTimeout(() => {
          if (opened.closed) {
            resolve(false);
          } else {
            resolve(true);
          }
        }, 100);
      } else {
        resolve(false);
      }
    } catch (error) {
      resolve(false);
    }
  });
};

/**
 * Method 2: Create and click invisible link element
 */
const attemptLinkClick = (url: string): Promise<boolean> => {
  return new Promise((resolve) => {
    try {
      const link = document.createElement('a');
      link.href = url;
      link.target = '_blank';
      link.rel = 'noopener noreferrer';
      link.style.display = 'none';
      link.style.position = 'absolute';
      link.style.left = '-9999px';
      
      document.body.appendChild(link);
      
      // Create and dispatch click event
      const clickEvent = new MouseEvent('click', {
        bubbles: true,
        cancelable: true,
        view: window,
        ctrlKey: true // Simulate Ctrl+Click for new tab
      });
      
      link.dispatchEvent(clickEvent);
      
      // Clean up
      setTimeout(() => {
        if (document.body.contains(link)) {
          document.body.removeChild(link);
        }
      }, 100);
      
      resolve(true);
    } catch (error) {
      resolve(false);
    }
  });
};

/**
 * Method 3: Platform-specific deep links
 */
const attemptDeepLink = (url: string, platform: string): Promise<boolean> => {
  return new Promise((resolve) => {
    try {
      const encodedUrl = encodeURIComponent(url);
      let deepLinkUrl: string;
      
      switch (platform) {
        case 'telegram':
          // Telegram doesn't have a reliable deep link for external browsers
          resolve(false);
          return;
        
        case 'whatsapp':
          // WhatsApp deep link to open external browser (limited support)
          deepLinkUrl = `intent://send?text=${encodedUrl}#Intent;scheme=http;package=com.android.chrome;end`;
          break;
        
        default:
          // Try Chrome deep link
          deepLinkUrl = `googlechrome://navigate?url=${encodedUrl}`;
          break;
      }
      
      window.location.href = deepLinkUrl;
      
      // Give it time to process
      setTimeout(() => resolve(true), 500);
      
    } catch (error) {
      resolve(false);
    }
  });
};

/**
 * Method 4: Full page redirect (last resort)
 */
const attemptRedirect = (url: string): Promise<boolean> => {
  return new Promise((resolve) => {
    try {
      // Use location.replace to avoid history entry
      window.location.replace(url);
      resolve(true);
    } catch (error) {
      resolve(false);
    }
  });
};

/**
 * Smart sharing with external browser forcing
 */
export const shareWithExternalBrowser = async (
  platform: 'telegram' | 'whatsapp' | 'facebook' | 'twitter' | 'linkedin',
  options: {
    url?: string;
    title?: string;
    description?: string;
  } = {}
): Promise<boolean> => {
  const {
    url = window.location.href,
    title = document.title,
    description = 'Check out this amazing travel itinerary!'
  } = options;
  
  const shareUrl = encodeURIComponent(url + `?utm_source=share&utm_medium=${platform}`);
  const shareTitle = encodeURIComponent(title);
  const shareDescription = encodeURIComponent(description);
  
  let platformUrl: string;
  
  switch (platform) {
    case 'telegram':
      platformUrl = `https://t.me/share/url?url=${shareUrl}&text=${shareTitle}`;
      break;
    case 'whatsapp':
      platformUrl = `https://wa.me/?text=${shareTitle}%20${shareUrl}`;
      break;
    case 'facebook':
      platformUrl = `https://www.facebook.com/sharer/sharer.php?u=${shareUrl}&quote=${shareDescription}`;
      break;
    case 'twitter':
      platformUrl = `https://twitter.com/intent/tweet?url=${shareUrl}&text=${shareTitle}`;
      break;
    case 'linkedin':
      platformUrl = `https://www.linkedin.com/sharing/share-offsite/?url=${shareUrl}&title=${shareTitle}&summary=${shareDescription}`;
      break;
    default:
      platformUrl = url;
  }
  
  return openInExternalBrowser({
    url: platformUrl,
    trackingParams: {
      share_platform: platform,
      share_timestamp: Date.now().toString()
    }
  });
};

/**
 * Global function integration for HTML script
 */
export const initializeGlobalFunctions = (): void => {
  // Make functions available globally for HTML script integration
  (window as any).__OPEN_EXTERNAL_PROFESSIONAL__ = openInExternalBrowser;
  (window as any).__SMART_SHARE_PROFESSIONAL__ = shareWithExternalBrowser;
  (window as any).__DETECT_BROWSER_CAPABILITIES__ = detectBrowserCapabilities;
  
  console.log('[EXTERNAL_BROWSER] Professional utilities initialized');
};

/**
 * Auto-initialization
 */
if (typeof window !== 'undefined') {
  initializeGlobalFunctions();
} 
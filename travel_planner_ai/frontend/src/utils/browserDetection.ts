/**
 * Browser Detection Utilities
 * Centralized logic for detecting different browser types and capabilities
 */

export interface BrowserInfo {
  isTelegram: boolean;
  isEmbedded: boolean;
  isMobile: boolean;
  userAgent: string;
  supportsPopups: boolean;
  requiresRedirectAuth: boolean;
}

/**
 * Detect if the current browser is Telegram's in-app browser
 */
export const isTelegramBrowser = (): boolean => {
  const userAgent = navigator.userAgent.toLowerCase();
  return userAgent.includes('telegram') || 
         userAgent.includes('telegramwebview') ||
         window.location.href.includes('tgWebAppPlatform');
};

/**
 * Detect if the current browser is an embedded/webview browser
 */
export const isEmbeddedBrowser = (): boolean => {
  const userAgent = navigator.userAgent.toLowerCase();
  return userAgent.includes('webview') || 
         userAgent.includes('wv') ||
         userAgent.includes('telegram') ||
         userAgent.includes('whatsapp') ||
         userAgent.includes('instagram') ||
         userAgent.includes('facebook') ||
         userAgent.includes('twitter') ||
         userAgent.includes('line');
};

/**
 * Detect if the current device is mobile
 */
export const isMobile = (): boolean => {
  return /Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
};

/**
 * Check if the browser supports popup-based authentication
 */
export const supportsPopupAuth = (): boolean => {
  // Embedded browsers typically don't support popups or have restrictions
  return !isEmbeddedBrowser();
};

/**
 * Get comprehensive browser information
 */
export const getBrowserInfo = (): BrowserInfo => {
  const isEmbedded = isEmbeddedBrowser();
  const isTelegram = isTelegramBrowser();
  const mobile = isMobile();
  
  return {
    isTelegram,
    isEmbedded,
    isMobile: mobile,
    userAgent: navigator.userAgent,
    supportsPopups: supportsPopupAuth(),
    requiresRedirectAuth: isEmbedded || isTelegram
  };
};

/**
 * Get user-friendly browser name for display
 */
export const getBrowserDisplayName = (): string => {
  if (isTelegramBrowser()) return 'Telegram';
  if (navigator.userAgent.toLowerCase().includes('whatsapp')) return 'WhatsApp';
  if (navigator.userAgent.toLowerCase().includes('instagram')) return 'Instagram';
  if (navigator.userAgent.toLowerCase().includes('facebook')) return 'Facebook';
  if (navigator.userAgent.toLowerCase().includes('twitter')) return 'Twitter';
  if (isEmbeddedBrowser()) return 'Embedded Browser';
  return 'Browser';
};

/**
 * Log browser detection info for debugging
 */
export const logBrowserInfo = (): void => {
  const info = getBrowserInfo();
  console.log('Browser Detection:', {
    displayName: getBrowserDisplayName(),
    ...info
  });
}; 
import { toast } from 'react-toastify';

// Target email that should receive detailed error information
const DETAILED_ERROR_EMAIL = 'vkusa87@gmail.com';

// Store state for whether detailed logging is enabled
let isDetailedLoggingEnabled = false;

// You can adjust the threshold for showing detailed errors
const REPORTING_THRESHOLD = 500; // Only report 5xx errors by default

/**
 * Notify user of an error with special handling for specific users
 * @param error The error object or message
 * @param user The current user's email or null if not logged in
 */
export const notifyError = (error: unknown, userEmail: string | null | undefined) => {
  // Extract error message
  const errorObj = error instanceof Error ? error : new Error(String(error));
  const errorMessage = errorObj.message || 'An unknown error occurred';
  
  // For console logging
  console.error('Error occurred:', {
    error,
    errorObj,
    stack: errorObj.stack,
    userEmail
  });
  
  // Special handling for specific email or if detailed logging is enabled
  if (userEmail === DETAILED_ERROR_EMAIL || isDetailedLoggingEnabled) {
    const detailedMessage = `
      Error: ${errorMessage}
      ${errorObj.stack ? `\nStack: ${errorObj.stack}` : ''}
      ${errorObj.cause ? `\nCause: ${JSON.stringify(errorObj.cause)}` : ''}
    `;
    
    toast.error(detailedMessage, {
      autoClose: 10000, // Keep error visible longer for detailed logs
      style: {
        maxHeight: '500px',
        overflowY: 'auto',
        whiteSpace: 'pre-wrap',
        width: '500px'
      }
    });
  } else {
    // Standard error for regular users
    toast.error(errorMessage);
  }
};

/**
 * Notify user of a success
 * @param message Success message
 */
export const notifySuccess = (message: string) => {
  toast.success(message);
};

/**
 * Toggle detailed error logging on/off
 * @returns The new state of detailed logging
 */
export const toggleDetailedLogging = (): boolean => {
  isDetailedLoggingEnabled = !isDetailedLoggingEnabled;
  toast.info(`Detailed error logging ${isDetailedLoggingEnabled ? 'enabled' : 'disabled'}`);
  return isDetailedLoggingEnabled;
};

/**
 * Get the current state of detailed logging
 * @returns Whether detailed logging is enabled
 */
export const isDetailedLogging = (): boolean => {
  return isDetailedLoggingEnabled;
};

const errorService = {
  notifyError,
  notifySuccess,
  toggleDetailedLogging,
  isDetailedLogging,
  REPORTING_THRESHOLD
};

// Assign to variable before default export
export default errorService; 
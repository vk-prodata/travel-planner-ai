import React, { useState, useEffect } from 'react';
import { Button, Alert, Badge, Card } from 'react-bootstrap';
import { FaTelegram, FaWhatsapp, FaFacebook, FaTwitter, FaExternalLinkAlt, FaInfoCircle } from 'react-icons/fa';
import { detectBrowserCapabilities, openInExternalBrowser, shareWithExternalBrowser } from '../utils/externalBrowser';
import type { BrowserCapabilities } from '../utils/externalBrowser';

const ExternalBrowserDemo: React.FC = () => {
  const [capabilities, setCapabilities] = useState<BrowserCapabilities | null>(null);
  const [testResults, setTestResults] = useState<string[]>([]);

  useEffect(() => {
    const caps = detectBrowserCapabilities();
    setCapabilities(caps);
  }, []);

  const addTestResult = (message: string) => {
    setTestResults(prev => [...prev.slice(-4), message]); // Keep last 5 results
  };

  const handleTestExternalBrowser = async () => {
    const success = await openInExternalBrowser({
      url: window.location.href,
      fallbackMessage: 'Professional external browser opening test',
      trackingParams: {
        test: 'external_browser_demo',
        timestamp: Date.now().toString()
      }
    });
    
    addTestResult(`External browser test: ${success ? 'SUCCESS' : 'FALLBACK'}`);
  };

  const handleTestShare = async (platform: 'telegram' | 'whatsapp' | 'facebook' | 'twitter') => {
    const success = await shareWithExternalBrowser(platform, {
      url: window.location.href,
      title: 'Travel Planner AI - External Browser Test',
      description: 'Testing professional external browser functionality'
    });
    
    addTestResult(`${platform} share: ${success ? 'SUCCESS' : 'FALLBACK'}`);
  };

  if (!capabilities) {
    return <div>Loading browser detection...</div>;
  }

  return (
    <Card className="mb-4">
      <Card.Header>
        <h5 className="mb-0">
          <FaExternalLinkAlt className="me-2" />
          Professional External Browser Demo
        </h5>
      </Card.Header>
      <Card.Body>
        <Alert variant="info" className="mb-3">
          <FaInfoCircle className="me-2" />
          This demo showcases the professional external browser functionality implemented for optimal link sharing.
        </Alert>

        {/* Browser Detection Results */}
        <div className="mb-4">
          <h6>Browser Detection Results:</h6>
          <div className="d-flex flex-wrap gap-2 mb-2">
            <Badge bg={capabilities.isEmbedded ? 'warning' : 'success'}>
              {capabilities.isEmbedded ? 'Embedded Browser' : 'Standard Browser'}
            </Badge>
            <Badge bg="secondary">Platform: {capabilities.platform}</Badge>
            <Badge bg={capabilities.supportsWindowOpen ? 'success' : 'danger'}>
              Window.open: {capabilities.supportsWindowOpen ? 'Supported' : 'Blocked'}
            </Badge>
            <Badge bg={capabilities.supportsClipboard ? 'success' : 'warning'}>
              Clipboard: {capabilities.supportsClipboard ? 'Available' : 'Limited'}
            </Badge>
          </div>
          <small className="text-muted">
            User Agent: {navigator.userAgent.substring(0, 80)}...
          </small>
        </div>

        {/* Test Buttons */}
        <div className="mb-4">
          <h6>Test External Browser Opening:</h6>
          <div className="d-flex flex-wrap gap-2 mb-3">
            <Button
              variant="primary"
              size="sm"
              onClick={handleTestExternalBrowser}
            >
              <FaExternalLinkAlt className="me-1" />
              Test External Browser
            </Button>
          </div>

          <h6>Test Social Media Sharing:</h6>
          <div className="d-flex flex-wrap gap-2">
            <Button
              variant="info"
              size="sm"
              onClick={() => handleTestShare('telegram')}
            >
              <FaTelegram className="me-1" />
              Test Telegram
            </Button>
            <Button
              variant="success"
              size="sm"
              onClick={() => handleTestShare('whatsapp')}
            >
              <FaWhatsapp className="me-1" />
              Test WhatsApp
            </Button>
            <Button
              variant="primary"
              size="sm"
              onClick={() => handleTestShare('facebook')}
            >
              <FaFacebook className="me-1" />
              Test Facebook
            </Button>
            <Button
              variant="info"
              size="sm"
              onClick={() => handleTestShare('twitter')}
            >
              <FaTwitter className="me-1" />
              Test Twitter
            </Button>
          </div>
        </div>

        {/* Test Results */}
        {testResults.length > 0 && (
          <div>
            <h6>Recent Test Results:</h6>
            <div className="bg-light p-2 rounded">
              {testResults.map((result, index) => (
                <div key={index} className="small text-muted">
                  {new Date().toLocaleTimeString()}: {result}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Implementation Notes */}
        <Alert variant="secondary" className="mt-4 small">
          <strong>Implementation Features:</strong>
          <ul className="mb-0 mt-2">
            <li>Multi-method fallback system (window.open → link click → deep links → clipboard)</li>
            <li>Platform-specific optimizations for Telegram, WhatsApp, etc.</li>
            <li>Enhanced meta tags for better social sharing</li>
            <li>Automatic tracking parameters for analytics</li>
            <li>Graceful degradation for restricted environments</li>
          </ul>
        </Alert>
      </Card.Body>
    </Card>
  );
};

export default ExternalBrowserDemo; 
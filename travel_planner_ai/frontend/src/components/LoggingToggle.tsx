import React, { useState, useEffect } from 'react';
import { Form } from 'react-bootstrap';
import { toggleDetailedLogging, isDetailedLogging } from '../services/errorService';
import { useAuth } from '../contexts/AuthContext';

const LoggingToggle: React.FC = () => {
  const { user } = useAuth();
  const [showToggle, setShowToggle] = useState(false);
  const [isEnabled, setIsEnabled] = useState(isDetailedLogging());

  // Only show the toggle for the specific user or when detailed logging is already enabled
  useEffect(() => {
    if (user?.email === 'vkusa87@gmail.com' || isDetailedLogging()) {
      setShowToggle(true);
    } else {
      setShowToggle(false);
    }
  }, [user]);

  const handleToggle = () => {
    const newState = toggleDetailedLogging();
    setIsEnabled(newState);
  };

  if (!showToggle) {
    return null;
  }

  return (
    <div className="logging-toggle mb-2 mt-2 d-flex align-items-center">
      <Form.Check
        type="switch"
        id="detailed-logging-toggle"
        checked={isEnabled}
        onChange={handleToggle}
        className="me-2"
      />
    </div>
  );
};

export default LoggingToggle; 
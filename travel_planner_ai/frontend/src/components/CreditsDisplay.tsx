import React from 'react';
import { Badge, OverlayTrigger, Tooltip } from 'react-bootstrap';
import { FaCoins } from 'react-icons/fa';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const CreditsDisplay: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  
  if (!user) return null;

  const availableCredits = user.availableCredits ?? 0;
  
  return (
    <OverlayTrigger
      placement="bottom"
      overlay={
        <Tooltip id="credits-tooltip">
          <div className="text-start">
            <div>You have {availableCredits} credit{availableCredits !== 1 ? 's' : ''} available.</div>
            <div className="mt-1">Each day of a trip uses 1 credit.</div>
            <div className="mt-1">Click to manage or purchase more.</div>
          </div>
        </Tooltip>
      }
    >
      <Badge 
        bg="primary"
        text="light"
        className="d-flex align-items-center px-2 py-1 cursor-pointer"
        style={{ cursor: 'pointer' }}
        onClick={() => navigate('/credits')}
      >
        <FaCoins className="me-1" /> {availableCredits}
      </Badge>
    </OverlayTrigger>
  );
};

export default CreditsDisplay; 
import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Button, Spinner } from 'react-bootstrap';
import { FcGoogle } from 'react-icons/fc';

const AuthForm: React.FC = () => {
  const { signIn } = useAuth();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSignIn = async () => {
    try {
      setError(null);
      setIsLoading(true);
      await signIn();
    } catch (error) {
      console.error('Sign-in error:', error);
      setError('Failed to sign in');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="d-inline-block">
      {error && <div className="text-danger small">{error}</div>}
      <Button 
        variant="outline-primary"
        onClick={handleSignIn}
        disabled={isLoading}
        className="rounded-pill d-flex align-items-center"
        size="sm"
        style={{ 
          fontSize: '0.875rem',
          padding: '0.25rem 0.75rem'
        }}
      >
        {isLoading ? (
          <Spinner animation="border" size="sm" />
        ) : (
          <>
            <FcGoogle size={16} className="me-1" />
            <span>Sign in</span>
          </>
        )}
      </Button>
    </div>
  );
};

export default AuthForm; 
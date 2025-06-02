import React, { useState, useEffect } from 'react';
import { Alert } from 'react-bootstrap';
import { FaLightbulb, FaSync, FaCog, FaClock, FaMapMarkerAlt, FaUtensils, FaTheaterMasks, FaWallet, FaLanguage, FaStar, FaGem, FaToggleOn } from 'react-icons/fa';

interface TripLoadingHintsProps {
  className?: string;
}

interface Hint {
  id: number;
  icon: React.ReactNode;
  title: string;
  description: string;
  variant?: 'primary' | 'info' | 'success' | 'warning';
}

const TripLoadingHints: React.FC<TripLoadingHintsProps> = ({ className = "" }) => {
  const hints: Hint[] = [
    {
      id: 1,
      icon: <FaTheaterMasks className="me-2" />,
      title: "Choose Entertainment Activities",
      description: "Always select Entertainment preferences to get the most engaging activities tailored to your interests!",
      variant: 'primary'
    },
    {
      id: 2,
      icon: <FaGem className="me-2" />,
      title: "Discover Hidden Gems",
      description: "Select 'Hidden Gems' preference to find lesser-known, authentic local experiences that most tourists miss!",
    },
    {
      id: 3,
      icon: <FaSync className="me-2" />,
      title: "Refresh Any Activity",
      description: "You can adjust or refresh any specific activity by clicking the refresh button (↻) next to it.",
      variant: 'info'
    },
    {
      id: 4,
      icon: <FaCog className="me-2" />,
      title: "Advanced Settings Available",
      description: "Explore more configurations like Cuisine preferences, Language options, and Advanced settings for a personalized experience.",
      variant: 'success'
    },
    {
      id: 5,
      icon: <FaClock className="me-2" />,
      title: "Processing Time",
      description: "Trip generation can take up to 3 minutes. We're creating the perfect itinerary just for you!",
      variant: 'warning'
    },
    {
      id: 6,
      icon: <FaToggleOn className="me-2" />,
      title: "Add Starting Location",
      description: "Use the 'Add starting location' toggle for route-optimized suggestions along your journey!",
      variant: 'primary'
    },
    {
      id: 7,
      icon: <FaMapMarkerAlt className="me-2" />,
      title: "Add Intermediate Stops",
      description: "For road trips, consider adding intermediate stops to explore more destinations along your route.",
      variant: 'info'
    },
    {
      id: 8,
      icon: <FaUtensils className="me-2" />,
      title: "Cuisine Preferences",
      description: "Set your cuisine preferences to discover local restaurants and must-try dishes at your destination.",
      variant: 'info'
    },
    {
      id: 9,
      icon: <FaWallet className="me-2" />,
      title: "Budget-Friendly Tips",
      description: "Choose 'budget' level to get cost-effective activities and accommodations that still offer great experiences.",
      variant: 'success'
    },
    {
      id: 10,
      icon: <FaLanguage className="me-2" />,
      title: "Language Settings",
      description: "Select your preferred language to get itineraries in your native language with local insights.",
      variant: 'primary'
    },
    {
      id: 11,
      icon: <FaStar className="me-2" />,
      title: "Entertainment Categories",
      description: "Mix different entertainment types (outdoor, cultural, family-friendly) for a well-rounded travel experience.",
      variant: 'info'
    },
    {
      id: 12,
      icon: <FaLightbulb className="me-2" />,
      title: "Pro Tip",
      description: "Save your generated trip to access it later, make modifications, and share it with travel companions!",
      variant: 'warning'
    }
  ];

  const [currentHintIndex, setCurrentHintIndex] = useState(0);
  const [isVisible, setIsVisible] = useState(true);

  useEffect(() => {
    const interval = setInterval(() => {
      setIsVisible(false);
      
      setTimeout(() => {
        setCurrentHintIndex((prevIndex) => (prevIndex + 1) % hints.length);
        setIsVisible(true);
      }, 500); // Half second fade out before changing
      
    }, 20000); // Change every 20 seconds

    return () => clearInterval(interval);
  }, [hints.length]);

  const currentHint = hints[currentHintIndex];

  return (
    <div className={`${className}`}>
      <Alert 
        variant={currentHint.variant} 
        className={`d-flex align-items-start mb-3 transition-opacity ${isVisible ? 'opacity-100' : 'opacity-50'}`}
        style={{ 
          transition: 'opacity 0.5s ease-in-out',
          border: '1px solid rgba(0,0,0,0.1)',
          boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
        }}
      >
        <div className="d-flex align-items-center w-100">
          <div className="fs-5 me-3">
            {currentHint.icon}
          </div>
          <div className="flex-grow-1">
            <div className="fw-bold mb-1">{currentHint.title}</div>
            <div className="mb-0 small">{currentHint.description}</div>
          </div>
        </div>
      </Alert>
      
      {/* Progress indicator showing which hint we're on */}
      <div className="text-center mb-3">
        <small className="text-muted">
          Tip {currentHintIndex + 1} of {hints.length}
        </small>
        <div className="mt-1">
          {hints.map((_, index) => (
            <span
              key={index}
              className={`d-inline-block rounded-circle me-1 ${
                index === currentHintIndex ? 'bg-primary' : 'bg-light border'
              }`}
              style={{ width: '6px', height: '6px' }}
            />
          ))}
        </div>
      </div>
    </div>
  );
};

export default TripLoadingHints; 
import React, { useState, useEffect, useRef } from 'react';
import { Form, InputGroup, Button, Spinner, Alert } from 'react-bootstrap';
import { FaMapMarkerAlt, FaTimes } from 'react-icons/fa';

interface AutocompleteSuggestion {
  place_id: number;
  display_name: string;
  type: string;
  lat?: string;
  lon?: string;
}

interface LocationInputProps {
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  showGeolocation?: boolean;
  showAutocomplete?: boolean;
  required?: boolean;
  className?: string;
}

const LocationInput: React.FC<LocationInputProps> = ({
  label,
  value,
  onChange,
  placeholder = "",
  showGeolocation = false,
  showAutocomplete = true,
  required = false,
  className = ""
}) => {
  const [suggestions, setSuggestions] = useState<AutocompleteSuggestion[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [isLoadingGeo, setIsLoadingGeo] = useState(false);
  const [isLoadingAutocomplete, setIsLoadingAutocomplete] = useState(false);
  const [geoError, setGeoError] = useState<string | null>(null);
  
  const searchTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const inputId = `location-input-${label.toLowerCase().replace(/\s+/g, '-')}`;

  // Handle clicking outside to close suggestions
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        dropdownRef.current && 
        !dropdownRef.current.contains(event.target as Node) &&
        inputRef.current &&
        !inputRef.current.contains(event.target as Node)
      ) {
        setShowSuggestions(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  // Cleanup timeout on unmount
  useEffect(() => {
    return () => {
      if (searchTimeoutRef.current) {
        clearTimeout(searchTimeoutRef.current);
      }
    };
  }, []);

  const handleGeolocation = () => {
    if (!navigator.geolocation) {
      setGeoError('Geolocation is not supported by this browser');
      return;
    }

    setIsLoadingGeo(true);
    setGeoError(null);

    navigator.geolocation.getCurrentPosition(
      async (position) => {
        try {
          const { latitude, longitude } = position.coords;
          
          // Reverse geocode to get readable address
          const response = await fetch(
            `https://nominatim.openstreetmap.org/reverse?format=json&lat=${latitude}&lon=${longitude}&accept-language=en`
          );
          
          if (response.ok) {
            const data = await response.json();
            const address = data.display_name || `${latitude}, ${longitude}`;
            onChange(address);
          } else {
            // Fallback to coordinates if reverse geocoding fails
            onChange(`${latitude}, ${longitude}`);
          }
        } catch (error) {
          console.error('Error reverse geocoding:', error);
          // Fallback to coordinates
          const { latitude, longitude } = position.coords;
          onChange(`${latitude}, ${longitude}`);
        } finally {
          setIsLoadingGeo(false);
        }
      },
      (error) => {
        setIsLoadingGeo(false);
        switch (error.code) {
          case error.PERMISSION_DENIED:
            setGeoError('Location access denied. Please enable location permissions.');
            break;
          case error.POSITION_UNAVAILABLE:
            setGeoError('Location information unavailable.');
            break;
          case error.TIMEOUT:
            setGeoError('Location request timed out.');
            break;
          default:
            setGeoError('An unknown error occurred while retrieving location.');
            break;
        }
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 300000 // 5 minutes
      }
    );
  };

  const searchPlaces = async (query: string) => {
    if (!showAutocomplete || query.length < 2) {
      setSuggestions([]);
      setShowSuggestions(false);
      return;
    }

    setIsLoadingAutocomplete(true);

    try {
      // Using Nominatim API (free, no API key required)
      const response = await fetch(
        `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}&limit=5&accept-language=en&addressdetails=1&extratags=1`
      );

      if (response.ok) {
        const data = await response.json();
        const formattedSuggestions: AutocompleteSuggestion[] = data.map((item: any) => ({
          place_id: item.place_id,
          display_name: item.display_name,
          type: item.type || 'place',
          lat: item.lat,
          lon: item.lon
        }));
        
        setSuggestions(formattedSuggestions);
        setShowSuggestions(formattedSuggestions.length > 0);
      } else {
        setSuggestions([]);
        setShowSuggestions(false);
      }
    } catch (error) {
      console.error('Error fetching suggestions:', error);
      setSuggestions([]);
      setShowSuggestions(false);
    } finally {
      setIsLoadingAutocomplete(false);
    }
  };

  const handleInputChange = (inputValue: string) => {
    onChange(inputValue);
    setGeoError(null); // Clear geolocation errors when user types

    // Clear existing timeout
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
    }

    // Debounce the search
    searchTimeoutRef.current = setTimeout(() => {
      searchPlaces(inputValue);
    }, 300);
  };

  const handleSuggestionSelect = (suggestion: AutocompleteSuggestion) => {
    onChange(suggestion.display_name);
    setShowSuggestions(false);
    setSuggestions([]);
  };

  return (
    <Form.Group className={className}>
      <div className="d-flex align-items-center justify-content-between mb-1">
        <Form.Label htmlFor={inputId} className="text-secondary fw-bold mb-0">{label}</Form.Label>
      </div>
      
      <div style={{ position: 'relative' }}>
        <InputGroup>
          <Form.Control
            ref={inputRef}
            id={inputId}
            type="text"
            value={value}
            onChange={(e) => handleInputChange(e.target.value)}
            placeholder={placeholder}
            required={required}
            className="shadow-sm"
            onFocus={() => {
              if (showAutocomplete && suggestions.length > 0) {
                setShowSuggestions(true);
              }
            }}
          />
          
          {showGeolocation && (
            <Button
              variant="outline-secondary"
              onClick={handleGeolocation}
              disabled={isLoadingGeo}
              title="Use current location"
              className="d-flex align-items-center justify-content-center"
              style={{ width: '45px' }}
            >
              {isLoadingGeo ? (
                <Spinner size="sm" />
              ) : (
                <FaMapMarkerAlt />
              )}
            </Button>
          )}
          
          {showAutocomplete && value && (
            <Button
              variant="outline-secondary"
              onClick={() => {
                onChange('');
                setShowSuggestions(false);
                setSuggestions([]);
                inputRef.current?.focus();
              }}
              title="Clear input"
              className="d-flex align-items-center justify-content-center"
              style={{ width: '35px' }}
            >
              <FaTimes />
            </Button>
          )}
        </InputGroup>

        {/* Autocomplete Dropdown */}
        {showSuggestions && showAutocomplete && (
          <div
            ref={dropdownRef}
            className="position-absolute w-100 bg-white border rounded shadow-lg"
            style={{ 
              top: '100%', 
              zIndex: 1050,
              maxHeight: '200px',
              overflowY: 'auto'
            }}
          >
            {isLoadingAutocomplete && (
              <div className="p-3 text-center">
                <Spinner size="sm" className="me-2" />
                Searching...
              </div>
            )}
            
            {!isLoadingAutocomplete && suggestions.length === 0 && value.length >= 2 && (
              <div className="p-3 text-muted text-center">
                No locations found
              </div>
            )}
            
            {!isLoadingAutocomplete && suggestions.map((suggestion) => (
              <div
                key={suggestion.place_id}
                className="p-2 border-bottom cursor-pointer hover-bg-light"
                onClick={() => handleSuggestionSelect(suggestion)}
                style={{
                  cursor: 'pointer',
                  borderBottom: '1px solid #eee'
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = '#f8f9fa';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = 'white';
                }}
              >
                <div className="fw-semibold">{suggestion.display_name}</div>
                <small className="text-muted text-capitalize">{suggestion.type}</small>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Error Messages */}
      {geoError && (
        <Alert variant="warning" className="mt-2 mb-0 py-2">
          <small>{geoError}</small>
        </Alert>
      )}
    </Form.Group>
  );
};

export default LocationInput; 
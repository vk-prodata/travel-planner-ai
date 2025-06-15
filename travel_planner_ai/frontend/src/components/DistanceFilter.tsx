import React, { useState, useEffect } from 'react';
import { Form, Button, OverlayTrigger, Tooltip } from 'react-bootstrap';
import { FaInfoCircle } from 'react-icons/fa';

interface DistanceFilterProps {
  exclusionRadius: number;
  exclusionUnit: 'miles' | 'km';
  onRadiusChange: (radius: number) => void;
  onUnitChange: (unit: 'miles' | 'km') => void;
}

const DistanceFilter: React.FC<DistanceFilterProps> = ({
  exclusionRadius,
  exclusionUnit,
  onRadiusChange,
  onUnitChange
}) => {
  // Convert between miles and kilometers
  const convertDistance = (value: number, fromUnit: 'miles' | 'km', toUnit: 'miles' | 'km'): number => {
    if (fromUnit === toUnit) return value;
    
    if (fromUnit === 'miles' && toUnit === 'km') {
      return Math.round(value * 1.60934);
    } else if (fromUnit === 'km' && toUnit === 'miles') {
      return Math.round(value / 1.60934);
    }
    return value;
  };

  const [sliderValue, setSliderValue] = useState<number>(exclusionRadius);

  // Get display value in current unit  
  const getDisplayValue = (): number => {
    return sliderValue;
  };

  // Get slider configuration based on unit
  const getSliderConfig = () => {
    if (exclusionUnit === 'miles') {
      return {
        min: 0,
        max: 310, // ~500 km
        step: 5,  // 5 mile steps for finer control
      };
    } else {
      return {
        min: 0,
        max: 500,
        step: 8,  // ~5 mile equivalent steps
      };
    }
  };

  const config = getSliderConfig();

  // Handle slider change
  const handleSliderChange = (value: number) => {
    setSliderValue(value);
    onRadiusChange(value);
  };

  // Handle unit toggle
  const handleUnitToggle = () => {
    const newUnit = exclusionUnit === 'miles' ? 'km' : 'miles';
    
    // Convert current slider value to new unit
    const convertedValue = convertDistance(sliderValue, exclusionUnit, newUnit);
    setSliderValue(convertedValue);
    onRadiusChange(convertedValue);
    onUnitChange(newUnit);
  };

  // Update slider value when props change
  useEffect(() => {
    setSliderValue(exclusionRadius);
  }, [exclusionRadius, exclusionUnit]);

  const tooltipContent = (
    <div className="text-start">
      <strong>Exclusion Radius</strong>
      <div>Skip recommendations within this distance from your starting location.</div>
      <div className="small text-muted mt-1">
        Useful for avoiding activities too close to where you're starting from.
      </div>
    </div>
  );

  return (
    <div data-testid="distance-filter-container" className="mb-3">
      <Form.Label className="d-flex align-items-center">
        Exclusion Radius
        <OverlayTrigger
          placement="top"
          trigger={['hover', 'focus']}
          overlay={<Tooltip id="distance-filter-tooltip">{tooltipContent}</Tooltip>}
        >
          <span data-testid="distance-filter-tooltip" className="ms-2" style={{ cursor: 'pointer' }}>
            <FaInfoCircle className="text-secondary" size={14} />
          </span>
        </OverlayTrigger>
      </Form.Label>
      
      <div className="mb-2">
        <Form.Range
          data-testid="distance-slider"
          aria-label={`Distance exclusion slider in ${exclusionUnit}`}
          min={config.min}
          max={config.max}
          step={config.step}
          value={sliderValue}
          onChange={(e) => handleSliderChange(parseInt(e.target.value))}
          className="mb-2"
        />
        
        <div className="d-flex justify-content-between align-items-center">
          <div className="d-flex align-items-center gap-2">
            <span className="text-muted small">Skip recommendations within:</span>
            <span 
              data-testid="distance-value-display" 
              className="badge bg-primary"
            >
              {getDisplayValue()} {exclusionUnit}
            </span>
          </div>
          
          <Button
            data-testid="distance-unit-toggle"
            aria-label={`Switch to ${exclusionUnit === 'miles' ? 'kilometers' : 'miles'}`}
            variant="outline-secondary"
            size="sm"
            onClick={handleUnitToggle}
          >
            {exclusionUnit === 'miles' ? 'Switch to km' : 'Switch to miles'}
          </Button>
        </div>
      </div>
      
      <div className="small text-muted">
        <strong>Range:</strong> {config.min}-{config.max} {exclusionUnit}
        {exclusionUnit === 'miles' && ' (0-500 km)'}
        {exclusionUnit === 'km' && ' (0-310 miles)'}
      </div>
    </div>
  );
};

export default DistanceFilter; 
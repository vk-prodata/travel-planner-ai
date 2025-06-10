import React, { useState } from 'react';
import { Button, ButtonGroup, Dropdown } from 'react-bootstrap';
import { FaFileDownload, FaShare, FaCopy, FaFileAlt, FaCalendarAlt, FaWhatsapp, FaTelegram, FaFacebook, FaTwitter } from 'react-icons/fa';
import { TripItinerary, TripFormData } from '../types';
import ical from 'ical-generator';
import { toast } from 'react-toastify';
import '../styles/TripExport.css';

interface TripExportProps {
  itinerary: TripItinerary;
  formData: TripFormData;
}

const TripExport: React.FC<TripExportProps> = ({ itinerary, formData }) => {
  const [copySuccess, setCopySuccess] = useState(false);

  const exportTextFile = () => {
    const tripDescription = generateTripDescription();
    const blob = new Blob([tripDescription], { type: 'text/plain' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `trip-to-${formData.destination}.txt`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
    toast.success('Text file exported successfully!');
  };

  const generateICS = () => {
    const calendar = ical();
    const startDate = new Date(formData.startDate);
    const endDate = new Date(formData.endDate);

    calendar.createEvent({
      start: startDate,
      end: endDate,
      summary: `Trip to ${formData.destination}`,
      description: generateTripDescription(),
      location: formData.destination
    });

    const blob = new Blob([calendar.toString()], { type: 'text/calendar' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `trip-to-${formData.destination}.ics`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
    toast.success('Calendar file exported successfully!');
  };

  const exportJSON = () => {
    const data = {
      formData,
      itinerary
    };
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `trip-to-${formData.destination}.json`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
    toast.success('JSON file exported successfully!');
  };

  const copyToClipboard = async () => {
    try {
      const tripDescription = generateTripDescription();
      await navigator.clipboard.writeText(tripDescription);
      setCopySuccess(true);
      toast.success('Trip details copied to clipboard!');
      
      // Reset copy success state after animation
      setTimeout(() => {
        setCopySuccess(false);
      }, 2000);
    } catch (error) {
      toast.error('Failed to copy trip details');
    }
  };

  const generateTripDescription = (): string => {
    let description = `Trip to ${formData.destination}\n`;
    description += `${formData.startDate} - ${formData.endDate}\n\n`;
    
    itinerary.days.forEach((day, index) => {
      description += `Day ${index + 1} - ${day.date}:\n`;
      day.activities.forEach(activity => {
        description += `  ${activity.time} - ${activity.description}\n`;
      });
      description += '\n';
    });
    
    return description;
  };

  const shareUrl = encodeURIComponent(window.location.href);
  const shareTitle = encodeURIComponent(`Check out my trip to ${formData.destination}!`);

  // Create share URLs
  const whatsappUrl = `https://wa.me/?text=${shareTitle}%20${shareUrl}`;
  const telegramUrl = `https://t.me/share/url?url=${shareUrl}&text=${shareTitle}`;
  const facebookUrl = `https://www.facebook.com/sharer/sharer.php?u=${shareUrl}`;
  const twitterUrl = `https://twitter.com/intent/tweet?url=${shareUrl}&text=${shareTitle}`;

  const openShareUrl = async (url: string, platform: string) => {
    try {
      const { openInExternalBrowser } = await import('../utils/externalBrowser');
      const success = await openInExternalBrowser({
        url,
        trackingParams: {
          share_source: 'trip_export',
          share_platform: platform
        }
      });
      if (success) {
        toast.success(`${platform} share opened in external browser!`);
      }
    } catch (error) {
      // Fallback to standard window.open
      window.open(url, '_blank', 'noopener,noreferrer');
      toast.success('Share window opened!');
    }
  };

  return (
    <div className="d-flex gap-2 align-items-center">
      <ButtonGroup>
        <Dropdown>
          <Dropdown.Toggle variant="primary" id="export-dropdown" className="export-button">
            <FaFileDownload className="me-2" />
            Export
          </Dropdown.Toggle>
          <Dropdown.Menu>
            <Dropdown.Item onClick={exportTextFile}>
              <FaFileAlt className="me-2" />
              Export as Text
            </Dropdown.Item>
            <Dropdown.Item onClick={generateICS}>
              <FaCalendarAlt className="me-2" />
              Add to Calendar (ICS)
            </Dropdown.Item>
            <Dropdown.Item onClick={exportJSON}>
              <FaFileDownload className="me-2" />
              Export as JSON
            </Dropdown.Item>
            <Dropdown.Divider />
            <Dropdown.Item onClick={copyToClipboard}>
              <FaCopy className="me-2" />
              {copySuccess ? 'Copied!' : 'Copy to Clipboard'}
            </Dropdown.Item>
          </Dropdown.Menu>
        </Dropdown>

        <Dropdown>
          <Dropdown.Toggle variant="info" id="share-dropdown" className="share-button">
            <FaShare className="me-2" />
            Share
          </Dropdown.Toggle>
          <Dropdown.Menu className="share-dropdown-menu">
            <div className="d-flex gap-2 p-2">
              <Button 
                variant="link" 
                className="p-1 rounded-circle share-icon-button" 
                onClick={() => openShareUrl(whatsappUrl, 'WhatsApp')}
              >
                <FaWhatsapp size={32} className="text-success" />
              </Button>
              
              <Button 
                variant="link" 
                className="p-1 rounded-circle share-icon-button" 
                onClick={() => openShareUrl(telegramUrl, 'Telegram')}
              >
                <FaTelegram size={32} className="text-primary" />
              </Button>
              
              <Button 
                variant="link" 
                className="p-1 rounded-circle share-icon-button" 
                onClick={() => openShareUrl(facebookUrl, 'Facebook')}
              >
                <FaFacebook size={32} className="text-primary" />
              </Button>
              
              <Button 
                variant="link" 
                className="p-1 rounded-circle share-icon-button" 
                onClick={() => openShareUrl(twitterUrl, 'Twitter')}
              >
                <FaTwitter size={32} className="text-info" />
              </Button>
            </div>
          </Dropdown.Menu>
        </Dropdown>
      </ButtonGroup>
    </div>
  );
};

export default TripExport; 
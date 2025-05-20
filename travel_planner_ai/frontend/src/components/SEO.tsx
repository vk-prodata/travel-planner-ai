import React from 'react';
import { Helmet } from 'react-helmet-async';

interface SEOProps {
  title?: string;
  description?: string;
  keywords?: string;
  image?: string;
  url?: string;
  type?: string;
}

const SEO: React.FC<SEOProps> = ({
  title = 'Travel Planner AI - Plan Your Perfect Trip',
  description = 'Your intelligent assistant for planning perfect trips. Create personalized itineraries, discover attractions, and organize your travel with ease.',
  keywords = 'travel planner, trip planning, travel itinerary, AI travel assistant, vacation planner',
  image = '/logo512.png',
  url = 'https://travelplannerai.org',
  type = 'website',
}) => {
  const siteUrl = process.env.REACT_APP_SITE_URL || 'https://travelplannerai.org';
  const fullUrl = url.startsWith('http') ? url : `${siteUrl}${url}`;
  const fullImage = image.startsWith('http') ? image : `${siteUrl}${image}`;
  
  return (
    <Helmet>
      {/* Basic Meta Tags */}
      <title>{title}</title>
      <meta name="description" content={description} />
      <meta name="keywords" content={keywords} />
      
      {/* OpenGraph Meta Tags */}
      <meta property="og:title" content={title} />
      <meta property="og:description" content={description} />
      <meta property="og:image" content={fullImage} />
      <meta property="og:url" content={fullUrl} />
      <meta property="og:type" content={type} />
      
      {/* Twitter Meta Tags */}
      <meta name="twitter:card" content="summary_large_image" />
      <meta name="twitter:title" content={title} />
      <meta name="twitter:description" content={description} />
      <meta name="twitter:image" content={fullImage} />
      
      {/* Canonical Link */}
      <link rel="canonical" href={fullUrl} />
    </Helmet>
  );
};

export default SEO; 
# Project Memory

## Progress Updates

### Hidden Gems Entertainment Feature Implementation - [Current Date]

- **Feature Added**: Implemented "Hidden Gems" as a new entertainment preference option
- **Frontend Implementation**:
  - **Type Safety**: Added `'hidden-gems'` to `EntertainmentPreference` type in both `types/index.ts` and `types.ts`
  - **UI Enhancement**: Added "Hidden Gems" button to entertainment preferences with special styling:
    - Sparkle emoji badge (✨) as visual indicator
    - Position-relative styling for badge placement
    - Informational tooltip explaining the feature when selected
  - **User Experience**: When selected, shows explanatory message about discovering "lesser-known, highly-rated places and unique experiences"
  - **Loading Hints**: Added new tip about Hidden Gems feature in `TripLoadingHints.tsx` component
- **Backend Implementation**:
  - **AI Prompt Enhancement**: Modified `_generate_prompt()` in `ai_client.py` to handle hidden-gems preference
  - **Specialized Instructions**: When hidden-gems is selected, adds specific prompt instructions:
    - Focus on lesser-known, authentic local experiences
    - Avoid major tourist attractions and mainstream venues
    - Prioritize local favorites with excellent ratings but low tourist traffic
    - Include off-the-beaten-path locations and family-run businesses
    - Seek unique experiences showcasing authentic local culture
    - Balance accessibility with authenticity
  - **Retry Logic**: Updated retry prompts to also handle hidden gems preferences
  - **Activity Refresh**: Enhanced activity refresh functionality to recognize hidden gems custom preferences
- **Testing Implementation**:
  - **Frontend Tests**: Created comprehensive test suite `HiddenGems.test.tsx`:
    - UI appearance and styling tests
    - Preference selection/deselection behavior
    - Combination with other preferences
    - Message display functionality
    - Type safety validation
  - **Backend Tests**: Created `test_hidden_gems.py`:
    - AI prompt generation with hidden gems preferences  
    - Integration with other entertainment preferences
    - Retry scenario handling
    - Activity refresh functionality testing
    - Type validation and edge cases
- **Technical Features**:
  - **Smart Prompting**: Separates hidden-gems from other preferences for specialized handling
  - **Backwards Compatibility**: Feature is optional and doesn't affect existing functionality
  - **Quality Assurance**: Maintains all existing quality standards while adding unique discovery elements
- **User Benefits**:
  - Discover authentic local experiences away from tourist crowds
  - Find highly-rated but lesser-known establishments
  - Access unique cultural experiences and local favorites
  - Explore off-the-beaten-path locations safely and accessibly
- **Result**: Users can now select "Hidden Gems" to receive recommendations for authentic, lesser-known local experiences

### Language Filter Fix - Russian Language Support - [Current Date]

- **Issue Identified**: Russian language selection was returning English results instead of Russian
- **Root Cause**: AI prompts completely lacked language instructions - the language parameter was captured but never told to the AI
- **Frontend Validation**: ✅ TripForm properly sends `"ru"` for Russian language selection
- **Backend Validation**: ✅ AI client captures language parameter in `args.get('language')`
- **Core Problem**: ❌ `_generate_prompt()` and `_generate_aggressive_retry_prompt()` had no language instructions
- **Solution Implemented**:
  - **Added Language Instructions**: Created comprehensive language instruction mapping for all supported languages
  - **Russian Support**: `'ru': 'ОТВЕЧАЙТЕ НА РУССКОМ ЯЗЫКЕ (Russian) - Все описания деятельности, местоположения и объяснения должны быть на русском языке'`
  - **Multi-Language Support**: Added instructions for Spanish, French, German, Italian, Chinese, and English
  - **Prompt Integration**: Added `🌍 LANGUAGE REQUIREMENT: {language_instruction}` to main prompt
  - **Retry Prompt Fix**: Added `🌍 LANGUAGE: {language_instruction}` to retry prompts as well
  - **Cache Management**: Added `clear_cache_for_language()` method to clear cached English responses for non-English requests
  - **Automatic Cache Clearing**: Non-English language requests now automatically clear cache to ensure fresh generation
- **Technical Changes**:
  - Modified `_generate_prompt()` to include language instruction mapping and prominent language requirement
  - Updated `_generate_aggressive_retry_prompt()` with language instructions for retry attempts
  - Added `clear_cache_for_language()` method to force regeneration for non-English languages
  - Integrated automatic cache clearing in `generate_itinerary()` for non-English requests
- **Language Support Status**:
  - English (en): ✅ RESPOND IN ENGLISH
  - Spanish (es): ✅ RESPONDE EN ESPAÑOL  
  - French (fr): ✅ RÉPONDEZ EN FRANÇAIS
  - German (de): ✅ ANTWORTEN SIE AUF DEUTSCH
  - Italian (it): ✅ RISPONDI IN ITALIANO
  - Russian (ru): ✅ ОТВЕЧАЙТЕ НА РУССКОМ ЯЗЫКЕ with detailed Russian instruction
  - Chinese (zh): ✅ 用中文回答
- **Expected Result**: All language filters should now work correctly, with Russian language requests returning full Russian itineraries

### Trip Loading Hints & Tips Implementation - [Current Date]

- **Feature**: Implemented rotating hints and tips during trip generation to improve user experience
- **Component Created**: `TripLoadingHints.tsx` - A new React component that displays helpful tips
- **Implementation Details**:
  - **10 Different Hints**: Created comprehensive set of tips covering all aspects of trip planning
  - **20-Second Rotation**: Hints automatically change every 20 seconds with smooth fade transitions
  - **Visual Design**: Uses Bootstrap Alert components with different variants (primary, info, success, warning)
  - **Progress Indicator**: Shows which tip is currently displayed (e.g., "Tip 3 of 10") with dot indicators
  - **Smooth Animations**: Fade-in/fade-out transitions between hints for better UX
- **Hints Content**:
  1. Entertainment Activities - Emphasizes selecting entertainment preferences
  2. Activity Refresh - How to refresh/adjust specific activities
  3. Advanced Settings - Cuisine, language, and configuration options
  4. Processing Time - Sets expectations (up to 3 minutes)
  5. Intermediate Stops - Road trip optimization tips
  6. Cuisine Preferences - Local restaurant discovery
  7. Budget Tips - Cost-effective options
  8. Language Settings - Native language itineraries
  9. Entertainment Mix - Combining different activity types
  10. Pro Tip - Saving and sharing trips
- **Integration**: 
  - Added to `App.tsx` loading section replacing simple "Generating your perfect trip..." message
  - Enhanced loading UI with larger spinner and improved styling
  - Maintains loading functionality while providing educational value
- **Technical Features**:
  - TypeScript interfaces for type safety
  - React hooks (useState, useEffect) for state management
  - Responsive design with Bootstrap classes
  - Icon integration using react-icons/fa
  - Clean component architecture for reusability
- **User Benefits**:
  - Reduces perceived waiting time during trip generation
  - Educates users on app features and best practices
  - Provides actionable tips for better trip planning
  - Improves overall user engagement during loading

### Incomplete Itinerary Generation Fix - [Current Date]

- Fixed critical issue where AI was returning incomplete itineraries (e.g., 3 days instead of 7+ requested days)
- **Root Cause**: Token limits were too low for longer trips, causing AI responses to be truncated
- **Solutions Implemented**:
  - **Increased token limits**: gpt-4o-2024-11-20 from 8,000 to 16,000 tokens, DeepSeek models from 6,000 to 8,000 tokens
  - **Enhanced prompt instructions**: Added explicit warnings and requirements for completing ALL days
  - **Added response validation**: System now detects when fewer days are returned than expected
  - **Implemented retry mechanism**: Up to 3 attempts with better prompts if incomplete responses detected
  - **Improved caching**: Cached results are validated for completeness before being returned
  - **Enhanced logging**: Detailed logs for tracking incomplete responses and retry attempts
- **Technical Changes**:
  - Modified `_generate_prompt()` to be more explicit about completing all days and include date lists
  - Added `_calculate_expected_days()` helper method for date range validation
  - Updated `_process_response()` to validate completeness and log missing days
  - Enhanced `generate_itinerary()` with retry logic and attempt tracking
  - Updated system message to emphasize completing entire itinerary
- **Testing**: Created comprehensive test suite (`test_incomplete_itinerary_fix.py`) to verify fixes
- **Result**: Should now consistently generate complete itineraries for longer trips

### Aggressive Incomplete Itinerary Fix - [Current Date]

- **Issue Persisted**: Despite previous fixes, AI was still consistently returning only 3 days out of 8 requested days
- **Additional Aggressive Fixes Implemented**:
  - **Completely redesigned prompt structure**: More concise, emoji-heavy format with stronger emphasis on completion
  - **Progressive retry strategy**: Each retry attempt uses increasingly aggressive prompts and different parameters
  - **Enhanced system messages**: Much stronger warnings about completion requirements
  - **Dynamic API parameters**: Retry attempts use modified temperature and token limits to force different behavior
  - **Comprehensive logging**: Added detailed tracking of response length, token usage, and block counts
  - **Ultra-compact retry prompts**: Simplified format for retry attempts to maximize space efficiency
- **New Technical Features**:
  - Added `_generate_aggressive_retry_prompt()` method for focused retry prompts
  - Modified API call parameters per retry attempt (temperature: 0.3→0.5→0.7, max_tokens reduced for retries)
  - Enhanced response logging to track exactly why responses are incomplete
  - Stronger validation and error reporting for incomplete responses
- **Strategy**: If standard detailed prompts fail, progressive retries use minimal descriptions but ensure all days are covered
- **Goal**: Guarantee complete itineraries even if activity details must be sacrificed for completeness

### Balanced Quality + Completeness Fix - [Current Date]

- **Issue**: Previous aggressive fix solved completeness but sacrificed too much quality - trips were "shitty"
- **Solution**: Balanced approach that maintains both completion guarantees AND quality standards
- **Balanced Improvements**:
  - **Maintained strong completion emphasis**: Clear warnings about requiring all days
  - **Restored detailed quality rules**: 10 quality rules + excellence standards covering all aspects
  - **Better retry strategy**: Retries maintain quality focus while streamlining format
  - **Balanced API parameters**: Less aggressive temperature changes (0.3→0.4→0.5 vs 0.3→0.5→0.7)
  - **Preserved all original requirements**: Budget compliance, family-friendly, ratings, preferences matching
- **Key Features Restored**:
  - Detailed "Why" explanations for each activity
  - Specific restaurant recommendations (2-3 options)
  - Tour company suggestions with reasoning
  - Historical context and ratings information
  - Budget level compliance throughout
  - Entertainment preference matching
  - Family-friendly considerations
  - Travel logistics and timing optimization
- **Completion Safeguards**:
  - Still uses 3-attempt retry with progressive urgency
  - Maintains date validation and logging
  - Clear instruction: "reduce descriptions but NEVER skip days"
  - Explicit date listing in prompts
- **Result**: Should now generate complete, high-quality itineraries that satisfy all user requirements

### Detailed Elaboration Restoration - [Current Date]

- **Issue**: Balanced fix still produced trips that were "not so good" and "not elaborative"
- **Root Cause**: Had removed the original detailed prompt instructions that generated rich, comprehensive itineraries
- **Solution**: Restored original detailed prompt structure while maintaining completion safeguards
- **Elaboration Improvements**:
  - **Restored comprehensive instructions**: Full original detailed prompt structure with 16 quality rules
  - **Enhanced description requirements**: "Detailed activity description with comprehensive information, context, and specific recommendations"
  - **Comprehensive "Why" sections**: Must explain preference matching, cultural significance, historical context, and practical value
  - **Rich detail standards**: 2-4 sentences per description with sensory details and vivid imagery
  - **Practical information**: Opening hours, booking recommendations, insider knowledge, difficulty levels
  - **Cultural context**: Historical significance, architectural details, cultural importance
  - **Specific recommendations**: Restaurant names, tour operators, accommodation options with reasoning
- **Elaboration Standards Added**:
  - Include specific names of restaurants, hotels, tour operators, and attractions
  - Mention historical significance, architectural details, or cultural importance
  - Provide practical information like duration, difficulty levels, age appropriateness
  - Suggest what to bring, what to expect, and how to make the most of each experience
  - Include sensory details that help travelers visualize and anticipate their experience
- **Enhanced Retry Prompts**: Also maintain detailed, elaborate standards in retry attempts
- **Completion + Quality**: Strong completion safeguards with restored rich content requirements
- **Result**: Should now generate complete, detailed, elaborate itineraries with comprehensive information and rich context

### Streamlined Completion-First Approach - [Current Date]

- **Persistent Issue**: Despite all previous fixes, AI still consistently returns only 3 days instead of 10 requested days
- **Root Cause Analysis**: Overly verbose prompts consuming too many input tokens, leaving insufficient output tokens for completion
- **Solution**: Streamlined approach prioritizing completion over excessive detail
- **Streamlined Improvements**:
  - **Drastically reduced prompt length**: From ~2500+ chars to <1500 chars while maintaining essential quality
  - **Efficient date listing**: Inline format instead of bullet points to save tokens
  - **Compact trip details**: Single-line format for traveler info, preferences, budget
  - **Streamlined rules**: 8 essential rules vs 16+ detailed rules
  - **Focused format instructions**: Clear but concise activity format requirements
  - **Aggressive retry strategy**: 10K tokens max for retries to force completion
- **Token Optimization**:
  - **Reduced base max_tokens**: 16K → 14K to leave more room for output
  - **Aggressive retry limits**: 14K → 10K tokens for retry attempts
  - **Simplified retry prompts**: Ultra-focused on completion over elaboration
- **Completion-First System Messages**:
  - Primary focus: "Complete ALL requested days. NEVER stop early."
  - Clear success criteria: "SUCCESS = ALL days completed. FAILURE = Missing any day."
  - Retry escalation: "Focus on coverage over excessive detail"
- **Quality Balance**:
  - Maintained essential quality requirements: specific recommendations, budget compliance, family considerations
  - Preserved preference matching and practical tips
  - Simplified descriptions: "Quality activity matching preferences" vs verbose requirements
- **Strategy**: Sacrifice verbose descriptions for guaranteed completion, then let quality emerge within constraints
- **Expected Result**: Complete coverage of all requested days with good quality within space limits

### Credit System Improvements - [Current Date]

- Updated credit system to use day-based deduction (1 credit per day in the trip)
- Increased free credits for new users from 1 to 10 credits
- Updated credit packages: Basic package now gives 30 credits (was 10), Premium package gives 300 credits (was 100)
- Maintained same pricing: Basic $4.99, Premium $39.99
- Added deduct_credits_for_trip function to calculate credits based on trip duration
- Fixed double credit deduction issue when saving a trip with an existing itinerary
- Added logic to check if a trip already has an itinerary before deducting credits
- Updated both routes.py and routers/trips.py to use consistent credit deduction
- Implemented proper logging for credit deduction operations
- Added error handling for credit deduction failures

### Trip List Page Implementation - [Date]

- Created a new TripList page component that displays all trips for a user
- Implemented functionality to view trip details by redirecting to the main page
- Added delete trip functionality with confirmation
- Created styling for the trip cards with hover effects and icons
- Added tests for the TripList component
- Updated App.tsx to include React Router for navigation between pages
- Added a "My Trips" button in the header for easy navigation
- Implemented loading states, empty states, and error handling
- Added date-fns package for date formatting

### Café & Restaurant Preferences Implementation - [Current Date]

- Added cuisine type selection in the trip form's advanced settings
- Implemented CuisineType enum with various cuisine options
- Updated TripFormData interface to include cuisinePreference
- Added comprehensive tests for the new feature
- Cuisine preferences will be used to tailor restaurant recommendations in the itinerary

### Credits System Implementation - [Current Date]

- Updated User interface to include availableCredits and totalCreditsPurchased properties
- Created a CreditsDisplay component that shows credits in the navigation with a tooltip
- Implemented a Credits Management Page for users to view and purchase credits
- Added credit packages with different pricing options (10 credits for $4.99, 100 credits for $39.99)
- Created creditsService with functions to fetch user credits and handle purchases
- Updated AuthContext to fetch and store user credits upon login
- Added a route for the Credits page in App.tsx
- Updated navigation in TripList and MainApp to include the CreditsDisplay
- Added CSS styling for the credits components

### Credits System Bug Fixes - [Current Date]

- Fixed issue with new users not receiving their free credit
- Updated backend to create user records when credits are requested directly
- Modified both frontend and backend to handle different naming conventions for credit properties
- Fixed credits purchase functionality to work without requiring Stripe integration
- Added detailed logging to track user creation and credit assignment
- Changed basic package price from $5.00 to $4.99
- Added Stripe test configuration with test credit card numbers
- Implemented fallback mechanisms for API errors

### MongoDB Integration Fixes - [Current Date]
- Fixed critical backend issues with MongoDB operations failing with "NoneType" errors
- Corrected async/await patterns in database access functions
- Modified get_user_collection to be non-async for proper operation
- Rewritten credits endpoints to directly use MongoDB operations without intermediate services
- Improved error handling with specific status codes and detailed error messages
- Added robust user creation flow when users don't exist in the database
- Ensured new users receive 1 free credit upon first access
- Standardized response format for both snake_case and camelCase field names

### MongoDB Synchronization Fix - [Current Date]
- Fixed "NoneType can't be used in await expression" errors in backend
- Converted all MongoDB operations to use synchronous calls (removed await keywords)
- Made all service functions consistent with the synchronous MongoDB approach
- Updated all services and routers to use the same synchronous pattern
- Fixed auth flow to properly create users with 1 free credit
- Made credit purchase and user management fully consistent
- Added proper error handling and logging in all MongoDB operations
- Implemented complete fix for MongoDB synchronization issues

### User Data Synchronization - [Current Date]
- Enhanced user creation flow to update temporary user data with Google Auth information
- Modified `create_user_if_not_exists` to check for and update temporary email/name values
- Added new API endpoint `/credits/update-user` to manually synchronize user data
- Created utility script `update_user.py` for command-line user data updates
- Fixed issue where users created via credits API had temporary placeholder values
- Ensured consistent user record data between direct API access and Google Auth flow
- Added proper error handling and detailed logging for user data operations
- Preserved existing credits when updating user information

### Trip Configuration Enhancement - [Current Date]

- Implemented storing trip configuration with trip activities
- Added trip_config field to TripItinerary models in both backend and frontend
- Modified the activity refresh endpoint to use trip configuration for more consistent suggestions
- Updated App.tsx to save and use trip configuration in refreshActivity function
- Improved activity suggestions by using original destination, preferences, and budget level
- Ensured trip configuration is preserved when saving trips
- Added integration tests for the refresh activity endpoint with trip configuration
- Made sure newly generated itineraries include trip configuration
- Fixed type issues to ensure proper type safety in the implementation

### OpenAI Model Configuration Fix - [Current Date]

- Fixed critical error with the OpenAI model configuration
- Updated the default model from 'gpt-4-turbo-8k' (which doesn't exist) to 'gpt-4-turbo-preview'
- Adjusted max_tokens parameter from 8000 to 4096 to comply with model limits
- Added backward compatibility handling for legacy model name references
- Improved error handling for model configuration mismatches
- Enhanced logging for model selection issues
- Added automatic model name correction to prevent API errors
- Updated get_model_config function to handle invalid model requests gracefully

### Price Level Display Fix - [Current Date]

- Fixed issue with price level indicators not displaying in the UI
- Simplified naming convention by standardizing on the 'price' field
- Updated frontend interfaces to use 'price' instead of 'priceLevel'
- Modified AI client and endpoints to only use the 'price' field
- Removed redundant 'priceLevel' field to simplify the codebase
- Ensured consistent display of price indicators (Free, $, $$, $$$) across the application

### Custom Activity Preferences Implementation - [Current Date]

- Added custom activity preferences feature for activity refresh
- Implemented input field that appears when user clicks "Refresh Activity" button
- Added functionality to submit custom preferences to the backend
- Updated backend to incorporate user preferences into AI prompt
- Added styles for the custom preferences container
- Improved UX with clear submit/cancel buttons
- Ensured the input field collapses after submission or cancellation
- Updated RefreshActivityRequest model to include custom_preferences field
- Enhanced the refresh activity flow to consider user's specific preferences
- Added responsive styling for mobile devices

### SEO Domain Update - [Current Date]

- Updated all SEO-related files to use the correct domain: https://travelplannerai.org/
- Modified robots.txt to point to the correct sitemap URL
- Updated sitemap.xml with the proper domain for all routes
- Enhanced index.html meta tags with the actual domain (og:url, canonical)
- Updated the SEO component to use travelplannerai.org as the default domain
- Improved search engine discoverability by using the actual production domain
- Note: REACT_APP_SITE_URL environment variable should be updated in deployment

### SEO Optimization - [Current Date]

- Enhanced SEO across the entire application to improve search engine visibility and ranking
- Created a robots.txt file with specific crawling directives and sitemap reference
- Generated a sitemap.xml with all main routes and content pages
- Improved the HTML meta tags in index.html with comprehensive description, keywords, and social media tags
- Implemented dynamic page titles, descriptions, and meta tags using React Helmet Async
- Created a reusable SEO component for consistent metadata across all pages
- Added OpenGraph and Twitter Card meta tags for better social media sharing
- Added canonical URLs to prevent duplicate content issues
- Implemented dynamic SEO data based on current page and trip information
- Applied SEO component to all major pages: Home, Trips, Credits, and FAQ

### Next Steps
- Consider adding sorting options for trips (by date, destination, etc.)
- Add filtering capabilities 
- Implement pagination for users with many trips
- Add trip search functionality 
- Consider adding more specific cuisine types based on user feedback
- Implement backend logic to incorporate cuisine preferences into AI-generated itineraries
- Add cuisine filters to the trip list view 
- Implement credit deduction when generating new trips
- Add transaction history for credit purchases
- Create admin interface for managing credit packages
- Integrate Stripe for production payments 

### Database Schema Optimization - [Current Date]
- Simplified database schema by using Google ID as MongoDB's primary key (_id)
- Eliminated redundant ID fields to improve database efficiency 
- Updated all user-related database operations to use _id consistently
- Modified User model to properly support aliasing between _id and id
- Adjusted user service layer for compatibility with the new schema
- Updated all references in credits router to use the new schema
- Modified utility scripts to work with the optimized schema
- Ensured backward compatibility with existing code

### User Authentication Improvements - [Current Date]
- Added automatic detection and correction of temporary user data
- Enhanced Google Auth flow to properly update user records with real data
- Fixed issue where users created by direct API access had placeholder emails
- Modified auth module to update temporary data during authentication
- Added fallback mechanism for users who can't authenticate via Google
- Created utility endpoints and scripts for manual user data updates
- Added comprehensive logging to track user data updates
- Ensured proper merging of user data while preserving credits information 

### Geographic Context Loss & Token Tracking Fix - [Current Date]

- **Issue Identified**: AI was generating activities in wrong geographic locations (e.g., suggesting Seattle locations for Canada trips)
- **Root Cause**: Prompt optimization removed too much geographical context, causing AI to confuse similar place names
- **Geographic Context Solutions**:
  - **Enhanced geographic enforcement**: Added country/region detection from destination strings
  - **Explicit geographic warnings**: Added clear warnings like "🍁 CANADA REGION: ALL activities must be in Canada (British Columbia). DO NOT suggest places in USA/Seattle."
  - **Regional constraints**: Added support for major countries (Canada, USA, France, Italy, Spain, Germany)
  - **Fallback region detection**: Extracts region from destination string parts for unknown countries
  - **Retry prompt enforcement**: Added geographic constraints to retry prompts as well
  - **Rule addition**: Added "Geography: ALL locations must be in the correct destination region" to prompt rules
- **Token Usage Tracking Enhancements**:
  - **Enhanced logging**: Token usage now logged with clear 🪙 emoji and detailed breakdown
  - **Response data inclusion**: Token usage now added to returned itinerary data for client access
  - **Attempt tracking**: Logs token waste on incomplete responses and success costs
  - **Detailed breakdown**: Shows prompt_tokens + completion_tokens = total_tokens
  - **Cache management**: Added method to clear cache for specific destination patterns to force regeneration
- **Technical Changes**:
  - Modified `_generate_prompt()` to include geographic context detection and enforcement
  - Enhanced `_generate_aggressive_retry_prompt()` with geographic warnings
  - Improved token logging in `generate_itinerary()` with structured data and attempt tracking
  - Added `clear_cache_for_destination()` method for targeted cache clearing
  - Added token_usage object to response data for client access
- **Expected Results**:
  - AI should now stay within correct geographic regions (Canada vs USA, etc.)
  - Complete token usage tracking for cost analysis and optimization
  - Better debugging of geographic and completion issues

### Google Maps Coordinate Fix - [Current Date]

- **Issue Identified**: Google Maps links were pointing to wrong locations (e.g., Tantalus Lookout showing Hawaii instead of Vancouver)
- **Root Cause**: `getGoogleMapsUrl` function was treating coordinate objects as strings, causing `[object Object]` in URLs
- **Solution**: 
  - Updated `getGoogleMapsUrl` in `Itinerary.tsx` to handle coordinate objects: `{latitude: X, longitude: Y}`
  - Prioritized precise coordinates over location name search for accuracy
  - Updated TypeScript types to properly reflect coordinate structure
  - Maintained backward compatibility for string coordinate format
- **Technical Changes**:
  - Modified coordinate handling: `lat,lon` format now used directly in Google Maps URLs
  - Fixed type definitions: `coordinates?: {latitude: number, longitude: number} | string`
  - Cache cleared to force fresh coordinate generation

### Coordinate Generation & Elaboration Restoration - [Current Date]

- **Issue Identified**: Recent trips were missing both coordinate data and elaborate descriptions
  - Google Maps "View on Map" links were completely missing (no coordinates generated)
  - Activities had basic descriptions like "Lunch at Black Bear Diner" without rich detail
- **Root Cause**: Streamlined prompt optimization removed both coordinate requirements and detailed description standards
- **Solution**: Enhanced prompt with dual focus on completion AND quality
- **Technical Fixes**:
  - **Restored Coordinate Requirements**: Added explicit coordinate generation: `"coordinates": {"latitude": X.XXXX, "longitude": -X.XXXX}`
  - **Enhanced Description Standards**: Restored 2-3 sentence rich descriptions with cultural context, practical tips, and specific recommendations
  - **Quality Rules Integration**: 8 comprehensive quality rules including coordinate requirements, cultural context, and practical information
  - **Maintained Completion Safeguards**: Kept strong completion requirements while restoring quality standards
  - **Updated Retry Prompts**: Retry attempts also generate coordinates and maintain quality descriptions
- **Expected Results**:
  - Google Maps links should work again with precise coordinates
  - Activities should have rich, elaborate descriptions with cultural context
  - Complete itineraries with both quality AND completion
- **Cache Cleared**: Forced fresh generation with enhanced coordinate and elaboration requirements

### Coordinate Accuracy Enhancement - [Current Date]

- **Issue Identified**: AI was generating inaccurate coordinates for specific landmarks
  - Example: Sundial Bridge coordinates `40.5865, -122.3772` were ~600m off from actual location `40.5918, -122.3775`
  - Google Maps links pointed to wrong locations despite having coordinate data
- **Root Cause**: AI was using approximate city coordinates instead of precise landmark coordinates
- **Solution**: Enhanced coordinate accuracy requirements and validation
- **Technical Fixes**:
  - **Enhanced Prompt Requirements**: Added explicit instruction "Use exact coordinates for landmarks, attractions, and specific businesses - NOT approximate city coordinates"
  - **Coordinate Validation**: Added `_validate_coordinate_region()` method to check if coordinates are reasonable for destination region
  - **Regional Bounds**: Implemented validation for major regions (USA, Canada, Europe) and specific cities (Redding, Portland, Campbell, Vancouver)
  - **Warning System**: Logs warnings when coordinates seem inconsistent with destination region
  - **Retry Prompt Enhancement**: Updated retry prompts to emphasize "precise coordinates for every location (not approximate city coordinates)"
- **Expected Results**:
  - More accurate coordinates for specific landmarks and attractions
  - Better Google Maps link accuracy
  - Regional validation to catch obviously wrong coordinates
- **Cache Cleared**: Forced fresh generation with enhanced coordinate accuracy requirements

### Map Search Strategy Enhancement - [Current Date]

- **Issue Identified**: AI-generated coordinates were still inaccurate for specific venues
  - Even with enhanced prompts, coordinates like `40.5865, -122.3772` for Sundial Bridge were off by ~600m
  - Coordinate-based map links pointed to wrong locations
- **User Insight**: Suggested using exact venue names instead of coordinates for map search
- **Solution**: Redesigned map URL generation to prioritize location names over coordinates
- **Technical Changes**:
  - **Priority Change**: Modified `getGoogleMapsUrl()` to use venue name as first choice
  - **Format**: Now generates URLs like `https://www.google.com/maps/search/?api=1&query=Black Bear Diner, Redding, CA`
  - **Fallback System**: Only uses coordinates if no location name is available
  - **Better Accuracy**: Google Maps search by name is more reliable than AI-generated coordinates
- **Benefits**:
  - **Always Current**: Google Maps has up-to-date business information
  - **Handles Changes**: Works even if businesses move or change addresses
  - **No Coordinate Errors**: Eliminates AI coordinate generation inaccuracies
  - **Better UX**: Users get exactly the venue they expect
- **Expected Results**:
  - Map links should point to exact business locations
  - Sundial Bridge, Black Bear Diner, etc. should be found accurately
  - No more coordinate-based location errors

# Progress

- Created FAQ page frontend components (`FaqPage.js`, `ContactForm.js`).
- Added route `/faq` in `App.tsx`.
- Added basic FAQ content.
- Implemented collapsible contact form.
- Added basic integration test for `FaqPage`.
- Added FAQ link to the main navigation header in `App.tsx`.
- Adjusted header layout in `App.tsx` to place title and buttons on separate rows.
- Added header structure to `FaqPage.js`.
- Rearranged `App.tsx` header: buttons first, title second.
- Changed FAQ and Credits button/badge colors to blue variants.
- Changed FAQ and Credits button/badge colors to match 'My Trips' button style (`outline-primary` and `bg="primary"`).
- Moved 'Contact Us' button to `FaqPage` header, integrated form logic into `FaqPage`, removed `ContactForm` component.
- Added a new FAQ item to `FaqPage.js` explaining how to get the best results from the Travel Planner AI.
- Added three more FAQ items to `FaqPage.js` covering trip management, credit deduction, and itinerary customization.

# Decisions

- Used a simple custom accordion for FAQs.
- Mocked the contact form submission for now.
- Added basic bootstrap styling.
- Added FAQ link within the existing sidebar header, not a full-width top bar.
- Aligned header control buttons to the right on their own row.
- Used `outline-primary` for FAQ button and `bg="primary"` for Credits badge.
- Contact form is now managed directly within `FaqPage` for simplicity.

# Next Steps

- Implement backend endpoint for contact form email submission.
- Connect frontend form to backend endpoint.
- Run tests. 

## Session Summary - YYYY-MM-DD

**Goal:** Limit trip duration to a maximum of 10 days, add validation, and notify the user.

**Progress:**
1.  **Backend Validation:**
    *   Modified `travel_planner_ai/backend/models/trip.py`.
    *   Added a `model_validator` to `TripCreate` and `TripUpdate` Pydantic models.
    *   The validator ensures that `endDate` is not more than 10 days after `startDate` and that `startDate` is not after `endDate`.
    *   Raises a `ValueError` if validation fails, leading to a 422 HTTP response from FastAPI.
2.  **Backend Integration Tests:**
    *   Updated `travel_planner_ai/backend/tests/test_trips_api.py`.
    *   Added new test cases:
        *   `test_create_trip_duration_too_long()`: Checks for 422 error if duration > 10 days.
        *   `test_create_trip_duration_valid_max()`: Checks for success if duration = 10 days.
        *   `test_create_trip_end_date_before_start_date()`: Checks for 422 error if end date is before start date.
    *   Adjusted database mocks for more accurate testing of the creation endpoint.
3.  **Frontend Validation & Notification:**
    *   Modified `travel_planner_ai/frontend/src/components/TripForm.tsx`.
    *   Added a `validateDates(startDate, endDate)` function to check duration (max 10 days) and date order.
    *   This function is called in `onChange` handlers for both start and end date inputs, and in `handleSubmit`.
    *   The `dateError` state is updated, and `Form.Control.Feedback` displays the error message below the date inputs.

**Decisions Made:**
*   Implemented validation on both backend (Pydantic models) and frontend (React component state and handlers).
*   Backend raises `ValueError` for Pydantic to convert to 422 errors.
*   Frontend provides immediate feedback on date input changes and on form submission attempt.
*   Ensured integration tests cover the new backend validation logic.

**Next Steps:**
*   (If any further work related to this feature is planned) 

# Travel Planner AI - Development Progress

## Recent Session Progress

### Trip Start/Destination Simplification - COMPLETED ✅
Successfully implemented geolocation and autocomplete features for trip forms:

**Features Implemented:**
1. **Geolocation Support:**
   - User can click a button to use their current location for the "From" field
   - Uses browser's geolocation API with proper error handling
   - Reverse geocoding to convert coordinates to readable addresses
   - Fallback to coordinates if reverse geocoding fails
   - Comprehensive error handling for permission denied, unavailable, timeout

2. **Autocomplete for Destinations:**
   - Real-time search suggestions using Nominatim API (OpenStreetMap)
   - English-only results with proper language parameter
   - Debounced search (300ms) to prevent excessive API calls
   - Users can enable/disable autocomplete with a toggle switch
   - Clear button to quickly empty the input
   - Proper dropdown UI with hover effects

3. **Integration:**
   - Created new `LocationInput` component with all features
   - Updated `TripForm` to use the new component
   - Maintained backward compatibility with existing form structure
   - Proper accessibility with labels and ARIA attributes

**Technical Implementation:**
- Component: `travel_planner_ai/frontend/src/components/LocationInput.tsx`
- Tests: `travel_planner_ai/frontend/src/components/LocationInput.test.tsx`
- Updated: `travel_planner_ai/frontend/src/components/TripForm.tsx`
- Updated tests: `travel_planner_ai/frontend/src/components/TripForm.test.tsx`

**ESLint Warnings Fixed:**
- Removed unused `FaShare` import from App.tsx
- Removed unused `handleGenerateItinerary` function from App.tsx
- Removed unused `Dropdown` import from LocationInput.tsx
- Removed unused `refreshUserCredits` from Credits.tsx
- Fixed missing `location.pathname` dependency in Credits.tsx useEffect

## Architecture Decisions
- Uses free Nominatim API instead of paid Google Places API for autocomplete
- Implements proper debouncing and error handling
- Maintains user privacy by asking for location permission appropriately
- Provides fallback options when services are unavailable

## Current Status
- ✅ Geolocation support for origin field
- ✅ Autocomplete for both origin and destination fields
- ✅ User can disable autocomplete naturally
- ✅ English-only autocomplete results
- ✅ Integration tests implemented
- ✅ All ESLint warnings resolved
- ✅ Proper error handling and user feedback

## Next Steps
- The geolocation and autocomplete features are complete and ready for use
- Consider adding more sophisticated location validation if needed
- Monitor API usage and consider rate limiting if necessary 

### UX Design Recommendation: "Add From" Toggle Implementation - [Current Date]

- **Feature**: Implemented toggle-based UX approach for trip planning with progressive disclosure
- **UX Decision**: Destination-only by default with "Add From" toggle to reveal origin field
- **Rationale**: 
  - Minimal initial interface reduces cognitive load for new users
  - Progressive enhancement for power users who want route optimization
  - Cleaner, less cluttered form by default
  - Backend already supports both patterns with route-based logic
- **Frontend Implementation**:
  - **Default State**: Only destination field visible initially
  - **Toggle Control**: "Add From, if you want suggestions along your journey" checkbox
  - **Progressive Disclosure**: Origin field appears when toggle is enabled
  - **Smart Layout**: Destination field spans full width when origin hidden, half width when shown
  - **Data Management**: Origin data automatically cleared when toggle is disabled
  - **Clean Interface**: No helper text clutter - clear, direct messaging
  - **Loading Hints**: Added new hint about "Add From" toggle feature
- **Backend Validation**: 
  - Existing implementation already handles both scenarios in `ai_client.py`
  - Route logic: Activities along route from origin to destination when both provided
  - Destination logic: Activities within reasonable distance of destination when origin not provided
  - Trip hash generation includes origin for proper caching optimization

### UX Cleanup: Simplified Toggle Interface - [Current Date]

- **Objective**: Clean up the "Add From" toggle section by removing unnecessary helper text and optimizing the label
- **Changes Made**:
  - **Removed Helper Text**: Eliminated "✨ Route mode: We'll suggest activities along your journey" and "🎯 Your main destination" notes
  - **Optimized Toggle Label**: Changed from "Add starting location for route optimization" to "Add From, if you want suggestions along your journey" 
  - **Removed Redundant Messaging**: Eliminated additional explanatory text that was cluttering the interface
  - **Simplified Layout**: Cleaner, more direct user interface with less cognitive load
- **UX Benefits**:
  - **Reduced Clutter**: Less text on screen makes the form feel cleaner and more focused
  - **Clear Intent**: The new toggle label directly explains what happens when enabled
  - **Better Flow**: Users can quickly understand and interact with the toggle without extra explanations
  - **Professional Look**: Cleaner interface appears more polished and easier to use
- **Technical Updates**:
  - Updated `TripForm.tsx` to remove helper text elements
  - Modified toggle label text for better clarity
  - Updated test files to match new label text
  - Maintained all existing functionality while improving presentation
- **Result**: Cleaner, more professional toggle interface that clearly communicates purpose without unnecessary clutter

### UX Simplification & Hidden Gems LOCAL Enhancement - [Current Date]

- **Objective**: Further simplify UX by removing explanatory notes and enhance Hidden Gems to focus on LOCAL experiences
- **UX Simplification**:
  - **Removed Hidden Gems Note**: Eliminated the explanatory message that appeared when Hidden Gems was selected
  - **Cleaner Interface**: No more expandable explanatory text cluttering the entertainment preferences section
  - **Self-Explanatory Design**: The sparkle emoji badge (✨) on Hidden Gems button is sufficient visual indicator
- **Hidden Gems LOCAL Enhancement**:
  - **Strengthened LOCAL Focus**: Enhanced AI prompts to heavily emphasize LOCAL experiences
  - **LOCAL Repetition Strategy**: Uses "LOCAL" repeatedly to reinforce importance of local vs tourist experiences
  - **Specific LOCAL Categories**: 
    - LOCAL favorites: family-run businesses, neighborhood spots, LOCAL institutions
    - LOCAL venues: markets, festivals, community centers, family restaurants
    - LOCAL businesses: owned shops, artisan workshops, cultural venues
    - LOCAL neighborhoods: where residents actually live and work
    - LOCAL culture: traditions, customs, stories, history, guides
  - **Anti-Tourist Language**: Explicitly states "not tourist traps or chain establishments"
  - **Accessibility Balance**: "Balance accessibility with LOCAL authenticity (safe and reachable LOCAL spots)"
- **Technical Implementation**:
  - **Frontend**: Removed explanatory div from `TripForm.tsx` entertainment preferences section
  - **Backend**: Enhanced `_generate_prompt()` with comprehensive LOCAL-focused instructions
  - **Retry Prompts**: Updated `_generate_aggressive_retry_prompt()` to maintain LOCAL focus in retry attempts
  - **Prompt Structure**: Clear distinction between LOCAL experiences vs general recommendations
- **Expected Results**:
  - **Cleaner UX**: Users get clean interface without explanatory clutter
  - **Better LOCAL Recommendations**: AI should now strongly favor places where locals actually go
  - **Authentic Experiences**: More family-run businesses, local markets, neighborhood spots
  - **Cultural Authenticity**: Greater emphasis on local traditions and community venues
- **User Benefits**:
  - **Simplified Interface**: Less visual clutter for easier decision-making
  - **Authentic LOCAL Experiences**: Discover where locals actually eat, shop, and visit
  - **Community Connection**: Experience destinations as locals do, not as tourists
  - **Cultural Immersion**: Access to local traditions, customs, and community life

### Prompt Optimization for Optional Origin - [Current Date]

- **Objective**: Optimize AI prompt generation to better handle the new optional origin UX pattern
- **Issue Identified**: Previous prompt logic didn't properly handle empty origin strings from the new toggle UX
- **Optimizations Implemented**:
  - **Improved Origin Detection**: Fixed logic to properly detect when origin is provided vs empty string
  - **Two-Mode System**: Clear distinction between "Route Planning Mode" and "Destination-Focused Mode"
  - **Geographic Context Enhancement**: 
    - Route Mode: "Plan activities along or near the route from {origin} to {destination}"
    - Destination Mode: "ALL activities must be within reasonable distance of {destination}"
  - **Travel Mode Optimization**: Dynamic travel mode description based on origin availability
  - **Traveler Info Compression**: More efficient traveler information formatting
  - **Streamlined Formatting**: Cleaner prompt structure with better organization
- **Technical Changes**:
  - **Fixed Origin Check**: Changed from `origin != 'Origin'` to `origin and origin.lower() != 'origin'`
  - **String Handling**: Added `.strip()` to handle whitespace properly
  - **Two-Path Logic**: Clear separation of route-based vs destination-focused planning
  - **Consistent Updates**: Applied same optimizations to both main prompt and retry prompt
  - **Token Efficiency**: Reduced redundant text while maintaining clarity
- **Prompt Structure Improvements**:
  - **Clear Mode Indicators**: Visual distinction between 🗺️ Route Planning and 🎯 Destination-Focused modes
  - **Contextual Instructions**: Mode-specific guidance for activity planning
  - **Efficient Layout**: Compressed traveler info and formatting for better token usage
  - **Consistent Language**: Aligned terminology between main and retry prompts
- **Expected Results**:
  - **Better Default Behavior**: Destination-only planning works more effectively
  - **Clearer Route Planning**: When origin is provided, route optimization is more explicit
  - **Improved Token Efficiency**: Streamlined prompts use tokens more effectively
  - **Consistent Quality**: Both modes produce high-quality, relevant recommendations
- **Cache Considerations**: Origin changes properly trigger cache invalidation due to improved detection logic
- **Result**: AI prompts now properly adapt to the optional origin UX, providing optimal planning for both destination-only and route-based trips

### Token Optimization - Deprecated Coordinates and Activity IDs - [Current Date]

- **Objective**: Optimize token usage by commenting out unused features (coordinates and activity IDs)
- **Features Deprecated**:
  - **Coordinates**: No longer requested from AI or processed for Google Maps (use location names instead)
  - **Activity IDs**: No longer generated since frontend uses array indexes for React keys
- **Backend Changes (travel_planner_ai/backend/ai_client.py)**:
  - **AI Prompt**: Removed coordinate requirements from main prompt and retry prompts
  - **Response Processing**: Commented out coordinate parsing logic in `_process_response()`
  - **Fallback Itinerary**: Removed activity ID generation from fallback activities
  - **Coordinate Validation**: Disabled `_validate_coordinate_region()` function usage
  - **Route Processing**: Commented out activity ID fallback generation in routes.py
- **Frontend Changes (travel_planner_ai/frontend/src/components/Itinerary.tsx)**:
  - **Map Links**: Updated `getGoogleMapsUrl()` to prioritize location names over coordinates
  - **React Keys**: Changed from `activity.id` to array index for React keys  
  - **Coordinate Display**: Commented out coordinate-based map link generation
- **Type Definitions**:
  - **Activity Interface**: Added TODO deprecation comments for `id` and `coordinates` fields
  - **Backend Models**: Added TODO deprecation comments in `Activity` model
- **Token Savings**: Significant reduction in prompt tokens by removing coordinate generation requests
- **Functionality Preserved**: Google Maps still works using location names (more accurate than AI-generated coordinates)

### Prompt Quality Enhancement - [Current Date]

- **Objective**: Improve description and "Why" section quality to better connect activities to user preferences
- **Changes Made**:
  - **Mandatory Filter Accuracy**: Added critical requirement that ALL activities MUST match user preferences, budget, and family composition - NO activities that contradict filters
  - **Elaborative Descriptions**: Updated from 2-3 sentences to comprehensive 3-4 sentence descriptions with thorough details, historical context, and practical insights
  - **Elaborative "Why" Explanations**: Enhanced to require detailed, comprehensive explanations of exactly how activities align with user filters and requirements
  - **Filter Compliance**: Made filter accuracy a mandatory requirement rather than optional guidance
  - **Quality Standards**: Elevated to "filter-accurate, elaborative content" with emphasis on thoroughness
  - **Both Prompts Updated**: Applied improvements to both main prompt and aggressive retry prompt
- **Expected Outcome**: Activities will strictly match user filters with comprehensive explanations of why each recommendation fits their specific needs and preferences

### Collapsible Trip Information Panel - [Current Date]

🦋 **Objective**: Add a collapsible panel at the top of the activity list showing trip filters/information from formData

**Features Implemented:**
1. **Trip Information Panel**:
   - Added collapsible panel at the top of the Itinerary component
   - Displays key trip details from formData object
   - Collapsed by default to minimize visual clutter
   - Clean, organized layout with two-column display for optimal space usage

2. **Information Displayed**:
   - **Travel Type**: Road trip, Flight, Train, or Cruise
   - **Origin/Destination**: From and To locations  
   - **Travel Dates**: Start and end dates (formatted)
   - **Travelers**: Total count with breakdown (adults, children, infants)
   - **Budget Level**: Budget preference level
   - **Language**: Selected language preference
   - **Cuisine Preference**: Food preference selection
   - **Entertainment Preferences**: Selected entertainment activities (formatted)
   - **Intermediate Stops**: Count of planned stops (if any)

3. **Technical Implementation**:
   - **Component**: Modified `travel_planner_ai/frontend/src/components/Itinerary.tsx`
   - **Props**: Added `formData?: TripFormData` to ItineraryProps interface
   - **State**: Added `showTripInfo` state (collapsed by default)
   - **Helper Function**: Created `formatTripInfo()` to process and format all trip data
   - **UI**: Used Bootstrap Collapse component with Card layout
   - **Icons**: Added info circle and chevron icons for better UX

4. **Styling**:
   - **CSS File**: Added styles to `travel_planner_ai/frontend/src/styles/Itinerary.css`
   - **Panel Styling**: Light background, hover effects, smooth transitions
   - **Typography**: Organized layout with proper spacing and readable fonts
   - **Responsive**: Works well on both desktop and mobile devices

5. **Integration**:
   - **App.tsx**: Updated to pass `formData` prop to Itinerary component
   - **Type Safety**: Fixed TypeScript issues with null/undefined handling
   - **Backwards Compatibility**: Panel only shows when formData is available

**User Experience**:
- Panel is collapsed by default to keep focus on the itinerary
- Users can expand to see all trip filters and preferences that were used
- Clear, organized presentation of all trip parameters
- Helps users understand why certain activities were suggested
- Easy to collapse back for clean itinerary view

**Benefits**:
- **Transparency**: Users can see exactly what filters influenced their itinerary
- **Context**: Better understanding of why activities were selected
- **Reference**: Easy access to trip details without navigating back to form
- **Validation**: Users can verify their preferences were correctly applied

### Google OAuth Token Refresh Implementation - [Current Date]

- **Issue Identified**: "Failed to save title" error caused by expired Google OAuth access tokens (expire after 1 hour)
- **Root Cause**: No token refresh mechanism, causing 401 "Invalid Credentials" errors when updating trips
- **Error Pattern**: Backend logs showed repeated 401 responses from Google API during authentication
- **Solution Implemented**: 
  - **Automatic Token Refresh**: Added `refreshToken()` function in AuthContext to automatically refresh expired tokens
  - **Token Validation**: Added `ensureValidToken()` function that tests current token and refreshes if expired  
  - **Enhanced Error Handling**: Improved error messages for authentication issues in trip service
  - **Session Management**: Clear localStorage on 401 errors and provide user-friendly messages
  - **Graceful Fallback**: Sign out users if token refresh fails

**Technical Implementation**:
  - **AuthContext Updates**: Added token refresh and validation functions to auth context
  - **Trip Service Enhancement**: Better 401 error handling with automatic token cleanup
  - **Title Save Fix**: Updated `handleTitleSave()` to validate token before API calls
  - **Trip Save Protection**: Updated `handleSaveTrip()` with token validation
  - **TypeScript Fixes**: Properly typed all error catch blocks to resolve linter issues

**Key Functions Added**:
  - `refreshToken()`: Uses Google OAuth client to get new access token
  - `ensureValidToken()`: Validates current token with test API call, refreshes if needed
  - Enhanced error handling in `updateTrip()` with automatic session cleanup

**User Experience**:
  - **Seamless Operation**: Users won't see authentication errors during normal usage
  - **Clear Error Messages**: "Your session has expired. Please sign in again." instead of generic errors
  - **Automatic Recovery**: System attempts token refresh before showing errors
  - **Session Protection**: Invalid tokens are automatically cleared to prevent confusion

**Testing**: Created basic test suite for token refresh functionality
**Expected Result**: Title saving and all authenticated operations should work reliably without token expiration errors

// ... existing code ... 
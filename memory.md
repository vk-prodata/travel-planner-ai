# Project Memory

## Progress Updates

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
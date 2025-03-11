# Trip List Feature Documentation

## Overview

The Trip List feature provides users with the ability to view all their saved trips in a single page, allowing them to:
- See a summary of each trip with key details
- Delete trips they no longer need
- Navigate to a specific trip to view or edit its details

## Implementation Details

The Trip List feature consists of:

1. **TripList.tsx**: The main component that displays the list of trips
2. **TripList.css**: Styling for the Trip List component
3. **TripList.test.tsx**: Tests for the Trip List component
4. **App.tsx**: Updated with React Router to support navigation between pages

The feature uses the existing `getUserTrips` function from the trip service to fetch trips and adds a direct API call for deleting trips.

## How to Use

1. **Accessing the Trip List**:
   - When logged in, click the "My Trips" button in the application header
   - Alternatively, navigate to `/trips` directly in the browser

2. **Viewing a Trip**:
   - Click the "View Trip" button on any trip card to be redirected to the main page with that trip loaded

3. **Deleting a Trip**:
   - Click the "Delete" button on a trip card
   - Confirm deletion by clicking "Confirm" when prompted
   - The trip will be permanently removed from your account

## Testing

To run the tests for the Trip List component:

```bash
cd travel_planner_ai/frontend
npm test -- --testPathPattern=TripList
```

The tests verify:
- Loading state is displayed while fetching trips
- Trips are properly displayed after loading
- The "Sign in" message is shown for unauthenticated users
- Navigation works when "View Trip" is clicked
- Empty state is displayed when no trips are available

## Future Enhancements

Planned enhancements for the Trip List feature include:
- Sorting options (by date, destination, etc.)
- Filtering capabilities
- Pagination for users with many trips
- Search functionality to find specific trips
- Trip sharing options

## Screenshots

[Add screenshots here when the feature is deployed] 
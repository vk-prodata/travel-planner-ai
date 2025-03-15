import React from 'react';
import { Document, Page, Text, View, StyleSheet } from '@react-pdf/renderer';
import { TripItinerary, TripFormData } from '../types';

interface TripPDFProps {
  itinerary: TripItinerary;
  formData: TripFormData;
}

const styles = StyleSheet.create({
  page: {
    flexDirection: 'column',
    backgroundColor: '#ffffff',
    padding: 30
  },
  header: {
    marginBottom: 20,
    borderBottom: '1pt solid #999',
    paddingBottom: 10
  },
  title: {
    fontSize: 24,
    marginBottom: 10
  },
  subtitle: {
    fontSize: 14,
    color: '#666',
    marginBottom: 5
  },
  dayHeader: {
    fontSize: 18,
    marginTop: 15,
    marginBottom: 10,
    backgroundColor: '#f0f0f0',
    padding: 8
  },
  activity: {
    marginBottom: 8,
    paddingLeft: 10
  },
  activityTime: {
    fontSize: 12,
    color: '#666',
    marginBottom: 2
  },
  activityDescription: {
    fontSize: 12
  }
});

const TripPDF: React.FC<TripPDFProps> = ({ itinerary, formData }) => (
  <Document>
    <Page size="A4" style={styles.page}>
      <View style={styles.header}>
        <Text style={styles.title}>Trip to {formData.destination}</Text>
        <Text style={styles.subtitle}>
          {formData.startDate} - {formData.endDate}
        </Text>
        <Text style={styles.subtitle}>
          Travelers: {formData.adults} Adults
          {formData.children > 0 && `, ${formData.children} Children`}
          {formData.infants > 0 && `, ${formData.infants} Infants`}
        </Text>
      </View>

      {itinerary.days.map((day, index) => (
        <View key={index}>
          <Text style={styles.dayHeader}>Day {index + 1} - {day.date}</Text>
          {day.activities.map((activity, actIndex) => (
            <View key={actIndex} style={styles.activity}>
              <Text style={styles.activityTime}>{activity.time}</Text>
              <Text style={styles.activityDescription}>{activity.description}</Text>
            </View>
          ))}
        </View>
      ))}
    </Page>
  </Document>
);

export default TripPDF; 
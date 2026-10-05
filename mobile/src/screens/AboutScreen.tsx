import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { Screen } from '../components/Screen';

export function AboutScreen() {
  return <Screen>
    <View style={styles.card}><Text style={styles.logo}>🍊🛡️</Text><Text style={styles.title}>CitriSurksha</Text><Text style={styles.text}>CitriSurksha helps citrus farmers detect pests and insects from plant photos, view prevention and cure guidance, and maintain detection history.</Text><Text style={styles.text}>The pest catalogue, blog, yearly calendar and AI review data are managed from the admin panel and backend database.</Text><Text style={styles.version}>Version 0.1.0 · Expo SDK 54</Text></View>
  </Screen>;
}
const styles = StyleSheet.create({ card: { backgroundColor: 'white', borderRadius: 22, padding: 22, borderWidth: 1, borderColor: '#e0efd8', alignItems: 'center' }, logo: { fontSize: 64 }, title: { fontSize: 28, fontWeight: '900', color: '#116530', marginVertical: 8 }, text: { lineHeight: 22, color: '#40513d', textAlign: 'center', marginTop: 8 }, version: { marginTop: 18, color: '#7b8a77', fontWeight: '800' } });

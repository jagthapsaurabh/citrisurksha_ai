import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { Screen } from '../components/Screen';

export function TermsScreen() {
  return <Screen>
    <View style={styles.card}>
      <Text style={styles.title}>Terms & Conditions</Text>
      <Text style={styles.point}>1. CitriSurksha AI results are advisory and should be verified by an agriculture expert for severe infestations.</Text>
      <Text style={styles.point}>2. Follow local agriculture department guidance, pesticide labels, PPE requirements and pre-harvest intervals.</Text>
      <Text style={styles.point}>3. Uploaded images may be reviewed by authorised admins/agronomists to improve service quality.</Text>
      <Text style={styles.point}>4. Farmer images are not used for AI training unless approved through the admin review workflow.</Text>
      <Text style={styles.point}>5. Keep your profile and farm details accurate to receive better recommendations.</Text>
    </View>
  </Screen>;
}
const styles = StyleSheet.create({ card: { backgroundColor: 'white', borderRadius: 22, padding: 18, borderWidth: 1, borderColor: '#e0efd8' }, title: { fontSize: 25, fontWeight: '900', color: '#116530', marginBottom: 12 }, point: { lineHeight: 22, color: '#40513d', marginBottom: 12 } });

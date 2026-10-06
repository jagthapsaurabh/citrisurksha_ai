import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { Screen } from '../components/Screen';
import { useI18n } from '../i18n';

export function TermsScreen() {
  const { t } = useI18n();
  return <Screen>
    <View style={styles.card}>
      <Text style={styles.title}>{t('termsTitle')}</Text>
      <Text style={styles.point}>{t('terms1')}</Text>
      <Text style={styles.point}>{t('terms2')}</Text>
      <Text style={styles.point}>{t('terms3')}</Text>
      <Text style={styles.point}>{t('terms4')}</Text>
      <Text style={styles.point}>{t('terms5')}</Text>
    </View>
  </Screen>;
}
const styles = StyleSheet.create({ card: { backgroundColor: 'white', borderRadius: 22, padding: 18, borderWidth: 1, borderColor: '#e0efd8' }, title: { fontSize: 25, fontWeight: '900', color: '#116530', marginBottom: 12 }, point: { lineHeight: 22, color: '#40513d', marginBottom: 12 } });

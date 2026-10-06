import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { Screen } from '../components/Screen';
import { useI18n } from '../i18n';

export function AboutScreen() {
  const { t } = useI18n();
  return <Screen>
    <View style={styles.card}><Text style={styles.logo}>🍊🛡️</Text><Text style={styles.title}>CitriSuraksha</Text><Text style={styles.text}>{t('aboutText1')}</Text><Text style={styles.text}>{t('aboutText2')}</Text><Text style={styles.version}>{t('version')} 0.1.0</Text></View>
  </Screen>;
}
const styles = StyleSheet.create({ card: { backgroundColor: 'white', borderRadius: 22, padding: 22, borderWidth: 1, borderColor: '#e0efd8', alignItems: 'center' }, logo: { fontSize: 64 }, title: { fontSize: 28, fontWeight: '900', color: '#116530', marginVertical: 8 }, text: { lineHeight: 22, color: '#40513d', textAlign: 'center', marginTop: 8 }, version: { marginTop: 18, color: '#7b8a77', fontWeight: '800' } });

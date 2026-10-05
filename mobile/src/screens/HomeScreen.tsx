import React from 'react';
import { Pressable, StyleSheet, Text, useWindowDimensions, View } from 'react-native';
import { Screen } from '../components/Screen';
import { useI18n } from '../i18n';

export function HomeScreen({ navigation }: any) {
  const { t } = useI18n();
  const { width } = useWindowDimensions();
  const cardSize = Math.min((width - 56) / 2, 154);
  const goRoot = (name: string) => navigation.getParent()?.navigate(name);
  const menu = [
    { icon: '📷', title: t('scanPest'), sub: t('cameraOrGallery'), action: () => navigation.navigate('Scan'), color: '#116530' },
    { icon: '🕘', title: t('history'), sub: t('fullReports'), action: () => goRoot('History'), color: '#6c4ab6' },
    { icon: '🌿', title: t('pestGuide'), sub: t('preventCure'), action: () => navigation.navigate('Pest Management'), color: '#2e7d32' },
    { icon: '📅', title: t('calendarOperation'), sub: t('monthCare'), action: () => goRoot('Calendar'), color: '#f57c00' },
    { icon: '📰', title: t('blog'), sub: t('advisory'), action: () => goRoot('Blog'), color: '#0077b6' },
    { icon: '💊', title: 'Recommended insecticides', sub: 'CIB-RC advisory', action: () => goRoot('Insecticides'), color: '#00897b' },
    { icon: '📅', title: t('events'), sub: t('alertsPrograms'), action: () => goRoot('Events'), color: '#d81b60' },
    { icon: '💬', title: t('chat'), sub: t('askSupport'), action: () => goRoot('Chat'), color: '#3949ab' },
  ];

  return <Screen>
    <View style={styles.hero}>
      <Text style={styles.heroEmoji}>🍊</Text>
      <View style={{ flex: 1 }}>
        <Text style={styles.heroTitle}>{t('welcome')}</Text>
        <Text style={styles.heroText}>{t('welcomeText')}</Text>
      </View>
    </View>
    <Text style={styles.section}>{t('dashboard')}</Text>
    <View style={styles.grid}>
      {menu.map((item) => <Pressable key={item.title} onPress={item.action} style={[styles.card, { width: cardSize, height: cardSize, borderTopColor: item.color }]}>
        <Text style={styles.icon}>{item.icon}</Text>
        <Text style={styles.title}>{item.title}</Text>
        <Text style={styles.sub}>{item.sub}</Text>
      </Pressable>)}
    </View>
  </Screen>;
}

const styles = StyleSheet.create({
  hero: { backgroundColor: '#116530', borderRadius: 24, padding: 18, flexDirection: 'row', alignItems: 'center', gap: 14, shadowColor: '#116530', shadowOpacity: 0.22, shadowRadius: 14, elevation: 4 },
  heroEmoji: { fontSize: 48 },
  heroTitle: { color: 'white', fontWeight: '900', fontSize: 24 },
  heroText: { color: '#e4ffd9', marginTop: 5, lineHeight: 20 },
  section: { fontSize: 20, fontWeight: '900', marginTop: 20, marginBottom: 12, color: '#1b271c' },
  grid: { flexDirection: 'row', flexWrap: 'wrap', gap: 12, justifyContent: 'center' },
  card: { backgroundColor: 'white', borderRadius: 22, padding: 14, borderWidth: 1, borderColor: '#e0efd8', borderTopWidth: 5, justifyContent: 'center', shadowColor: '#000', shadowOpacity: 0.08, shadowRadius: 10, elevation: 2 },
  icon: { fontSize: 28, marginBottom: 8 },
  title: { fontWeight: '900', color: '#1b271c', fontSize: 15 },
  sub: { color: '#657763', marginTop: 4, fontSize: 11 },
});

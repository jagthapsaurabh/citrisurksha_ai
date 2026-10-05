import React, { useCallback, useState } from 'react';
import { Image, Pressable, StyleSheet, Text, View } from 'react-native';
import { useFocusEffect } from '@react-navigation/native';
import { api, mediaUrl } from '../api/client';
import { Screen } from '../components/Screen';
import { useI18n } from '../i18n';

export function HistoryScreen({ navigation }: any) {
  const { t, pestField } = useI18n(); const [items, setItems] = useState<any[]>([]); const [refreshing, setRefreshing] = useState(false);
  const load = useCallback(async () => { setRefreshing(true); try { setItems(await api.history()); } finally { setRefreshing(false); } }, []);
  useFocusEffect(useCallback(() => { load(); }, [load]));
  return <Screen>
    <Text style={styles.h1}>{t('detectionHistory')}</Text>
    <Text style={styles.help}>{t('historyHelp')}</Text>
    {items.map(item => <Pressable key={item.id} style={styles.card} onPress={() => navigation.navigate('DetectionDetail', { id: item.id, item })}>
      {item.image_url && <Image source={{ uri: mediaUrl(item.image_url) }} style={styles.thumb} />}
      <View style={{ flex: 1 }}>
        <Text style={styles.name}>{pestField(item.pest_details || item.pest_id, 'name', item.predicted_name)}</Text>
        <Text style={styles.meta}>{t('stage')}: {item.stage ?? '-'}</Text>
        <Text style={styles.status}>{item.corrected_by_admin ? 'Corrected by admin' : item.admin_status}</Text>
        <Text style={styles.date}>{new Date(item.created_at).toLocaleString()}</Text>
      </View>
      <Text style={styles.chev}>›</Text>
    </Pressable>)}
    {items.length === 0 && <View style={styles.empty}><Text style={styles.emptyText}>No detections yet. Use Scan to detect your first pest.</Text></View>}
  </Screen>;
}
const styles = StyleSheet.create({
  h1: { fontSize: 26, fontWeight: '900', marginBottom: 4 }, help: { color: '#5b6b58', marginBottom: 14 },
  card: { flexDirection: 'row', gap: 12, padding: 12, borderRadius: 16, backgroundColor: 'white', marginBottom: 10, borderColor: '#e0efd8', borderWidth: 1, alignItems: 'center' },
  thumb: { width: 72, height: 72, borderRadius: 14, backgroundColor: '#edf4e8' }, name: { color: '#116530', fontWeight: '900', fontSize: 17 }, meta: { color: '#4b5b49', marginTop: 3 }, status: { color: '#6c4ab6', marginTop: 3, fontWeight: '700' }, date: { color: '#7b8a77', fontSize: 12, marginTop: 3 }, chev: { fontSize: 34, color: '#adc1a6' }, empty: { backgroundColor: 'white', borderRadius: 18, padding: 20, alignItems: 'center' }, emptyText: { color: '#5b6b58', textAlign: 'center' }
});

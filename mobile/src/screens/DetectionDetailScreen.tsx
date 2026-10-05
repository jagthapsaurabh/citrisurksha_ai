import React, { useEffect, useState } from 'react';
import { ActivityIndicator, Alert, Image, Pressable, StyleSheet, Text, View } from 'react-native';
import { api, mediaUrl } from '../api/client';
import { Screen } from '../components/Screen';
import { useI18n } from '../i18n';

export function DetectionDetailScreen({ route }: any) {
  const { t, pestField } = useI18n();
  const { id, item } = route.params ?? {};
  const [data, setData] = useState<any>(item ?? null);
  const [loading, setLoading] = useState(Boolean(id && !item));
  useEffect(() => {
    if (!id) return;
    api.detection(id).then(setData).catch((e) => Alert.alert('Could not load result', e.message)).finally(() => setLoading(false));
  }, [id]);
  async function sendFeedback(isCorrect: boolean) {
    try {
      await api.feedback(data.id, { is_correct: isCorrect, comment: isCorrect ? 'Farmer marked correct' : 'Farmer says result may be wrong' });
      Alert.alert('Thank you', isCorrect ? 'Feedback saved.' : 'Feedback saved for expert review.');
    } catch (e: any) { Alert.alert('Feedback failed', e.message); }
  }
  if (loading) return <Screen><ActivityIndicator color="#116530" size="large" /></Screen>;
  const p = data?.pest_details;
  return <Screen>
    <Text style={styles.h1}>{t('fullResult')}</Text>
    {data?.image_url && <Image source={{ uri: mediaUrl(data.image_url) }} style={styles.photo} />}
    <View style={styles.card}>
      <Text style={styles.name}>{pestField(data?.pest_details || data?.pest_id, 'name', data?.predicted_name)}</Text>
      <Text style={styles.meta}>{t('stage')}: {data?.stage ?? '-'}</Text>
      <Text style={styles.badge}>{data?.corrected_by_admin ? 'Corrected by admin/agronomist' : `Status: ${data?.admin_status ?? 'unreviewed'}`}</Text>
      {data?.severity_level ? <Text style={styles.severity}>{t('severity')}: {data.severity_level}</Text> : null}
      {data?.admin_note ? <Text style={styles.note}>Admin note: {data.admin_note}</Text> : null}
      <View style={styles.feedbackRow}><Pressable style={styles.yes} onPress={() => sendFeedback(true)}><Text style={styles.fbText}>✓ {t('correct')}</Text></Pressable><Pressable style={styles.no} onPress={() => sendFeedback(false)}><Text style={styles.fbText}>✕ {t('wrong')}</Text></Pressable></View>
    </View>
    {p && <View style={styles.card}>
      <Text style={styles.section}>{t('pestDetails')}</Text>
      <Text style={styles.science}>{p.scientific_name}</Text>
      <Text style={styles.label}>{t('symptoms')}</Text><Text>{pestField(p, 'symptoms', p.symptoms)}</Text>
      <Text style={styles.label}>{t('lifecycle')}</Text><Text>{Object.entries(p.lifecycle ?? {}).map(([k, v]) => `${k}: ${v}`).join('\n')}</Text>
      <Text style={styles.label}>{t('prevention')}</Text><Text>{pestField(p, 'prevention', p.prevention)}</Text>
      <Text style={styles.label}>{t('cureControl')}</Text><Text>{pestField(p, 'cure', p.cure)}</Text>
      <Text style={styles.label}>{t('organicControl')}</Text><Text>{pestField(p, 'organic_control', p.organic_control)}</Text>
      <Text style={styles.label}>{t('chemicalControl')}</Text><Text>{pestField(p, 'chemical_control', p.chemical_control)}</Text>
      <Text style={styles.safety}>{pestField(p, 'safety_note', p.safety_note)}</Text>
    </View>}
    {data?.ai_response?.top_k && <View style={styles.card}><Text style={styles.section}>{t('aiTopResults')}</Text>{data.ai_response.top_k.map((x: any) => <Text key={x.pest_id}>• {x.pest_name}: {(x.confidence * 100).toFixed(1)}%</Text>)}</View>}
  </Screen>;
}
const styles = StyleSheet.create({
  h1: { fontSize: 25, fontWeight: '900', marginBottom: 12 }, photo: { width: '100%', height: 260, borderRadius: 20, backgroundColor: '#edf4e8', marginBottom: 12 },
  card: { backgroundColor: 'white', borderRadius: 18, padding: 16, borderColor: '#e0efd8', borderWidth: 1, marginBottom: 12 }, name: { color: '#116530', fontWeight: '900', fontSize: 23 }, meta: { color: '#4b5b49', marginTop: 5 }, badge: { alignSelf: 'flex-start', backgroundColor: '#eaf7e4', color: '#116530', fontWeight: '900', paddingHorizontal: 10, paddingVertical: 6, borderRadius: 999, marginTop: 10 }, severity: { marginTop: 8, fontWeight: '900', color: '#f57c00' }, note: { marginTop: 10, color: '#6c4ab6', fontWeight: '700' }, feedbackRow: { flexDirection: 'row', gap: 10, marginTop: 14 }, yes: { flex: 1, backgroundColor: '#116530', padding: 12, borderRadius: 12, alignItems: 'center' }, no: { flex: 1, backgroundColor: '#b00020', padding: 12, borderRadius: 12, alignItems: 'center' }, fbText: { color: 'white', fontWeight: '900' }, section: { color: '#116530', fontWeight: '900', fontSize: 18, marginBottom: 4 }, science: { fontStyle: 'italic', color: '#667', marginBottom: 8 }, label: { color: '#116530', fontWeight: '900', marginTop: 12 }, safety: { marginTop: 14, backgroundColor: '#fff8df', padding: 10, borderRadius: 10 }
});

import React, { useState } from 'react';
import { ActivityIndicator, Alert, Image, Pressable, StyleSheet, Text, View } from 'react-native';
import * as ImagePicker from 'expo-image-picker';
import { api } from '../api/client';
import { Screen } from '../components/Screen';
import { useI18n } from '../i18n';

export function DetectScreen({ navigation }: any) {
  const { t, pestField } = useI18n();
  const [uri, setUri] = useState<string | null>(null);
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [manageTab, setManageTab] = useState<'preventive' | 'curative'>('preventive');

  async function pick(source: 'camera' | 'gallery') {
    try {
      const perm = source === 'camera' ? await ImagePicker.requestCameraPermissionsAsync() : await ImagePicker.requestMediaLibraryPermissionsAsync();
      if (!perm.granted) return Alert.alert('Permission needed', 'Please allow access from phone settings.');
      const res = source === 'camera'
        ? await ImagePicker.launchCameraAsync({ quality: 0.85 })
        : await ImagePicker.launchImageLibraryAsync({ quality: 0.85, mediaTypes: ['images'] });
      if (!res.canceled) { setUri(res.assets[0].uri); setResult(null); await detect(res.assets[0].uri, source); }
    } catch (e: any) { Alert.alert('Image error', e.message || 'Could not open image picker.'); }
  }
  async function detect(photoUri: string, source: 'camera' | 'gallery') {
    try { setLoading(true); setResult(await api.detect(photoUri, source)); setManageTab('preventive'); }
    catch (e: any) { Alert.alert('Detection failed', e.message || 'Server error. Please try again.'); }
    finally { setLoading(false); }
  }
  const p = result?.pest_details;
  const isPest = result?.prediction?.is_citrus_pest !== false && !!p;
  return <Screen>
    <Text style={styles.h1}>{t('scanCitrusPest')}</Text>
    <Text style={styles.help}>{t('scanHelp')}</Text>
    <View style={styles.row}>
      <Pressable style={styles.button} onPress={() => pick('camera')}><Text style={styles.buttonText}>📷 {t('clickPhoto')}</Text></Pressable>
      <Pressable style={styles.button2} onPress={() => pick('gallery')}><Text style={styles.buttonText2}>🖼️ {t('upload')}</Text></Pressable>
    </View>
    {uri && <Image source={{ uri }} style={styles.preview} />}
    {loading && <View style={styles.loading}><ActivityIndicator size="large" color="#116530" /><Text style={styles.help}>{t('aiChecking')}</Text></View>}
    {result && <View style={styles.report}>
      <Text style={styles.reportTitle}>{isPest ? pestField(p, 'name', result.prediction.pest_name) : 'No citrus pest detected'}</Text>
      {isPest ? <Text style={styles.meta}>{t('severity')}: {result.prediction.severity_level ?? '-'}</Text> : null}
      <Text style={result.prediction.is_citrus_pest === false ? styles.notPest : styles.message}>{result.prediction.is_citrus_pest === false ? t('noPest') : result.message}</Text>
      {isPest && <>
        <Text style={styles.section}>{t('symptoms')}</Text><Text>{pestField(p, 'symptoms', p.symptoms)}</Text>
        <View style={styles.manageBox}>
          <Text style={styles.manageTitle}>{t('management')}</Text>
          <View style={styles.tabRow}>
            <Pressable onPress={() => setManageTab('preventive')} style={[styles.tab, manageTab === 'preventive' && styles.tabActive]}><Text style={manageTab === 'preventive' ? styles.tabTextActive : styles.tabText}>{t('preventive')}</Text></Pressable>
            <Pressable onPress={() => setManageTab('curative')} style={[styles.tab, manageTab === 'curative' && styles.tabActive]}><Text style={manageTab === 'curative' ? styles.tabTextActive : styles.tabText}>{t('curative')}</Text></Pressable>
          </View>
          {manageTab === 'preventive' ? <Text>{pestField(p, 'prevention', p.prevention)}</Text> : <View><Text style={styles.sectionSmall}>{t('cureControl')}</Text><Text>{pestField(p, 'cure', p.cure)}</Text><Text style={styles.sectionSmall}>{t('organicControl')}</Text><Text>{pestField(p, 'organic_control', p.organic_control)}</Text><Text style={styles.sectionSmall}>{t('chemicalControl')}</Text><Text>{pestField(p, 'chemical_control', p.chemical_control)}</Text></View>}
        </View>
        <Text style={styles.safety}>{pestField(p, 'safety_note', p.safety_note)}</Text>
      </>}
      <Pressable style={styles.historyButton} onPress={() => navigation.getParent()?.navigate('DetectionDetail', { id: result.detection_id })}><Text style={styles.historyText}>{t('viewFull')}</Text></Pressable>
    </View>}
  </Screen>;
}
const styles = StyleSheet.create({
  h1: { fontSize: 26, fontWeight: '900', color: '#1b271c' }, help: { color: '#5b6b58', marginTop: 6, lineHeight: 20 },
  row: { flexDirection: 'row', gap: 10, marginVertical: 16 }, button: { flex: 1, backgroundColor: '#116530', padding: 14, borderRadius: 16, alignItems: 'center' }, button2: { flex: 1, backgroundColor: '#ffb000', padding: 14, borderRadius: 16, alignItems: 'center' }, buttonText: { color: 'white', fontWeight: '900' }, buttonText2: { color: '#263300', fontWeight: '900' },
  preview: { width: '100%', height: 250, borderRadius: 18, marginBottom: 14, backgroundColor: '#e3eadf' }, loading: { padding: 18, alignItems: 'center' },
  report: { backgroundColor: 'white', borderRadius: 20, padding: 16, marginBottom: 30, borderWidth: 1, borderColor: '#dfeedd' }, reportTitle: { fontSize: 22, fontWeight: '900', color: '#116530' }, meta: { color: '#5b6b58', marginTop: 4 }, message: { marginTop: 8, color: '#116530', fontWeight: '800' }, notPest: { marginTop: 10, color: '#b00020', fontWeight: '900', backgroundColor: '#fff2f2', padding: 10, borderRadius: 10 }, section: { marginTop: 12, fontWeight: '900', color: '#116530' }, sectionSmall: { marginTop: 10, fontWeight: '900', color: '#116530' }, safety: { marginTop: 14, backgroundColor: '#fff8df', padding: 10, borderRadius: 10 }, historyButton: { marginTop: 14, backgroundColor: '#116530', padding: 13, borderRadius: 12, alignItems: 'center' }, historyText: { color: 'white', fontWeight: '900' },
  manageBox: { marginTop: 14, borderWidth: 1, borderColor: '#e0efd8', borderRadius: 16, padding: 12, backgroundColor: '#fbfff8' }, manageTitle: { fontSize: 18, fontWeight: '900', color: '#116530', marginBottom: 10 }, tabRow: { flexDirection: 'row', gap: 8, marginBottom: 12 }, tab: { flex: 1, padding: 10, borderRadius: 12, backgroundColor: 'white', alignItems: 'center', borderWidth: 1, borderColor: '#d5e8d0' }, tabActive: { backgroundColor: '#116530', borderColor: '#116530' }, tabText: { color: '#116530', fontWeight: '900' }, tabTextActive: { color: 'white', fontWeight: '900' }
});

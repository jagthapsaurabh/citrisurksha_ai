import React, { useEffect, useState } from 'react';
import { Alert, Pressable, StyleSheet, Text, TextInput, View } from 'react-native';
import { api } from '../api/client';
import { Lang, useI18n } from '../i18n';
import { Screen } from '../components/Screen';

export function ProfileScreen({ navigation, onLogout }: any) {
  const { lang, setLang, t } = useI18n();
  const [profile, setProfile] = useState<any>({});
  const [saving, setSaving] = useState(false);
  const [editing, setEditing] = useState(false);
  useEffect(() => { api.me().then((p) => { setProfile(p); if (['en','mr','hi'].includes(p.language)) setLang(p.language as Lang); }).catch((e) => Alert.alert(t('profileError'), e.message)); }, []);
  function setField(k: string, v: string) { setProfile((p: any) => ({ ...p, [k]: v })); }
  async function save() {
    try {
      setSaving(true);
      const payload = { ...profile, acres_land: profile.acres_land ? Number(profile.acres_land) : null, farming_experience_years: profile.farming_experience_years ? Number(profile.farming_experience_years) : null };
      const updated = await api.updateProfile(payload); setProfile(updated); setEditing(false);
      Alert.alert(t('saved'), t('profileUpdated'));
    } catch (e: any) { Alert.alert(t('couldNotSave'), e.message); }
    finally { setSaving(false); }
  }
  function confirmLogout() { Alert.alert(t('logout'), t('logoutConfirm'), [{ text: t('cancel'), style: 'cancel' }, { text: t('yes'), style: 'destructive', onPress: onLogout }]); }
  const FIELDS: [string, string][] = [
    ['name', t('fName')], ['email', t('fEmail')], ['village', t('fVillage')], ['district', t('fDistrict')], ['state', t('fState')], ['address', t('fAddress')],
    ['acres_land', t('fAcres')], ['plants', t('fPlants')], ['citrus_varieties', t('fVarieties')], ['irrigation_type', t('fIrrigation')], ['farming_experience_years', t('fExperience')],
  ];
  return <Screen>
    <View style={styles.topCard}><Text style={styles.avatar}>👨‍🌾</Text><View style={{ flex: 1 }}><Text style={styles.name}>{profile.name ?? t('profileTitle')}</Text><Text style={styles.meta}>{profile.phone}</Text><Text style={styles.badge}>{profile.profile_completed ? t('profileComplete') : t('completeProfile')}</Text></View></View>
    <Text style={styles.section}>{t('language')}</Text>
    <View style={styles.langRow}>{(['en','mr','hi'] as Lang[]).map(l => <Pressable key={l} onPress={async () => { try { setLang(l); setField('language', l); setProfile(await api.updateProfile({ language: l })); } catch(e:any){ Alert.alert(t('langUpdateFailed'), e.message); } }} style={[styles.langChip, (profile.language || lang) === l && styles.langChipActive]}><Text style={(profile.language || lang) === l ? styles.langTextActive : styles.langText}>{l === 'en' ? t('english') : l === 'mr' ? t('marathi') : t('hindi')}</Text></Pressable>)}</View>
    <View style={styles.sectionRow}><Text style={styles.section}>{t('farmDetails')}</Text><Pressable style={styles.editBtn} onPress={() => setEditing(!editing)}><Text style={styles.editText}>{editing ? t('cancel') : t('edit')}</Text></Pressable></View>
    {!editing ? <View style={styles.summary}>{FIELDS.map(([key,label]) => <Text key={key} style={styles.summaryText}><Text style={styles.bold}>{label}: </Text>{profile[key] == null || profile[key] === '' ? t('notAvailable') : String(profile[key])}</Text>)}</View> : <>{FIELDS.map(([key, label]) => <View key={key}><Text style={styles.label}>{label}</Text><TextInput style={[styles.input, key === 'address' || key === 'plants' ? styles.multi : null]} value={profile[key] == null ? '' : String(profile[key])} onChangeText={(v) => setField(key, v)} placeholder={label} keyboardType={key.includes('acres') || key.includes('years') ? 'numeric' : 'default'} multiline={key === 'address' || key === 'plants'} /></View>)}<Pressable style={styles.save} onPress={save}><Text style={styles.saveText}>{saving ? t('saving') : t('updateProfile')}</Text></Pressable></>}
    <Text style={styles.section}>{t('more')}</Text>
    <Pressable style={styles.row} onPress={() => navigation.getParent()?.navigate('About')}><Text style={styles.rowText}>ℹ️ {t('aboutApp')}</Text><Text>›</Text></Pressable>
    <Pressable style={styles.row} onPress={() => navigation.getParent()?.navigate('Terms')}><Text style={styles.rowText}>📜 {t('terms')}</Text><Text>›</Text></Pressable>
    <Pressable style={[styles.row, styles.logout]} onPress={confirmLogout}><Text style={[styles.rowText, { color: '#b00020' }]}>🚪 {t('logout')}</Text><Text style={{ color: '#b00020' }}>›</Text></Pressable>
  </Screen>;
}
const styles = StyleSheet.create({
  topCard: { backgroundColor: 'white', padding: 16, borderRadius: 20, borderWidth: 1, borderColor: '#e0efd8', flexDirection: 'row', gap: 14, alignItems: 'center' }, avatar: { fontSize: 58 }, name: { fontSize: 22, fontWeight: '900', color: '#116530' }, meta: { color: '#657763', marginTop: 2 }, badge: { alignSelf: 'flex-start', marginTop: 8, backgroundColor: '#eaf7e4', color: '#116530', paddingHorizontal: 10, paddingVertical: 5, borderRadius: 999, fontWeight: '900' }, section: { fontSize: 20, fontWeight: '900', marginTop: 20, marginBottom: 10 }, sectionRow: { flexDirection:'row', alignItems:'center', justifyContent:'space-between' }, editBtn:{backgroundColor:'#ffb000',paddingHorizontal:14,paddingVertical:8,borderRadius:12}, editText:{fontWeight:'900',color:'#263300'}, label: { fontWeight: '800', color: '#40513d', marginBottom: 5 }, input: { backgroundColor: 'white', borderWidth: 1, borderColor: '#d5e8d0', borderRadius: 14, padding: 12, marginBottom: 10 }, multi: { minHeight: 74, textAlignVertical: 'top' }, save: { backgroundColor: '#116530', borderRadius: 14, padding: 16, alignItems: 'center', marginTop: 6 }, saveText: { color: 'white', fontWeight: '900' }, langRow: { flexDirection: 'row', gap: 8, marginBottom: 8 }, langChip: { flex: 1, backgroundColor: 'white', padding: 12, borderRadius: 14, alignItems: 'center', borderWidth: 1, borderColor: '#d5e8d0' }, langChipActive: { backgroundColor: '#116530', borderColor: '#116530' }, langText: { color: '#116530', fontWeight: '900' }, langTextActive: { color: 'white', fontWeight: '900' }, summary:{backgroundColor:'white',borderWidth:1,borderColor:'#e0efd8',borderRadius:16,padding:14}, summaryText:{marginBottom:7,color:'#40513d'}, bold:{fontWeight:'900'}, row: { backgroundColor: 'white', borderRadius: 14, padding: 16, marginBottom: 10, flexDirection: 'row', justifyContent: 'space-between', borderWidth: 1, borderColor: '#e0efd8' }, rowText: { fontWeight: '900', color: '#1b271c' }, logout: { borderColor: '#ffd8d8', backgroundColor: '#fff7f7' }
});

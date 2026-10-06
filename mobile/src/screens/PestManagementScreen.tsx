import React, { useEffect, useMemo, useState } from 'react';
import { StyleSheet, Text, TextInput, View } from 'react-native';
import { api } from '../api/client';
import { Screen } from '../components/Screen';
import { useI18n } from '../i18n';

export function PestManagementScreen() {
  const { t, pestField, lang } = useI18n();
  const [pests, setPests] = useState<any[]>([]); const [query,setQuery]=useState(''); const [loading,setLoading]=useState(true); const [err,setErr]=useState('');
  useEffect(() => { api.pests().then(setPests).catch((e:any) => setErr(e.message)).finally(()=>setLoading(false)); }, []);
  const filtered=useMemo(()=>pests.filter(p=>`${p.common_name} ${p.scientific_name} ${p.id} ${(p.translations?.[lang]?.common_name)||''}`.toLowerCase().includes(query.toLowerCase())),[pests,query,lang]);
  return <Screen><Text style={styles.h1}>{t('pestManagement')}</Text><TextInput style={styles.search} placeholder={t('searchPest')} value={query} onChangeText={setQuery}/>{loading?<Text style={styles.empty}>{t('loading')}</Text>:null}{err?<Text style={styles.error}>{err}</Text>:null}{!loading&&!err&&filtered.length===0?<Text style={styles.empty}>{t('dataNotAvailable')}</Text>:null}{filtered.map(p => <View key={p.id} style={styles.card}><Text style={styles.name}>{pestField(p, 'name', p.common_name)}</Text><Text style={styles.science}>{p.scientific_name}</Text><Text style={styles.label}>{t('symptoms')}</Text><Text>{pestField(p, 'symptoms', p.symptoms)}</Text><Text style={styles.label}>{t('prevention')}</Text><Text>{pestField(p, 'prevention', p.prevention)}</Text><Text style={styles.label}>{t('cureControl')}</Text><Text>{pestField(p, 'cure', p.cure)}</Text><Text style={styles.label}>{t('organicControl')}</Text><Text>{pestField(p, 'organic_control', p.organic_control)}</Text><Text style={styles.label}>{t('chemicalControl')}</Text><Text>{pestField(p, 'chemical_control', p.chemical_control)}</Text></View>)}</Screen>;
}
const styles = StyleSheet.create({ h1: { fontSize: 26, fontWeight: '900', marginBottom: 10 }, search:{backgroundColor:'white',borderWidth:1,borderColor:'#d5e8d0',borderRadius:14,padding:12,marginBottom:12}, help: { color: '#5b6b58', marginBottom: 14 }, error:{color:'#b00020',fontWeight:'800',marginBottom:10}, empty:{backgroundColor:'white',borderRadius:14,padding:16,color:'#667',marginBottom:10}, card: { padding: 16, borderRadius: 18, backgroundColor: 'white', marginBottom: 12, borderWidth: 1, borderColor: '#e0efd8' }, name: { color: '#116530', fontSize: 20, fontWeight: '900' }, science: { fontStyle: 'italic', color: '#667', marginBottom: 8 }, label: { marginTop: 10, fontWeight: '900', color: '#116530' } });

import React, { useState } from 'react';
import { Alert, Image, Pressable, StyleSheet, Text, TextInput, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { api, setToken } from '../api/client';
import { registerPushTokenWithBackend } from '../push';
import { useI18n } from '../i18n';
const logo = require('../../assets/logo.png');

export function LoginScreen({ navigation, onLogin }: any) {
  const { t } = useI18n();
  const [phone, setPhone] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  async function submit() {
    try {
      if (!phone.trim()) throw new Error(t('phoneRequired'));
      if (!password) throw new Error(t('passwordPh'));
      setLoading(true); const res = await api.login(phone, password); setToken(res.access_token); await registerPushTokenWithBackend(); onLogin();
    } catch (e: any) { Alert.alert(t('loginFailed'), e.message || t('checkDetails')); }
    finally { setLoading(false); }
  }
  return <SafeAreaView style={styles.container}><View style={styles.card}><Image source={logo} style={styles.logo}/><Text style={styles.brand}>CitriSuraksha AI</Text><Text style={styles.tag}>Scan · Detect · Protect</Text><Text style={styles.h1}>{t('loginTitle')}</Text><TextInput style={styles.input} placeholder={t('phonePh')} keyboardType="phone-pad" value={phone} onChangeText={setPhone} /><View style={styles.passWrap}><Text style={styles.lock}>🔒</Text><TextInput style={styles.passInput} placeholder={t('passwordPh')} secureTextEntry={!showPassword} value={password} onChangeText={setPassword} /><Pressable onPress={() => setShowPassword(!showPassword)}><Text style={styles.show}>{showPassword ? '🙈' : '👁️'}</Text></Pressable></View><Pressable style={[styles.button,loading&&{opacity:.7}]} onPress={submit} disabled={loading}><Text style={styles.buttonText}>{loading ? t('pleaseWait') : t('loginBtn')}</Text></Pressable><Pressable onPress={() => navigation.navigate('Register')}><Text style={styles.link}>{t('registerLink')}</Text></Pressable></View></SafeAreaView>;
}
const styles = StyleSheet.create({ container: { flex: 1, padding: 20, justifyContent: 'center', backgroundColor: '#050805' }, card: { backgroundColor: '#ffffff', borderRadius: 30, padding: 22, borderWidth: 1, borderColor: '#e0efd8', shadowColor:'#116530',shadowOpacity:.25,shadowRadius:20,elevation:5 }, logo:{width:150,height:150,borderRadius:28,alignSelf:'center',marginBottom:8}, brand: { textAlign: 'center', fontSize: 28, fontWeight: '900', color: '#116530' }, tag:{textAlign:'center',color:'#4f6b4d',fontWeight:'800',letterSpacing:1,marginBottom:18}, h1: { fontSize: 24, fontWeight: '900', marginBottom: 14 }, input: { backgroundColor: '#fbfff8', borderColor: '#d5e8d0', borderWidth: 1, padding: 14, borderRadius: 14, marginBottom: 12 }, passWrap: { flexDirection: 'row', alignItems: 'center', backgroundColor: '#fbfff8', borderColor: '#d5e8d0', borderWidth: 1, borderRadius: 14, marginBottom: 12, paddingRight: 12 }, lock:{paddingLeft:12}, passInput: { flex: 1, padding: 14 }, show: { color: '#116530', fontWeight: '900', fontSize:20 }, button: { backgroundColor: '#116530', padding: 16, borderRadius: 14, alignItems: 'center', marginTop: 8 }, buttonText: { color: 'white', fontWeight: '900' }, link: { textAlign: 'center', color: '#116530', marginTop: 18, fontWeight: '800' } });

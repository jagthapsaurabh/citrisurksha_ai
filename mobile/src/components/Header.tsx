import React, { useCallback, useState } from 'react';
import { Alert, Image, Pressable, View, Text, StyleSheet } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useFocusEffect, useNavigation } from '@react-navigation/native';
import { api } from '../api/client';

const logo = require('../../assets/logo.png');

export function AppHeader() {
  const navigation = useNavigation<any>();
  const [count,setCount]=useState(0);
  useFocusEffect(useCallback(()=>{api.unreadNotifications().then(r=>setCount(r.count||0)).catch(()=>setCount(0));},[]));
  function go(){ try { navigation.getParent()?.navigate('Notifications'); } catch { try{navigation.navigate('Notifications')}catch{Alert.alert('Notifications', 'No new notifications');} } }
  return (
    <SafeAreaView edges={["top"]} style={styles.safe}>
      <View style={styles.header}>
        <Image source={logo} style={styles.logo} />
        <View style={{ flex: 1 }}>
          <Text style={styles.title}>CitriSuraksha AI</Text>
          <Text style={styles.subtitle}>Scan · Detect · Protect</Text>
        </View>
        <Pressable style={styles.bellWrap} onPress={go}><Text style={styles.bell}>🔔</Text>{count>0&&<View style={styles.badge}><Text style={styles.badgeText}>{count>99?'99+':count}</Text></View>}</Pressable>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { backgroundColor: '#071108' },
  header: { paddingHorizontal: 16, paddingBottom: 12, paddingTop: 8, backgroundColor: '#071108', flexDirection: 'row', alignItems: 'center', gap: 12, borderBottomWidth: 1, borderBottomColor: '#163d20' },
  logo: { width: 50, height: 50, borderRadius: 14, backgroundColor: '#071108' },
  title: { color: 'white', fontWeight: '900', fontSize: 22 },
  subtitle: { color: '#d9f9df', fontSize: 12, letterSpacing: 1 },
  bellWrap: { width: 42, height: 42, borderRadius: 14, backgroundColor: '#ffffff22', alignItems: 'center', justifyContent: 'center', position:'relative' },
  bell: { fontSize: 24 }, badge:{position:'absolute',right:-4,top:-4,backgroundColor:'#ffb000',borderRadius:999,minWidth:20,height:20,alignItems:'center',justifyContent:'center',paddingHorizontal:4}, badgeText:{fontSize:10,fontWeight:'900',color:'#1b271c'}
});

import React, { useEffect, useState } from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { StatusBar } from 'expo-status-bar';
import { Image, Platform, View, Text, StyleSheet } from 'react-native';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import Constants from 'expo-constants';
import { LoginScreen } from './src/screens/LoginScreen';
import { RegisterScreen } from './src/screens/RegisterScreen';
import { DetectScreen } from './src/screens/DetectScreen';
import { HistoryScreen } from './src/screens/HistoryScreen';
import { DetectionDetailScreen } from './src/screens/DetectionDetailScreen';
import { PestManagementScreen } from './src/screens/PestManagementScreen';
import { ProfileScreen } from './src/screens/ProfileScreen';
import { CalendarScreen } from './src/screens/CalendarScreen';
import { BlogScreen } from './src/screens/BlogScreen';
import { BlogDetailScreen } from './src/screens/BlogDetailScreen';
import { AboutScreen } from './src/screens/AboutScreen';
import { TermsScreen } from './src/screens/TermsScreen';
import { EventScreen } from './src/screens/EventScreen';
import { ChatScreen } from './src/screens/ChatScreen';
import { InsecticidesScreen } from './src/screens/InsecticidesScreen';
import { NotificationScreen } from './src/screens/NotificationScreen';
import { HomeScreen } from './src/screens/HomeScreen';
import { AppHeader } from './src/components/Header';
import { setToken } from './src/api/client';
import { LanguageProvider, useI18n } from './src/i18n';
import { ErrorBoundary } from './src/components/ErrorBoundary';


async function requestAppPermissions() {
  if (Constants.appOwnership === 'expo') {
    // Avoid loading expo-notifications in Expo Go. Remote push requires a development build on SDK 53+.
    return;
  }
  const Notifications = await import('expo-notifications');
  Notifications.setNotificationHandler({
    handleNotification: async () => ({
      shouldShowBanner: true,
      shouldShowList: true,
      shouldPlaySound: false,
      shouldSetBadge: true,
    }),
  });
  if (Platform.OS === 'android') {
    await Notifications.setNotificationChannelAsync('citrisurksha-alerts', {
      name: 'CitriSurksha pest alerts',
      importance: Notifications.AndroidImportance.DEFAULT,
    });
  }
  await Notifications.requestPermissionsAsync();
}

const RootStack = createNativeStackNavigator();
const Tab = createBottomTabNavigator();

const appLogo = require('./assets/logo.png');
function Splash() {
  return <View style={styles.splash}><Image source={appLogo} style={styles.splashLogo}/><Text style={styles.name}>CitriSuraksha AI</Text><Text style={styles.tagline}>Scan · Detect · Protect</Text></View>;
}

function DashboardTabs({ onLogout }: { onLogout: () => void }) {
  const { t } = useI18n();
  return (
    <View style={{ flex: 1, backgroundColor: '#f8fff3' }}>
      <AppHeader />
      <Tab.Navigator
        screenOptions={{
          headerShown: false,
          tabBarActiveTintColor: '#116530',
          tabBarInactiveTintColor: '#799075',
          tabBarHideOnKeyboard: true,
          tabBarLabelStyle: { fontSize: 12, fontWeight: '800' },
          tabBarStyle: { height: Platform.OS === 'ios' ? 92 : 88, paddingTop: 8, paddingBottom: Platform.OS === 'ios' ? 30 : 22, borderTopColor: '#dcebd4' },
          tabBarItemStyle: { paddingVertical: 2 },
        }}
      >
        <Tab.Screen name="Home" component={HomeScreen} options={{ tabBarLabel: t('home'), tabBarIcon: ({ focused }) => <Text style={focused ? styles.tabIconActive : styles.tabIcon}>🏠</Text> }} />
        <Tab.Screen name="Scan" component={DetectScreen} options={{ tabBarLabel: t('scan'), tabBarIcon: ({ focused }) => <Text style={focused ? styles.tabIconActive : styles.tabIcon}>📷</Text> }} />
        <Tab.Screen name="Pest Management" component={PestManagementScreen} options={{ tabBarLabel: t('pestManagement'), tabBarIcon: ({ focused }) => <Text style={focused ? styles.tabIconActive : styles.tabIcon}>🌿</Text> }} />
        <Tab.Screen name="Profile" options={{ tabBarLabel: t('profile'), tabBarIcon: ({ focused }) => <Text style={focused ? styles.tabIconActive : styles.tabIcon}>👤</Text> }}>
          {(props) => <ProfileScreen {...props} onLogout={onLogout} />}
        </Tab.Screen>
      </Tab.Navigator>
    </View>
  );
}

export default function App() {
  const [splash, setSplash] = useState(true);
  const [authed, setAuthed] = useState(false);
  useEffect(() => { const t = setTimeout(() => setSplash(false), 1000); return () => clearTimeout(t); }, []);
  useEffect(() => { if (authed) requestAppPermissions().catch(() => undefined); }, [authed]);
  const logout = () => { setToken(null); setAuthed(false); };
  if (splash) return <SafeAreaProvider><ErrorBoundary><LanguageProvider><Splash /><StatusBar style="light" /></LanguageProvider></ErrorBoundary></SafeAreaProvider>;
  return (
    <SafeAreaProvider>
      <ErrorBoundary>
      <LanguageProvider>
      <NavigationContainer>
        <RootStack.Navigator screenOptions={{ headerStyle: { backgroundColor: '#116530' }, headerTintColor: 'white', headerTitleStyle: { fontWeight: '900' } }}>
          {authed ? <>
            <RootStack.Screen name="Dashboard" options={{ headerShown: false }}>{() => <DashboardTabs onLogout={logout} />}</RootStack.Screen>
            <RootStack.Screen name="History" component={HistoryScreen} options={{ title: 'Detection History' }} />
            <RootStack.Screen name="DetectionDetail" component={DetectionDetailScreen} options={{ title: 'Detection Result' }} />
            <RootStack.Screen name="Calendar" component={CalendarScreen} options={{ title: 'Calendar of Operation' }} />
            <RootStack.Screen name="Blog" component={BlogScreen} options={{ title: 'Blog & Advisory' }} />
            <RootStack.Screen name="BlogDetail" component={BlogDetailScreen} options={{ title: 'Blog Details' }} />
            <RootStack.Screen name="About" component={AboutScreen} options={{ title: 'About App' }} />
            <RootStack.Screen name="Terms" component={TermsScreen} options={{ title: 'Terms & Conditions' }} />
            <RootStack.Screen name="Events" component={EventScreen} options={{ title: 'Events & Alerts' }} />
            <RootStack.Screen name="Chat" component={ChatScreen} options={{ title: 'Farmer Chat' }} />
            <RootStack.Screen name="Insecticides" component={InsecticidesScreen} options={{ title: 'Recommended insecticides' }} />
            <RootStack.Screen name="Notifications" component={NotificationScreen} options={{ title: 'Notifications' }} />
          </> : <>
            <RootStack.Screen name="Login" options={{ headerShown: false }}>{(props) => <LoginScreen {...props} onLogin={() => setAuthed(true)} />}</RootStack.Screen>
            <RootStack.Screen name="Register" options={{ headerShown: false }}>{(props) => <RegisterScreen {...props} onRegister={() => setAuthed(true)} />}</RootStack.Screen>
          </>}
        </RootStack.Navigator>
        <StatusBar style="light" />
      </NavigationContainer>
      </LanguageProvider>
      </ErrorBoundary>
    </SafeAreaProvider>
  );
}

const styles = StyleSheet.create({
  splash: { flex: 1, backgroundColor: '#050805', alignItems: 'center', justifyContent: 'center', padding: 24 },
  splashLogo: { width: 240, height: 240, borderRadius: 34, marginBottom: 12 },
  name: { color: 'white', fontSize: 34, fontWeight: '900', marginTop: 12 },
  tagline: { color: '#eaffd8', fontSize: 18, marginTop: 8, textAlign: 'center', letterSpacing: 1 }, 
  tabIcon: { fontSize: 21, opacity: 0.75 },
  tabIconActive: { fontSize: 23 },
});

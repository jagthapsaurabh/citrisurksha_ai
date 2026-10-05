import { Platform } from 'react-native';
import Constants from 'expo-constants';
import { api } from './api/client';

export async function registerPushTokenWithBackend() {
  try {
    if (Constants.appOwnership === 'expo') return { skipped: true, reason: 'Expo Go does not support Firebase remote push on SDK 53+' };
    let token: string | undefined;
    let platform: string = Platform.OS;
    try {
      const mod: any = await import('@react-native-firebase/messaging');
      const messaging = mod.default;
      const instance = messaging();
      await instance.requestPermission();
      token = await instance.getToken();
      platform = `${Platform.OS}-fcm`;
      instance.onTokenRefresh((newToken: string) => api.registerFcmToken(newToken, platform).catch(() => undefined));
    } catch {
      const Notifications = await import('expo-notifications');
      const perm = await Notifications.requestPermissionsAsync();
      if (!perm.granted) return { skipped: true, reason: 'permission_denied' };
      const deviceToken = await Notifications.getDevicePushTokenAsync();
      token = String(deviceToken.data);
      platform = `${Platform.OS}-${deviceToken.type || 'device'}`;
    }
    if (token) await api.registerFcmToken(token, platform);
    return { registered: Boolean(token), platform };
  } catch (e: any) {
    console.warn('Push token registration failed', e?.message || e);
    return { error: e?.message || 'push registration failed' };
  }
}

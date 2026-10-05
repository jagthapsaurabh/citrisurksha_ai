# CitriSurksha Mobile Native Permissions - Expo SDK 54

The mobile app has been upgraded to **Expo SDK 54** and native Android/iOS folders were generated with:

```bash
npx expo prebuild --clean --no-install --platform all
```

Native configuration files:

- `android/app/src/main/AndroidManifest.xml`
- `ios/CitriSurksha/Info.plist`
- `ios/CitriSurksha/CitriSurksha.entitlements`

## SDK 54 dependency baseline

Important SDK 54 versions now used:

- `expo ~54.0.35`
- `react 19.1.0`
- `react-native 0.81.5`
- `expo-image-picker ~17.0.11`
- `expo-notifications ~0.32.17`
- `expo-status-bar ~3.0.9`
- `expo-build-properties ~1.0.10`
- `expo-system-ui ~6.0.9`
- `react-native-safe-area-context ~5.6.0`
- `react-native-screens ~4.16.0`
- `typescript ~5.9.2`

## Runtime permissions requested in app code

- Camera: pest detection and AI training image capture.
- Gallery/photo library: pest image upload.
- Notifications: pest alerts, calendar reminders and training review updates.

Runtime prompts are implemented in:

- `src/screens/DetectScreen.tsx`
- `src/screens/TrainAIScreen.tsx`
- `App.tsx`

## Android native permissions

Configured in `app.json` and synced into `AndroidManifest.xml` by Expo prebuild:

- `android.permission.CAMERA`
- `android.permission.READ_MEDIA_IMAGES`
- `android.permission.READ_EXTERNAL_STORAGE`
- `android.permission.POST_NOTIFICATIONS`
- `android.permission.INTERNET`
- `android.permission.ACCESS_NETWORK_STATE`
- `android.permission.VIBRATE`

`expo-image-picker` may also generate `WRITE_EXTERNAL_STORAGE` for older Android compatibility. `RECORD_AUDIO` is explicitly removed using the SDK 54 image-picker plugin setting:

```json
"microphonePermission": false
```

## iOS permission keys

Configured in `Info.plist`:

- `NSCameraUsageDescription`
- `NSPhotoLibraryUsageDescription`
- `NSPhotoLibraryAddUsageDescription`
- `NSUserNotificationsUsageDescription`

## Regenerating native folders

If you change native config in `app.json`, regenerate native projects:

```bash
cd mobile
npm install
npx expo prebuild --clean --no-install --platform all
```

## Validation

TypeScript passes:

```bash
npx tsc --noEmit
```

`expo-doctor` passes 17/18 checks. The remaining check is expected because this repository intentionally keeps native `android/` and `ios/` folders while also keeping Expo prebuild config in `app.json`. If using pure Continuous Native Generation, do not commit native folders.

## Production reminder

`usesCleartextTraffic` and `NSAllowsArbitraryLoads` are enabled for local HTTP development. Disable them and use HTTPS before Play Store/App Store release.

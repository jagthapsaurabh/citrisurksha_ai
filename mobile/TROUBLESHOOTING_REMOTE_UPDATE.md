# Fix: java.io.IOException: Failed to download remote update

This error normally means the app/Expo Go could not download the JavaScript bundle or remote update from the development server. It is very common when the phone/emulator cannot reach Metro on your computer.

## Project-side fix applied

The project now disables remote OTA updates during development in `app.json`:

```json
"updates": {
  "enabled": false,
  "checkAutomatically": "NEVER",
  "fallbackToCacheTimeout": 0
}
```

After prebuild this generated Android metadata:

```xml
<meta-data android:name="expo.modules.updates.ENABLED" android:value="false" />
<meta-data android:name="expo.modules.updates.EXPO_UPDATES_CHECK_ON_LAUNCH" android:value="NEVER" />
```

## Recommended start command

Use tunnel mode if your phone and laptop are not reliably on the same reachable network:

```bash
cd mobile
npm run start:tunnel
```

Other options:

```bash
npm run start:lan
npm run start:localhost
```

## Clean rebuild steps

If the error remains, clear the old native app and rebuild:

```bash
cd mobile
rm -rf node_modules
npm install
npx expo prebuild --clean --no-install --platform all
npx expo run:android
# or
npx expo run:ios
```

Also uninstall the old CitriSurksha app from the device/simulator before reinstalling.

## Network checklist

- Make sure phone and computer are on the same Wi-Fi if using LAN mode.
- Disable VPN/proxy on phone and computer.
- Allow Node.js through Windows Defender Firewall/antivirus.
- Prefer `npm run start:tunnel` when testing on a physical phone.
- For Android emulator, localhost to host machine is usually `10.0.2.2`, not `localhost`.

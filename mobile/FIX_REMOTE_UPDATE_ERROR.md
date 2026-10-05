# Fix: java.io.IOException Failed to download remote update

`updates.enabled=false` disables EAS/OTA update checks in standalone/dev builds. It does **not** stop Expo Go or a development build from downloading the JavaScript bundle from Metro during development.

If you still see:

```text
java.io.IOException: Failed to download remote update
```

it means the device cannot reach the Metro dev server URL, or you are trying to run native Firebase modules inside Expo Go.

## Important for this project

CitriSurksha uses native Firebase modules:

```text
@react-native-firebase/app
@react-native-firebase/messaging
```

Therefore, **do not use Expo Go** for full testing. Use a development build.

## Android fix

```powershell
cd citrisurksha\mobile
npm install
npx expo prebuild --clean
npx expo run:android --device
npm run start:dev
```

If it still fails:

```powershell
adb reverse tcp:8081 tcp:8081
npm run start:localhost
```

## iOS fix

```powershell
cd citrisurksha\mobile
npm install
npx expo prebuild --clean
npx expo run:ios --device
npm run start:dev
```

For physical iPhone, make sure Mac and phone are on the same network or use tunnel.

## Network checklist

- Phone and laptop are on the same Wi-Fi if using LAN.
- Disable VPN/proxy.
- Allow Node.js through Windows Defender Firewall.
- Use `npm run start:dev` because it uses dev-client + tunnel.
- Uninstall old CitriSurksha app from device before reinstalling.
- Clear Expo/Metro cache.

## Full reset command

```powershell
cd citrisurksha\mobile
rd /s /q node_modules
npm install
npx expo prebuild --clean
npx expo run:android --device
npm run start:dev
```

## If terminal says: No development build is installed

This means the QR code is for a development build, but your phone does not yet have the CitriSurksha development app installed.

Install it first:

```powershell
cd citrisurksha\mobile
npm install
npx expo run:android --device
```

Then start Metro:

```powershell
npm run start:dev
```

If you cannot build locally, create an EAS internal development build:

```powershell
npm install -g eas-cli
eas login
eas build --profile development --platform android
```

Download and install the generated APK on your phone, then run `npm run start:dev` and scan/open again.

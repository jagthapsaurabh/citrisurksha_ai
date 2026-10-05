# Firebase Push Notifications

CitriSurksha is configured for Firebase Cloud Messaging (FCM) on Android and iOS.

## Client app IDs

- Android package: `com.citrisurksha.app`
- iOS bundle ID: `com.citrisurksha.app`

## Client config files added

- `mobile/google-services.json`
- `mobile/android/app/google-services.json`
- `mobile/GoogleService-Info.plist`
- `mobile/ios/CitriSurksha/GoogleService-Info.plist`

`app.json` includes:

```json
{
  "android": { "googleServicesFile": "./google-services.json" },
  "ios": { "googleServicesFile": "./GoogleService-Info.plist" },
  "plugins": ["@react-native-firebase/app", "@react-native-firebase/messaging"]
}
```

## Important: Firebase server credentials

The uploaded `google-services.json` and `GoogleService-Info.plist` are client configuration files. They are not enough for backend sending.

To send push notifications from backend, download a Firebase Admin SDK service account JSON:

Firebase Console → Project Settings → Service Accounts → Generate new private key

Save it as:

```text
citrisurksha/firebase-service-account.json
```

Then set in `.env`:

```env
FIREBASE_SERVICE_ACCOUNT_PATH=./firebase-service-account.json
```

Do not commit the service account to public git.

## Mobile token registration

After login/register, mobile tries to get FCM token using `@react-native-firebase/messaging` in development/production builds and saves it to backend:

```http
POST /notifications/register-token
```

Expo Go does not support Firebase remote push in SDK 53+. Use a development build:

```bash
cd mobile
npx expo prebuild --clean
npx expo run:android
npx expo run:ios
```

## Backend notification APIs

```http
GET    /notifications
GET    /notifications/unread-count
POST   /notifications/{id}/read
DELETE /notifications/{id}
POST   /notifications/clear
POST   /notifications/admin/send
```

## Admin custom push

Admin Dashboard includes **Send Custom Push Notification**. It stores notification records and sends FCM to all farmers with tokens.

## Event notification

When admin creates an event with `send_notification=true`, backend creates notifications and sends FCM to all farmers.

## Mobile notification UI

- Bell icon opens Notification screen.
- Bell shows unseen notification count.
- Farmer can mark/read by opening, delete one notification, or clear all.

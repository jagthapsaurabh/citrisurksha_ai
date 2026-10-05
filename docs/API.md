# API Specification Summary

Base URL in local Docker: `http://localhost:8080/api`

## Auth

### `POST /auth/register`

```json
{ "name": "Ramesh", "phone": "9876543210", "password": "secret", "district": "Nagpur", "language": "en" }
```

Returns JWT token.

### `POST /auth/login`

```json
{ "phone": "9876543210", "password": "secret" }
```

## Farmer mobile

### `POST /detections`

Multipart form:

- `image`: jpg/png/webp
- `source`: `camera` or `gallery`

Response includes prediction and pest management details.

### `GET /detections/history`

Returns the logged-in farmer's last 100 detections.

### `POST /detections/{id}/send-for-training`

Farmer can opt in to submit a detection image for admin review/training.

### `GET /pests`

Cached pest catalogue with prevention and cure.

### `GET /pests/{pest_id}`

Detailed pest information.

### `GET /pests/calendar/year`

Month-wise citrus care calendar.

### `GET /blogs`

Farmer advisory/blog posts.

## Admin

Admin seed credentials for local dev:

- phone: `9999999999`
- password: `admin123`

Change this before any real deployment.

### `GET /admin/dashboard`

Counts users, pests, detections, training images and training jobs.

### `POST /admin/pests`

Create/update pest catalogue details.

### `POST /admin/training-images`

Multipart upload verified labelled training image.

### `GET /admin/detections/review`

List farmer detections awaiting expert review.

### `POST /admin/detections/{id}/approve-training`

Approve/relabel farmer uploaded image as verified training data.

### `POST /admin/ai/train`

Queue a model training job.

```json
{ "dataset_version": "2026-06-30", "base_model": "convnext_tiny", "epochs": 30, "batch_size": 64 }
```

### `POST /admin/blogs`

Publish advisory content.

## Farmer AI training contribution

### `POST /training/farmer-images`

Multipart form from mobile **Train AI** tab:

- `image`: jpg/png/webp
- `pest_id`: selected pest label
- `stage`: lifecycle stage, e.g. `adult`, `nymph/larva`
- `note`: optional farmer note

The image is saved as **unverified** and must be approved from admin before use in training.

### `GET /training/my-submissions`

Returns the farmer's submitted AI training images and review status.

### `GET /admin/training-images/pending`

Admin list of unverified mobile training submissions.

### `POST /admin/training-images/{training_image_id}/verify`

Admin verifies/corrects pest label and lifecycle stage before the image is included in training.

## Profile update

### `PATCH /auth/me`

Update farmer profile and farm details:

```json
{
  "name": "Farmer Name",
  "village": "Village",
  "district": "District",
  "state": "State",
  "acres_land": 5.5,
  "plants": "Orange, lemon",
  "citrus_varieties": "Nagpur orange",
  "irrigation_type": "drip",
  "farming_experience_years": 8
}
```

## Detection detail and admin correction

### `GET /detections/{id}`

Farmer can view full saved detection result, pest management details and admin correction status.

### `PATCH /admin/detections/{id}`

Admin/agronomist can correct AI result:

```json
{
  "pest_id": "citrus-psyllid",
  "predicted_name": "Asian Citrus Psyllid",
  "confidence": 0.98,
  "stage": "adult",
  "admin_status": "corrected",
  "admin_note": "Corrected after expert review"
}
```

### `GET /admin/ai/free-models`

Lists free/open-source base models available for transfer learning.

### `POST /admin/calendar`

Create/update a month in the citrus year calendar.

## Admin route-based modules added

### Users and farmers

```http
GET /admin/users
GET /admin/farmers
POST /admin/users
POST /admin/users/{user_id}/reset-password
```

### Blog CRUD and assets

```http
GET /admin/blogs
POST /admin/blogs
PATCH /admin/blogs/{id}
DELETE /admin/blogs/{id}
POST /admin/assets
```

### Events

```http
GET /admin/events
POST /admin/events
PATCH /admin/events/{id}
DELETE /admin/events/{id}
GET /events
```

### Chat

```http
GET /chat/conversations
POST /chat/conversations
GET /chat/conversations/{id}/messages
POST /chat/conversations/{id}/messages
GET /admin/chats
GET /admin/chats/{id}/messages
POST /admin/chats/{id}/messages
```

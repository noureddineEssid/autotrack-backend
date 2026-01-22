# API Documentation - AutoTrack Backend

## Base URL
```
http://127.0.0.1:8000/api/
```

## Authentication
All API endpoints (except public ones) require JWT authentication.

### Headers
```
Authorization: Bearer <access_token>
```

## API Endpoints

### Authentication (`/api/auth/`)

#### POST `/api/auth/register/`
Register a new user.
```json
{
  "email": "user@example.com",
  "password": "password123",
  "first_name": "John",
  "last_name": "Doe"
}
```

#### POST `/api/auth/login/`
Login and get JWT tokens.
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```
Response:
```json
{
  "access": "eyJ0eXAiOiJKV1...",
  "refresh": "eyJ0eXAiOiJKV1...",
  "user": {...}
}
```

#### POST `/api/auth/logout/`
Logout (requires authentication).

#### GET `/api/auth/me/`
Get current user profile.

#### PUT `/api/auth/change-password/`
Change user password.

#### GET `/api/auth/sessions/`
Get user sessions.

#### POST `/api/token/refresh/`
Refresh access token.

---

### Vehicles (`/api/vehicles/`)

#### GET `/api/vehicles/`
List all user's vehicles.
- Filters: `make`, `model`, `year`, `fuel_type`
- Search: `make`, `model`, `vin`, `license_plate`
- Ordering: `year`, `created_at`

#### POST `/api/vehicles/`
Create a new vehicle.

#### GET `/api/vehicles/{id}/`
Get vehicle details.

#### PUT/PATCH `/api/vehicles/{id}/`
Update vehicle.

#### DELETE `/api/vehicles/{id}/`
Delete vehicle.

#### GET `/api/vehicles/stats/`
Get user's vehicles statistics.

#### GET `/api/vehicles/{id}/maintenances/`
Get all maintenances for a vehicle.

#### GET `/api/vehicles/{id}/documents/`
Get all documents for a vehicle.

#### GET `/api/vehicles/{id}/diagnostics/`
Get all diagnostics for a vehicle.

---

### Maintenances (`/api/maintenances/`)

#### GET `/api/maintenances/`
List all user's maintenances.
- Filters: `vehicle`, `status`, `service_type`
- Search: `service_type`, `description`, vehicle info
- Ordering: `service_date`, `cost`, `mileage`

#### POST `/api/maintenances/`
Create a new maintenance record.

#### GET `/api/maintenances/{id}/`
Get maintenance details.

#### PUT/PATCH `/api/maintenances/{id}/`
Update maintenance.

#### DELETE `/api/maintenances/{id}/`
Delete maintenance.

#### GET `/api/maintenances/upcoming/`
Get upcoming scheduled maintenances.

#### GET `/api/maintenances/recent/`
Get recent completed maintenances (last 30 days).

#### GET `/api/maintenances/stats/`
Get maintenance statistics.

#### GET `/api/maintenances/by_vehicle/`
Get maintenances grouped by vehicle.

---

### Garages (`/api/garages/`)

#### GET `/api/garages/`
List all garages (public).
- Filters: `city`, `postal_code`, `country`
- Search: `name`, `address`, `city`, `specialties`
- Ordering: `name`, `average_rating`, `total_reviews`

#### POST `/api/garages/`
Create a new garage (requires auth).

#### GET `/api/garages/{id}/`
Get garage details with reviews.

#### PUT/PATCH `/api/garages/{id}/`
Update garage.

#### DELETE `/api/garages/{id}/`
Delete garage.

#### POST `/api/garages/{id}/add_review/`
Add a review to a garage.

#### GET `/api/garages/top_rated/`
Get top rated garages.
- Query params: `limit` (default: 10)

#### GET `/api/garages/search_nearby/`
Search garages nearby.
- Query params: `lat`, `lng`, `radius` (km, default: 10)

#### GET `/api/garages/by_specialty/`
Get garages by specialty.
- Query params: `specialty`

---

### Garage Reviews (`/api/garages/reviews/`)

#### GET `/api/garages/reviews/`
List all reviews (public).
- Filters: `garage`, `rating`
- Ordering: `rating`, `created_at`

#### POST `/api/garages/reviews/`
Create a new review.

---

### Diagnostics (`/api/diagnostics/`)

#### GET `/api/diagnostics/`
List all user's diagnostics.
- Filters: `vehicle`, `status`
- Search: `title`, `description`, vehicle info
- Ordering: `created_at`

#### POST `/api/diagnostics/`
Create a new diagnostic.

#### GET `/api/diagnostics/{id}/`
Get diagnostic details with replies.

#### PUT/PATCH `/api/diagnostics/{id}/`
Update diagnostic.

#### DELETE `/api/diagnostics/{id}/`
Delete diagnostic.

#### POST `/api/diagnostics/{id}/add_reply/`
Add a reply to a diagnostic.

#### POST `/api/diagnostics/{id}/request_ai_analysis/`
Request AI analysis for a diagnostic.

#### GET `/api/diagnostics/by_severity/`
Get diagnostics by severity.

#### GET `/api/diagnostics/pending/`
Get pending diagnostics.

#### GET `/api/diagnostics/resolved/`
Get resolved diagnostics.

#### GET `/api/diagnostics/stats/`
Get diagnostic statistics.

#### GET `/api/diagnostics/by_vehicle/`
Get diagnostics grouped by vehicle.

---

### Diagnostic Replies (`/api/diagnostics/replies/`)

#### GET `/api/diagnostics/replies/`
List all replies for user's diagnostics.
- Filters: `diagnostic`, `sender_type`
- Ordering: `created_at`

#### POST `/api/diagnostics/replies/`
Create a new reply.

---

### Documents (`/api/documents/`)

#### GET `/api/documents/`
List all user's documents.
- Filters: `vehicle`, `document_type`
- Search: `title`, `description`, vehicle info
- Ordering: `created_at`, `file_size`

#### POST `/api/documents/`
Upload a new document (multipart/form-data).

#### GET `/api/documents/{id}/`
Get document details.

#### PUT/PATCH `/api/documents/{id}/`
Update document.

#### DELETE `/api/documents/{id}/`
Delete document.

#### GET `/api/documents/by_type/`
Get documents by type.
- Query params: `type`

#### GET `/api/documents/expiring_soon/`
Get documents expiring soon.
- Query params: `days` (default: 30)

#### GET `/api/documents/expired/`
Get expired documents.

#### GET `/api/documents/stats/`
Get document statistics.

#### GET `/api/documents/by_vehicle/`
Get documents grouped by vehicle.

#### POST `/api/documents/{id}/reprocess_ocr/`
Reprocess OCR for a document.

---

### Notifications (`/api/notifications/`)

#### GET `/api/notifications/`
List all user's notifications.
- Filters: `notification_type`, `is_read`
- Search: `title`, `message`
- Ordering: `created_at`, `read_at`

#### POST `/api/notifications/`
Create a new notification.

#### GET `/api/notifications/{id}/`
Get notification details.

#### PUT/PATCH `/api/notifications/{id}/`
Update notification (mark as read).

#### DELETE `/api/notifications/{id}/`
Delete notification.

#### GET `/api/notifications/unread/`
Get unread notifications.

#### GET `/api/notifications/unread_count/`
Get count of unread notifications.

#### POST `/api/notifications/{id}/mark_as_read/`
Mark notification as read.

#### POST `/api/notifications/{id}/mark_as_unread/`
Mark notification as unread.

#### POST `/api/notifications/mark_all_as_read/`
Mark all notifications as read.

#### DELETE `/api/notifications/delete_all_read/`
Delete all read notifications.

#### GET `/api/notifications/by_type/`
Get notifications by type.

#### GET `/api/notifications/stats/`
Get notification statistics.

---

### Plans (`/api/plans/`)

#### GET `/api/plans/`
List all active subscription plans (public).
- Filters: `interval`, `is_active`
- Search: `name`, `description`
- Ordering: `price`, `created_at`

#### POST `/api/plans/`
Create a new plan (admin only).

#### GET `/api/plans/{id}/`
Get plan details.

#### PUT/PATCH `/api/plans/{id}/`
Update plan (admin only).

#### DELETE `/api/plans/{id}/`
Delete plan (admin only).

#### GET `/api/plans/active_plans/`
Get all active plans.

#### GET `/api/plans/by_period/`
Get plans by billing period.
- Query params: `period` (month/year)

#### GET `/api/plans/popular/`
Get popular plans (with trial).

---

### Subscriptions (`/api/subscriptions/`)

#### GET `/api/subscriptions/`
List user's subscriptions.
- Filters: `status`, `plan`, `cancel_at_period_end`
- Ordering: `created_at`, `current_period_end`

#### POST `/api/subscriptions/`
Create a new subscription.

#### GET `/api/subscriptions/{id}/`
Get subscription details.

#### PUT/PATCH `/api/subscriptions/{id}/`
Update subscription.

#### DELETE `/api/subscriptions/{id}/`
Delete subscription.

#### GET `/api/subscriptions/active/`
Get current active subscription.

#### POST `/api/subscriptions/{id}/cancel/`
Cancel subscription at period end.

#### POST `/api/subscriptions/{id}/reactivate/`
Reactivate a cancelled subscription.

#### POST `/api/subscriptions/{id}/change_plan/`
Change subscription plan.
```json
{
  "plan_id": 1
}
```

#### GET `/api/subscriptions/stats/`
Get subscription statistics (admin only).

---

### Webhooks (`/api/webhooks/`)

#### GET `/api/webhooks/events/`
List all webhook events (admin only).
- Filters: `event_type`, `source`, `processed`
- Ordering: `created_at`

#### GET `/api/webhooks/events/{id}/`
Get webhook event details.

#### GET `/api/webhooks/events/unprocessed/`
Get unprocessed webhook events.

#### GET `/api/webhooks/events/errors/`
Get webhook events with errors.

#### POST `/api/webhooks/stripe/`
Stripe webhook endpoint (public - used by Stripe).

---

### Settings (`/api/settings/`)

#### GET `/api/settings/settings/`
List user's settings (returns single object).

#### GET `/api/settings/settings/me/`
Get current user's settings.

#### PUT/PATCH `/api/settings/settings/update_me/`
Update current user's settings.

#### POST `/api/settings/settings/reset/`
Reset settings to default.

---

### AI Assistant (`/api/ai_assistant/`)

#### GET `/api/ai_assistant/conversations/`
List user's AI conversations.
- Ordering: `updated_at`

#### POST `/api/ai_assistant/conversations/`
Create a new conversation.

#### GET `/api/ai_assistant/conversations/{id}/`
Get conversation details with messages.

#### PUT/PATCH `/api/ai_assistant/conversations/{id}/`
Update conversation.

#### DELETE `/api/ai_assistant/conversations/{id}/`
Delete conversation.

#### POST `/api/ai_assistant/conversations/{id}/send_message/`
Send a message in a conversation.
```json
{
  "content": "What's wrong with my car?"
}
```

#### GET `/api/ai_assistant/conversations/{id}/messages/`
Get all messages in a conversation.

#### GET `/api/ai_assistant/conversations/recent/`
Get recent conversations.
- Query params: `limit` (default: 10)

#### GET `/api/ai_assistant/conversations/stats/`
Get conversation statistics.

---

## Error Responses

### 400 Bad Request
```json
{
  "field_name": ["Error message"]
}
```

### 401 Unauthorized
```json
{
  "detail": "Authentication credentials were not provided."
}
```

### 403 Forbidden
```json
{
  "detail": "You do not have permission to perform this action."
}
```

### 404 Not Found
```json
{
  "detail": "Not found."
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error."
}
```

---

## Pagination

List endpoints use cursor pagination:

```json
{
  "count": 100,
  "next": "http://api.example.com/api/vehicles/?cursor=cD0yMDIz",
  "previous": null,
  "results": [...]
}
```

---

## Notes

1. **File Uploads**: Use `multipart/form-data` for document uploads
2. **Date Format**: ISO 8601 format (`YYYY-MM-DD` or `YYYY-MM-DDTHH:MM:SSZ`)
3. **Filtering**: Combine multiple filters with `&` (e.g., `?status=active&year=2023`)
4. **Ordering**: Use `-` prefix for descending order (e.g., `?ordering=-created_at`)
5. **Stripe Webhooks**: Configured to receive Stripe events at `/api/webhooks/stripe/`
6. **AI Features**: Currently return placeholder responses (TODO: integrate OpenAI)
7. **OCR Processing**: Currently placeholder (TODO: integrate Tesseract/OCR service)
8. **Celery Tasks**: Background task processing configured but not yet implemented

---

## TODO: Features to Implement

1. **Stripe Integration**: Complete payment processing
2. **OpenAI Integration**: Implement AI diagnostic analysis
3. **OCR Processing**: Implement document text extraction
4. **Email Service**: Send notifications via email
5. **Celery Tasks**: Implement background job processing
6. **Unit Tests**: Add comprehensive test coverage
7. **API Documentation**: Add Swagger/OpenAPI documentation
8. **Rate Limiting**: Implement API rate limiting
9. **WebSocket Support**: Real-time notifications
10. **Search Optimization**: Implement Elasticsearch for better search

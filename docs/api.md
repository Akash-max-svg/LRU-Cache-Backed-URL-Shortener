# REST API Reference Documentation

All endpoints return JSON responses (except the short URL redirect which returns HTTP 302).

Base URL: `http://localhost:5000`

---

## 1. Health Check

Verifies server and database availability.

* **Endpoint**: `GET /api/health`
* **Response**: `200 OK`
```json
{
  "status": "healthy",
  "database": "connected",
  "cache": "operational"
}
```

---

## 2. Shorten URL

Creates a new Base62 short URL or returns the existing short code if the same active URL was previously shortened.

* **Endpoint**: `POST /api/shorten`
* **Headers**: `Content-Type: application/json`
* **Request Body**:
```json
{
  "url": "https://www.example.com/products/electronics/iphone-16",
  "expires_in": 86400
}
```
*Note: `expires_in` is optional (TTL in seconds). Supported options: 3600 (1 hour), 86400 (1 day), 604800 (7 days), or null/omitted for permanent.*

* **Response (New URL Created)**: `201 Created`
```json
{
  "success": true,
  "short_code": "aB72xK",
  "short_url": "http://localhost:5000/aB72xK",
  "original_url": "https://www.example.com/products/electronics/iphone-16",
  "expires_at": "2026-09-30T10:00:00+00:00"
}
```

* **Response (Duplicate Detected)**: `200 OK`
```json
{
  "success": true,
  "short_code": "aB72xK",
  "short_url": "http://localhost:5000/aB72xK",
  "original_url": "https://www.example.com/products/electronics/iphone-16",
  "is_duplicate": true
}
```

* **Error Responses**:
  - `400 Bad Request` (Missing URL, invalid scheme, excessively long):
    ```json
    { "success": false, "error": "URL missing scheme. Must start with http:// or https://" }
    ```

---

## 3. Redirect Short URL

Resolves a short code and redirects to the target destination via Cache-Aside resolution.

* **Endpoint**: `GET /<short_code>`
* **Example**: `GET /aB72xK`
* **Behavior**:
  - Checks LRU cache $\rightarrow$ If hit: immediate redirect.
  - If miss: fetches from MongoDB $\rightarrow$ adds to LRU cache $\rightarrow$ redirect.
  - Increments `click_count` and updates `last_accessed` timestamp.
* **Success Response**: `302 Found`
  - Header: `Location: https://www.example.com/...`
* **Error Responses**:
  - `404 Not Found` (Code does not exist or deleted):
    ```json
    { "success": false, "error": "Short URL not found" }
    ```
  - `410 Gone` (URL has expired):
    ```json
    { "success": false, "error": "URL has expired" }
    ```

---

## 4. Get URL Metadata

Fetches complete analytics and status details for a short code.

* **Endpoint**: `GET /api/url/<short_code>`
* **Response**: `200 OK`
```json
{
  "success": true,
  "short_code": "aB72xK",
  "short_url": "http://localhost:5000/aB72xK",
  "original_url": "https://www.example.com/products",
  "click_count": 42,
  "created_at": "2026-09-29T10:00:00+00:00",
  "expires_at": null,
  "last_accessed": "2026-09-29T14:15:30+00:00",
  "is_active": true
}
```

---

## 5. Delete Short URL

Removes a shortened URL from MongoDB and evicts it immediately from the LRU Cache.

* **Endpoint**: `DELETE /api/url/<short_code>`
* **Response**: `200 OK`
```json
{
  "success": true,
  "message": "URL deleted successfully"
}
```
* **Error Response**:
  - `404 Not Found` if code does not exist.

---

## 6. Cache Statistics

Returns real-time performance indicators from the custom LRU Cache.

* **Endpoint**: `GET /api/cache/stats`
* **Response**: `200 OK`
```json
{
  "capacity": 100,
  "current_size": 15,
  "total_requests": 500,
  "hits": 420,
  "misses": 80,
  "hit_rate": 84.0
}
```

---

## 7. System Analytics

Aggregates overall database and cache usage numbers.

* **Endpoint**: `GET /api/analytics`
* **Response**: `200 OK`
```json
{
  "total_urls": 125,
  "total_clicks": 1420,
  "cache_hits": 1180,
  "cache_misses": 240,
  "cache_hit_rate": 83.1,
  "cache_capacity": 100,
  "current_cache_size": 45,
  "database_type": "MongoDB Live"
}
```

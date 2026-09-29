# System Architecture Specification

## 1. Architectural Overview

The **Simple LRU Cache-Backed URL Shortener** is designed following a modular, layered architecture adhering strictly to **Separation of Concerns (SoC)** and the **Cache-Aside (Lazy Loading)** design pattern.

```text
┌────────────────────────────────────────────────────────┐
│                   Client Layer                         │
│   Web Browser (HTML5 / Vanilla JS)  |  REST Consumers  │
└───────────────────────────┬────────────────────────────┘
                            │ HTTP Requests
                            ▼
┌────────────────────────────────────────────────────────┐
│                   Flask API Layer                      │
│             routes/url_routes.py                       │
│  - Request Validation    - HTTP Response Mapping       │
│  - CORS Management       - Error Handling              │
└───────────────────────────┬────────────────────────────┘
                            │ Calls
                            ▼
┌────────────────────────────────────────────────────────┐
│                  Service Layer                         │
│  - services/url_service.py       (Shortening & Resolv) │
│  - services/hash_service.py      (Base62 & SHA-256)    │
│  - services/analytics_service.py (Metrics Aggregation) │
└─────────────┬───────────────────────────┬──────────────┘
              │                           │
       Cache Lookup (O(1))         DB Fallback (O(log N))
              ▼                           ▼
┌───────────────────────────┐ ┌──────────────────────────┐
│     Custom LRU Cache      │ │     MongoDB Database     │
│  cache/lru_cache.py       │ │  database/mongodb.py     │
│  - HashMap                │ │  - Collection: urls      │
│  - Doubly Linked List     │ │  - Unique short_code idx │
│  - In-memory O(1) ops     │ │  - SHA-256 url_hash idx  │
└───────────────────────────┘ └──────────────────────────┘
```

---

## 2. Layer Responsibilities

### 2.1 Presentation & Client Layer (`templates/`, `static/`)
- Responsive HTML5 user interface with Vanilla JavaScript (`fetch()` API).
- Real-time LRU cache queue visualizer demonstrating MRU-to-LRU node positions.
- Live analytics charts and interactive URL management actions.

### 2.2 Controller & Routing Layer (`routes/`)
- Exposes clean REST API endpoints (`/api/shorten`, `/api/cache/stats`, etc.).
- Directs traffic from `/<short_code>` to original destinations using HTTP 302 redirects.
- Translates business exceptions into standard HTTP status codes (`200`, `201`, `400`, `404`, `410`, `500`).

### 2.3 Business Domain Layer (`services/`)
- **`URLService`**: Orchestrates duplicate detection, short-code generation, cache population, database writes, and TTL expiration checks.
- **`HashService`**: Pure functions for Base62 encoding/decoding and SHA-256 URL hashing.
- **`AnalyticsService`**: Calculates system-wide metrics, cache hit rate ratios, and gathers recent URL history.

### 2.4 Caching Layer (`cache/`)
- Custom Python implementation of an LRU cache.
- Internal HashMap (`dict`) holding pointers to `Node` elements in a Doubly Linked List.
- Sentinel dummy nodes (`HEAD` and `TAIL`) simplify edge-case pointer rewiring.
- Uses `threading.RLock()` to ensure thread-safety across concurrent Flask worker threads.

### 2.5 Persistence Layer (`database/`)
- PyMongo client connecting to MongoDB server.
- Supports MongoDB Atlas, local MongoDB Community Server, and automated fallback to in-memory `mongomock` for testing and evaluation environments.
- Maintains automated unique index on `short_code` and lookup index on `url_hash`.

---

## 3. Redirection Sequence: Cache HIT vs. Cache MISS

### 3.1 Cache HIT Workflow
```text
User Accesses: GET /aB72xK
  1. Flask receives request.
  2. URLService executes `lru_cache.get("aB72xK")`.
  3. Hash Map finds Node in O(1) time.
  4. Node is unlinked and moved to the front (MRU, behind HEAD).
  5. Cache hit counter increments: `hits += 1`.
  6. Expiration verified (not expired).
  7. Async/DB click counter incremented.
  8. Return HTTP 302 Redirect to original target.
Latency: ~0.5 microseconds (in-memory pointer operation).
```

### 3.2 Cache MISS Workflow
```text
User Accesses: GET /aB72xK (Cold Cache or Evicted)
  1. Flask receives request.
  2. URLService executes `lru_cache.get("aB72xK")`.
  3. Hash Map returns `None`.
  4. Cache miss counter increments: `misses += 1`.
  5. URLService queries MongoDB collection: `urls.find_one({"short_code": "aB72xK"})`.
  6. Document found in MongoDB index.
  7. Expiration verified.
  8. Document inserted into LRU Cache: `lru_cache.put("aB72xK", doc)`.
  9. Click count incremented in DB.
 10. Return HTTP 302 Redirect to original target.
Latency: ~150-500 microseconds (includes DB query overhead).
Subsequent requests for "aB72xK" are now immediate Cache HITs!
```

---

## 4. Concurrency & Thread-Safety

Web servers often handle simultaneous requests across multiple worker threads. The custom `LRUCache` guarantees thread-safety through Python's `threading.RLock()`:
```python
with self._lock:
    # All pointer rewiring and map updates are atomic
```
This prevents pointer corruption (such as circular references or lost nodes) when multiple requests trigger simultaneous cache updates or evictions.

# Simple LRU Cache-Backed URL Shortener

A high-performance, production-style URL shortening system built with **Python 3.11+**, **Flask**, and **MongoDB**, featuring a custom **HashMap + Doubly Linked List LRU (Least Recently Used) Cache** engineered from scratch.

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.1-000000?style=flat&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![MongoDB](https://img.shields.io/badge/MongoDB-Persistent-47A248?style=flat&logo=mongodb&logoColor=white)](https://mongodb.com)
[![Pytest](https://img.shields.io/badge/Tests-28%20Passed-brightgreen?style=flat&logo=pytest&logoColor=white)](https://pytest.org)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

---

## 1. Project Title
**Simple LRU Cache-Backed URL Shortener (CacheSnap)**

---

## 2. Project Description
A full-stack, modular web application that converts long URLs into compact, collision-resistant Base62 short links. The system employs the **Cache-Aside (Lazy Loading)** design pattern: when a shortened URL is visited, the system first inspects a custom in-memory LRU Cache. If found (**Cache HIT**), the client is immediately redirected in $O(1)$ time without database round-trips. If absent (**Cache MISS**), the mapping is fetched from persistent MongoDB storage, loaded into the LRU Cache, and then redirected.

---

## 3. Problem Statement
High-traffic URL redirection services encounter millions of read requests per second. Repeatedly querying disk-based databases for hot URLs introduces latency, network bottlenecks, and high database connection pool strain. 

By introducing an in-memory **Least Recently Used (LRU) Cache** with strict $O(1)$ access and eviction bounds, the system minimizes database I/O while guaranteeing that frequently accessed URLs resolve with sub-microsecond latency.

---

## 4. Objectives
- Accept long URLs and validate against web standards and security constraints.
- Generate compact, collision-resistant Base62 short codes.
- Implement an in-memory LRU Cache using a **HashMap** and **Doubly Linked List** without third-party caching libraries.
- Persist URL documents permanently in **MongoDB** with unique and compound indexing.
- Implement automated duplicate URL detection via **SHA-256 fingerprinting**.
- Support optional URL expiration (TTL) and dynamic deletion.
- Provide a clean, glassmorphic responsive frontend and complete REST APIs.
- Provide comprehensive test coverage with **pytest**.

---

## 5. Features
- ⚡ **Custom LRU Cache**: Implements $O(1)$ `get()`, `put()`, `remove()` operations with configurable capacity.
- 🔁 **Base62 Short Codes**: Compact 6-character alphanumeric identifiers (`0-9`, `a-z`, `A-Z`).
- 🛡️ **SHA-256 Duplicate Detection**: Prevents duplicate database records for identical URLs.
- ⏱️ **URL Expiration (TTL)**: Optional expiration (1 Hour, 1 Day, 7 Days, or Permanent).
- 📊 **Real-time Analytics**: Tracks cache hits, misses, hit rate percentage, and total visits.
- 🔄 **Cache Visualizer**: Dynamic visual representation of LRU cache nodes from MRU (head) to LRU (tail).
- 🗑️ **URL Deletion**: Instantly removes records from MongoDB and evicts them from the cache.
- 📱 **Modern Responsive UI**: Dark glassmorphic styling built with Vanilla HTML5, CSS3, and JavaScript.

---

## 6. Technology Stack
- **Backend**: Python 3.11+, Flask 3.1+, PyMongo, python-dotenv, Werkzeug, Flask-CORS
- **Database**: MongoDB (supports local MongoDB, MongoDB Atlas, and automatic fallback)
- **Frontend**: HTML5, Vanilla CSS3 (Glassmorphism & CSS Grid), Vanilla JavaScript (ES6+ `fetch`)
- **Testing**: pytest (28 comprehensive unit & integration tests)

---

## 7. System Architecture

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

## 8. Project Structure

```text
pythonproject/
│
├── app.py                     # Main application entry point & factory
├── config.py                  # Environment-based configuration
├── requirements.txt           # Python package dependencies
├── benchmark.py               # Performance benchmarking script
├── pytest.ini                 # Pytest discovery configuration
├── .env                       # Environment variables
├── .env.example               # Template environment configuration
├── .gitignore                 # Git ignore rules
├── README.md                  # Complete project documentation
│
├── cache/                     # Core Data Structure Implementation
│   ├── __init__.py
│   ├── node.py                # Doubly Linked List Node
│   └── lru_cache.py           # HashMap + Doubly Linked List LRU Cache
│
├── database/                  # Persistence Layer
│   ├── __init__.py
│   └── mongodb.py             # MongoDB connection & index initialization
│
├── models/                    # Data Entities
│   ├── __init__.py
│   └── url_model.py           # URL document representation
│
├── services/                  # Business Logic Layer
│   ├── __init__.py
│   ├── url_service.py         # URL shortening & Cache-Aside redirection
│   ├── hash_service.py        # Base62 encoding & SHA-256 hashing
│   └── analytics_service.py   # Metrics and statistics computation
│
├── routes/                    # Web & REST API Controllers
│   ├── __init__.py
│   └── url_routes.py          # Flask route definitions
│
├── utils/                     # Utility Modules
│   ├── __init__.py
│   └── validators.py          # RFC-compliant URL & short code validation
│
├── templates/                 # Jinja2 HTML5 Templates
│   ├── index.html             # Main shortening interface
│   ├── analytics.html         # Real-time analytics dashboard
│   └── error.html             # Friendly error & 404/410 page
│
├── static/                    # Frontend Assets
│   ├── css/
│   │   └── style.css          # Glassmorphic dark theme stylesheet
│   └── js/
│       ├── app.js             # Shortener client logic
│       └── analytics.js       # Analytics dashboard & cache visualizer logic
│
├── tests/                     # Unit and Integration Tests
│   ├── test_lru_cache.py      # LRU Cache algorithm tests
│   ├── test_hash_service.py   # Base62 & SHA-256 tests
│   ├── test_validators.py     # URL validation tests
│   └── test_api.py            # Flask API & Cache-Aside flow tests
│
└── docs/                      # Technical Documentation
    ├── architecture.md        # System design & sequence flows
    ├── api.md                 # Complete REST API reference
    └── algorithms.md          # Algorithmic complexity & data structures
```

---

## 9. LRU Cache Explanation

The cache is constructed using **two classical data structures**:
1. **Hash Map (`dict`)**: Maps `short_code` $\rightarrow$ `Node` reference for $O(1)$ lookup time.
2. **Doubly Linked List**: Maintains access order with dummy `HEAD` and `TAIL` sentinel nodes:
   - `HEAD.next` points to the **Most Recently Used (MRU)** node.
   - `TAIL.prev` points to the **Least Recently Used (LRU)** node.

```text
                 Hash Map
              ┌───────────┐
   "aB72xK" ──┼───────────┼──┐
              └───────────┘  │
                             ▼
   [HEAD] ⇄ [ Node: aB72xK ] ⇄ [ Node: mN49eQ ] ⇄ [ Node: z8Wq2A ] ⇄ [TAIL]
 (Sentinel)       (MRU)                                  (LRU)      (Sentinel)
```

- When an item is accessed via `get(key)`: The node is unlinked in $O(1)$ time and moved right behind `HEAD`.
- When an item is added via `put(key, value)`: A node is inserted behind `HEAD`. If capacity is exceeded, `TAIL.prev` is unlinked and deleted from the hash map in $O(1)$ time.

---

## 10. Hashing & Encoding Explanation

- **Base62 Encoding**:
  Converts high-resolution 64-bit integer timestamps and entropy into a 62-character radix (`0-9`, `a-z`, `A-Z`). 6 characters yield $62^6 \approx 56.8 \text{ billion}$ distinct URL codes without special characters.
- **SHA-256 Hashing**:
  Produces a deterministic 64-character hexadecimal digest. When a user enters a URL, the system calculates its SHA-256 hash. If an active document with that hash already exists, the system returns the existing short code rather than creating duplicate records.

---

## 11. Database Design

- **Database Name**: `url_shortener`
- **Collection**: `urls`

### Document Schema
```json
{
  "_id": "ObjectId('...')",
  "short_code": "aB72xK",
  "original_url": "https://www.example.com/products/iphone",
  "url_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "created_at": "2026-09-29T10:00:00+00:00",
  "expires_at": null,
  "click_count": 42,
  "last_accessed": "2026-09-29T14:30:00+00:00",
  "is_active": true
}
```

### Indexes
1. `short_code` (Unique ASCENDING) $\rightarrow$ Ensures fast $O(\log N)$ document retrieval and enforces uniqueness.
2. `url_hash` (ASCENDING) $\rightarrow$ Enables instant duplicate URL detection.
3. `(url_hash, is_active)` (Compound) $\rightarrow$ Filters active duplicates.

---

## 12. API Documentation Summary

| Method | Endpoint | Description | Status Codes |
|---|---|---|---|
| `POST` | `/api/shorten` | Shorten a long URL | `201`, `200`, `400`, `500` |
| `GET` | `/<short_code>` | Redirect to original URL | `302`, `404`, `410` |
| `GET` | `/api/url/<short_code>` | Fetch URL metadata | `200`, `404`, `410` |
| `DELETE` | `/api/url/<short_code>` | Delete URL from DB & Cache | `200`, `400`, `404` |
| `GET` | `/api/cache/stats` | Retrieve LRU Cache statistics | `200` |
| `GET` | `/api/analytics` | Retrieve system analytics | `200` |
| `GET` | `/api/health` | Health check endpoint | `200` |

*Full API documentation is available in [docs/api.md](docs/api.md).*

---

## 13. Installation

### Prerequisites
- Python 3.11 or higher
- Git

### Clone Repository & Setup
```bash
git clone https://github.com/your-username/url-shortener.git
cd url-shortener
```

### Create and Activate Virtual Environment
On Windows:
```powershell
python -m venv venv
.\venv\Scripts\activate
```
On Linux / macOS:
```bash
python3 -m venv venv
source venv/bin/activate
```

### Install Dependencies
```bash
pip install -r requirements.txt
```

---

## 14. Environment Setup

Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

Configuration parameters:
```env
MONGO_URI=mongodb://localhost:27017
DATABASE_NAME=url_shortener
CACHE_CAPACITY=100
BASE_URL=http://localhost:5000
FLASK_ENV=development
PORT=5000
SECRET_KEY=development-secret-key-change-in-production
```

---

## 15. Running the Project

Start the application with:
```bash
python app.py
```

The application will be live at:
- **Home (Shortener)**: [http://localhost:5000](http://localhost:5000)
- **Analytics Dashboard**: [http://localhost:5000/analytics](http://localhost:5000/analytics)

---

## 16. Testing

Run the complete test suite with **pytest**:
```bash
pytest -v
```

All 28 tests cover:
- LRU `get()` and `put()`
- LRU eviction ordering (capacity boundary)
- Cache HIT and MISS tracking
- Hit rate formula calculation
- Base62 encoding and decoding
- SHA-256 deterministic fingerprinting
- URL schema and security validation
- End-to-end Cache-Aside redirection flow
- Duplicate URL reuse
- URL TTL expiration
- URL deletion

---

## 17. Complexity Analysis

| Component | Operation | Time Complexity | Space Complexity |
|---|---|---|---|
| **LRU Cache** | `get(key)` | $O(1)$ | $O(1)$ |
| **LRU Cache** | `put(key, value)` | $O(1)$ | $O(1)$ |
| **LRU Cache** | `remove(key)` | $O(1)$ | $O(1)$ |
| **LRU Cache** | Eviction | $O(1)$ | $O(1)$ |
| **HashService** | Base62 Encode | $O(\log_{62} N) \approx O(1)$ | $O(1)$ |
| **HashService** | SHA-256 Hash | $O(L) \approx O(1)$ | $O(1)$ |
| **MongoDB** | Lookup by `short_code` | $O(\log N)$ (Indexed B-Tree) | $O(1)$ |

### Benchmark Results
Run the benchmark script:
```bash
python benchmark.py
```
Observed lookup latency:
- **LRU Cache Lookup**: $\approx 0.54\,\mu\text{s}$ ($0.00054\,\text{ms}$)
- **Database Query Lookup**: $\approx 152\,\mu\text{s}$ ($0.15295\,\text{ms}$)
- **Speedup**: Over **$280\times$ faster** using the custom in-memory LRU Cache.

---

## 18. Demonstration Guide

1. **Shorten URL**: Enter `https://www.example.com/products/iphone` and click **Shorten URL**. Receive short URL `http://localhost:5000/aB72xK`.
2. **First Visit (Cold Cache / MISS)**: Navigate to `http://localhost:5000/aB72xK`. The system misses cache, fetches from MongoDB, warms cache, and redirects.
3. **Second Visit (Warm Cache / HIT)**: Navigate to `http://localhost:5000/aB72xK` again. The system immediately hits the LRU cache and redirects with sub-microsecond response.
4. **Analytics**: Open `/analytics` to see live Cache Hits, Misses, Hit Rate %, and the visual ordering of nodes in the cache!

---

## 19. Future Enhancements
- User authentication and custom aliases (vanity URLs)
- Dynamic QR code generation for shortened links
- Distributed caching layer (Redis / Memcached for multi-instance clusters)
- Geographic visitor analytics and referrer tracking
- Token bucket rate limiting per IP address

---

## 20. Author
Built as a demonstration of Object-Oriented Programming, Data Structures & Algorithms, and modern web application development.

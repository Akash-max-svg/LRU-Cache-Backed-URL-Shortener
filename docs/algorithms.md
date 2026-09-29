# Algorithmic Complexity and Data Structures Specification

This document details the core algorithms, mathematical foundations, and data structures utilized in the **Simple LRU Cache-Backed URL Shortener**.

---

## Algorithm 1: URL Validation

### Overview
Validates incoming web addresses to prevent injection attacks, SSRF, malformed URLs, and non-routable resource schemes.

* **Input**: Raw string `url` submitted by client.
* **Process**:
  1. Strip leading and trailing whitespace.
  2. Verify string is non-empty and does not exceed maximum length ($2048$ characters).
  3. Pre-filter dangerous schemes like `javascript:`, `data:`, `file:`.
  4. Parse URL using RFC-3986 parser (`urllib.parse.urlparse`).
  5. Validate scheme against whitelist (`{'http', 'https'}`).
  6. Validate host exists and has valid domain structure (or is `localhost`).
* **Output**: Tuple `(is_valid: bool, error_message: str | None)`.
* **Time Complexity**: $O(L)$ where $L$ is the length of the URL string ($L \le 2048$, hence effectively $O(1)$).
* **Space Complexity**: $O(L)$ to store parsed URL components.

---

## Algorithm 2: SHA-256 URL Hashing & Duplicate Detection

### Overview
Generates a cryptographic 256-bit fingerprint for each normalized URL string. Used as a database lookup index to identify duplicate URL shortening attempts in $O(1)$ time.

* **Input**: Normalized URL string `url`.
* **Process**:
  1. Encode the UTF-8 string into byte array.
  2. Process bytes through the NIST-standard SHA-256 compression function (Merkl-Damgård construction).
  3. Output the 64-character hexadecimal digest.
* **Output**: 64-character hexadecimal string.
* **Time Complexity**: $O(B)$ where $B$ is the number of 512-bit message blocks. For web URLs, $B \le 33$, running in sub-microsecond time.
* **Space Complexity**: $O(1)$ auxiliary memory (fixed 256-bit internal state).

---

## Algorithm 3: Base62 Short Code Encoding

### Overview
Transforms numeric integer sequences and timestamps into compact alphanumeric strings using a 62-character radix:
$$\Sigma = \{0\dots9,\, a\dots z,\, A\dots Z\}$$
Base62 is natively URL-safe, avoiding percent-encoding overhead like `+`, `/`, or `=`.

* **Input**: Non-negative integer $N$.
* **Process**:
  1. If $N = 0$, return `"0"`.
  2. While $N > 0$:
     $$rem = N \pmod{62}$$
     $$N = \lfloor N / 62 \rfloor$$
     Append character $\Sigma[rem]$.
  3. Reverse the accumulated character array to maintain big-endian significance.
* **Output**: Base62 alphanumeric string (e.g., $125 \rightarrow \text{"cb"}$).
* **Time Complexity**: $O(\log_{62} N)$ operations. For 6-character codes ($62^6 \approx 56.8$ billion unique combinations), time is constant $O(1)$.
* **Space Complexity**: $O(\log_{62} N)$ characters.

---

## Algorithm 4: Custom LRU (Least Recently Used) Cache

### Overview
The LRU cache maintains an ordered working set of the most recently accessed URL mappings in high-speed RAM.
It combines two foundational data structures:
1. **Hash Map (Dictionary)**: Maps `short_code` $\rightarrow$ `Node` reference for instant key resolution.
2. **Doubly Linked List**: Links nodes sequentially with dummy `HEAD` and `TAIL` sentinels to allow insertion, deletion, and relocation in pointer-rewiring time without array shifting.

### Structural Diagram

```text
               HashMap
            ┌───────────┐
 "aB72xK" ──┼───────────┼──┐
            └───────────┘  │
                           ▼
 [HEAD] ⇄ [ Node: aB72xK ] ⇄ [ Node: k9Lm1X ] ⇄ [ Node: z8Wq2A ] ⇄ [TAIL]
 (Sentinel)     (MRU)                                  (LRU)       (Sentinel)
```

### Core Operations

#### `get(key)`
1. Check if `key` exists in Hash Map.
2. If absent: increment `cache_misses`, return `None`.
3. If present: increment `cache_hits`, unlink node from its current position, insert immediately after `HEAD` (MRU position), return node value.
* **Time Complexity**: Strictly $O(1)$
* **Space Complexity**: $O(1)$

#### `put(key, value)`
1. If `key` already exists in Hash Map:
   - Update node's `value`.
   - Relocate node to MRU position behind `HEAD`.
2. If `key` is new:
   - Allocate new `Node(key, value)`.
   - Insert node directly after `HEAD`.
   - Add reference `map[key] = node`.
   - If `len(map) > capacity`:
     - Identify LRU node directly before `TAIL` (`tail.prev`).
     - Unlink LRU node from doubly linked list.
     - Delete entry `map.pop(evicted.key)`.
* **Time Complexity**: Strictly $O(1)$
* **Space Complexity**: $O(1)$ auxiliary per operation; $O(C)$ total for capacity $C$.

#### `remove(key)`
1. Check if `key` in Hash Map.
2. If found, unlink node from doubly linked list and delete from map.
* **Time Complexity**: Strictly $O(1)$

---

## Algorithm 5: Cache-Aside Resolution Flow

### Overview
When a client requests `GET /<short_code>`, the application executes the Cache-Aside pattern:

```text
Incoming Request
       │
       ▼
 [LRU Cache Look-Up]
       │
   ┌───┴───────────────┐
   │ (Found)           │ (Not Found)
   ▼                   ▼
Cache HIT           Cache MISS
   │                   │
   │                   ▼
   │            [MongoDB Lookup]
   │                   │
   │            ┌──────┴───────┐
   │            ▼              ▼
   │          Found?         Not Found?
   │            │              │
   │      (Yes) │              ▼
   │            ▼           HTTP 404
   │      [Put to LRU]
   │            │
   ▼            ▼
 Check Expiry & Increment Clicks
       │
       ▼
HTTP 302 Redirect to Original URL
```

* **Hit Scenario Time Complexity**: $O(1)$ in-memory pointer resolution ($\approx 0.5\,\mu\text{s}$).
* **Miss Scenario Time Complexity**: $O(\log D)$ database index scan followed by $O(1)$ cache insertion.

---

## Algorithm 6: URL Expiration Verification

### Overview
Enforces time-to-live (TTL) on shortened URLs.

* **Input**: `expires_at` ISO 8601 string or `None`.
* **Process**:
  1. If `expires_at` is `None`, URL is permanent $\rightarrow$ return `False`.
  2. Parse `expires_at` timestamp.
  3. Compare with `datetime.now(timezone.utc)`.
  4. If `current_time > expires_at`:
     - Evict from LRU Cache.
     - Set `is_active = False` in MongoDB.
     - Return `True` (Expired).
* **Output**: Boolean `is_expired`.
* **Time Complexity**: $O(1)$.
* **Space Complexity**: $O(1)$.

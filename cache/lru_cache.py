"""
Custom LRU (Least Recently Used) Cache implementation.

Combines a Hash Map (Python dictionary) for O(1) key lookups with a
Doubly Linked List to maintain temporal access ordering in O(1) time.

Design:
    - Sentinel HEAD <--> MRU <--> ... <--> LRU <--> Sentinel TAIL
    - Most recently used item is placed right after HEAD.
    - Least recently used item is placed right before TAIL.
    - Thread-safe using re-entrant locks.
"""
import threading
from typing import Any, Dict, List, Optional, Tuple
from cache.node import Node


class LRUCache:
    """
    LRU Cache implemented using a HashMap + Doubly Linked List.

    Time Complexity:
        get(key)    : O(1)
        put(key)    : O(1)
        remove(key) : O(1)
        clear()     : O(1)
        size()      : O(1)

    Space Complexity:
        O(C) where C is the maximum capacity.
    """

    def __init__(self, capacity: int = 100):
        if capacity <= 0:
            raise ValueError("Cache capacity must be a positive integer greater than 0.")
        self.capacity: int = capacity
        self.map: Dict[Any, Node] = {}

        # Sentinel dummy nodes
        self.head: Node = Node("__HEAD_SENTINEL__", None)
        self.tail: Node = Node("__TAIL_SENTINEL__", None)
        self.head.next = self.tail
        self.tail.prev = self.head

        # Statistics
        self.hits: int = 0
        self.misses: int = 0

        # Thread safety lock
        self._lock = threading.RLock()

    # --------------------------------------------------------------------------
    # Internal Doubly Linked List Operations (O(1))
    # --------------------------------------------------------------------------

    def _add_to_front(self, node: Node) -> None:
        """Add node immediately after the HEAD sentinel (MRU position)."""
        node.prev = self.head
        node.next = self.head.next
        self.head.next.prev = node
        self.head.next = node

    def _remove_node(self, node: Node) -> None:
        """Unlink an existing node from the Doubly Linked List."""
        node.prev.next = node.next
        node.next.prev = node.prev
        node.prev = None
        node.next = None

    def _move_to_front(self, node: Node) -> None:
        """Move an existing node to the MRU position (right after HEAD)."""
        self._remove_node(node)
        self._add_to_front(node)

    def _pop_tail(self) -> Optional[Node]:
        """Remove and return the LRU node (just before TAIL sentinel)."""
        lru_node = self.tail.prev
        if lru_node is self.head:
            return None
        self._remove_node(lru_node)
        return lru_node

    # --------------------------------------------------------------------------
    # Public API Methods
    # --------------------------------------------------------------------------

    def get(self, key: Any) -> Optional[Any]:
        """
        Retrieve value by key.
        - If key exists: move node to MRU, increment hit count, return value.
        - If key does not exist: increment miss count, return None.

        Time Complexity: O(1)
        """
        with self._lock:
            if key in self.map:
                node = self.map[key]
                self._move_to_front(node)
                self.hits += 1
                return node.value
            else:
                self.misses += 1
                return None

    def put(self, key: Any, value: Any) -> None:
        """
        Insert or update key-value pair.
        - If key exists: update value and move to MRU front.
        - If key is new: create node, insert at MRU front.
          If capacity exceeded: evict least recently used (LRU) node from tail.

        Time Complexity: O(1)
        """
        with self._lock:
            if key in self.map:
                node = self.map[key]
                node.value = value
                self._move_to_front(node)
            else:
                new_node = Node(key, value)
                self.map[key] = new_node
                self._add_to_front(new_node)

                # Check if capacity is exceeded
                if len(self.map) > self.capacity:
                    evicted = self._pop_tail()
                    if evicted and evicted.key in self.map:
                        del self.map[evicted.key]

    def remove(self, key: Any) -> Optional[Any]:
        """
        Remove a key and its node from the cache if present.

        Time Complexity: O(1)
        """
        with self._lock:
            if key in self.map:
                node = self.map.pop(key)
                self._remove_node(node)
                return node.value
            return None

    def clear(self) -> None:
        """Reset the cache contents and linked list structure."""
        with self._lock:
            self.map.clear()
            self.head.next = self.tail
            self.tail.prev = self.head

    def size(self) -> int:
        """Return the current number of items stored in the cache."""
        with self._lock:
            return len(self.map)

    def is_full(self) -> bool:
        """Return True if the cache has reached maximum capacity."""
        with self._lock:
            return len(self.map) >= self.capacity

    def display(self) -> List[Tuple[Any, Any]]:
        """
        Return a list of (key, value) pairs ordered from Most Recently Used (MRU)
        to Least Recently Used (LRU).
        """
        with self._lock:
            items: List[Tuple[Any, Any]] = []
            curr = self.head.next
            while curr is not self.tail and curr is not None:
                items.append((curr.key, curr.value))
                curr = curr.next
            return items

    def get_stats(self) -> Dict[str, Any]:
        """
        Return cache performance metrics and current status.

        Formula:
            total_requests = hits + misses
            hit_rate = (hits / total_requests) * 100 if total_requests > 0 else 0.0
        """
        with self._lock:
            total = self.hits + self.misses
            hit_rate = (self.hits / total * 100.0) if total > 0 else 0.0
            return {
                "capacity": self.capacity,
                "current_size": len(self.map),
                "total_requests": total,
                "hits": self.hits,
                "misses": self.misses,
                "hit_rate": round(hit_rate, 2),
            }

    def reset_stats(self) -> None:
        """Reset hit and miss counters."""
        with self._lock:
            self.hits = 0
            self.misses = 0

    def __len__(self) -> int:
        return self.size()

    def __contains__(self, key: Any) -> bool:
        with self._lock:
            return key in self.map

    def __repr__(self) -> str:
        return f"<LRUCache size={self.size()}/{self.capacity} hits={self.hits} misses={self.misses}>"

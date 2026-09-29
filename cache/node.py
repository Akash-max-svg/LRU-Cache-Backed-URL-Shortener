"""
Doubly Linked List Node for LRU Cache.
"""


class Node:
    """
    Represents a single node in the Doubly Linked List of the LRU Cache.

    Attributes:
        key: The key identifier (e.g. short_code).
        value: The value stored (e.g. URL document or original URL).
        prev: Pointer to previous node in the list.
        next: Pointer to next node in the list.
    """

    def __init__(self, key, value):
        self.key = key
        self.value = value
        self.prev = None
        self.next = None

    def __repr__(self):
        return f"Node(key={self.key!r}, value={self.value!r})"

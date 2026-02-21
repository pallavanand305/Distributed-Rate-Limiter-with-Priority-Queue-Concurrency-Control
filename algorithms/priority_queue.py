"""
Binary Min-Heap Priority Queue

Implements a priority queue using a binary min-heap with dynamic array.
Supports three priority levels: CRITICAL (0), HIGH (1), NORMAL (2).
Preserves FIFO ordering within same priority level.
"""

from typing import Optional, Tuple, Dict, Any


class PriorityQueue:
    """
    Binary min-heap priority queue for request scheduling.
    
    Heap Properties:
    - Parent at index i, children at 2i+1 and 2i+2
    - Min-heap: parent priority ≤ children priorities
    - For same priority, lower sequence_number comes first (FIFO)
    
    Time Complexity:
    - insert: O(log n)
    - extract_min: O(log n)
    - decrease_key: O(log n)
    - peek_min: O(1)
    """
    
    def __init__(self):
        """Initialize empty priority queue."""
        self.heap = []  # Dynamic array: [(priority, sequence, request_id, data), ...]
        self.sequence_counter = 0  # For FIFO within same priority
        self.index_map: Dict[str, int] = {}  # Maps request_id to heap index
        
    def insert(self, request_id: str, priority: int, data: Dict[str, Any]) -> None:
        """
        Insert request into priority queue.
        
        Args:
            request_id: Unique identifier for the request
            priority: Priority level (0=CRITICAL, 1=HIGH, 2=NORMAL)
            data: Request metadata
            
        Time: O(log n)
        """
        if priority not in [0, 1, 2]:
            raise ValueError(f"Priority must be 0, 1, or 2, got {priority}")
            
        # Create heap item with sequence number for FIFO
        item = (priority, self.sequence_counter, request_id, data)
        self.sequence_counter += 1
        
        # Add to end of heap
        self.heap.append(item)
        index = len(self.heap) - 1
        self.index_map[request_id] = index
        
        # Restore heap property
        self._heapify_up(index)
    
    def extract_min(self) -> Tuple[str, Dict[str, Any]]:
        """
        Remove and return highest priority request.
        
        Returns:
            Tuple of (request_id, data)
            
        Raises:
            IndexError: If queue is empty
            
        Time: O(log n)
        """
        if not self.heap:
            raise IndexError("Cannot extract from empty queue")
        
        # Get min element
        min_item = self.heap[0]
        request_id = min_item[2]
        data = min_item[3]
        
        # Remove from index map
        del self.index_map[request_id]
        
        if len(self.heap) == 1:
            self.heap.pop()
            return request_id, data
        
        # Move last element to root
        last_item = self.heap.pop()
        self.heap[0] = last_item
        self.index_map[last_item[2]] = 0
        
        # Restore heap property
        self._heapify_down(0)
        
        return request_id, data
    
    def peek_min(self) -> Optional[Tuple[str, int, Dict[str, Any]]]:
        """
        View highest priority request without removing.
        
        Returns:
            Tuple of (request_id, priority, data) or None if empty
            
        Time: O(1)
        """
        if not self.heap:
            return None
        
        item = self.heap[0]
        return item[2], item[0], item[3]
    
    def decrease_key(self, request_id: str, new_priority: int) -> None:
        """
        Decrease priority of existing request (make it higher priority).
        
        Args:
            request_id: Request to update
            new_priority: New priority level (must be lower number)
            
        Raises:
            KeyError: If request_id not found
            ValueError: If new_priority is not lower
            
        Time: O(log n)
        """
        if request_id not in self.index_map:
            raise KeyError(f"Request {request_id} not found in queue")
        
        if new_priority not in [0, 1, 2]:
            raise ValueError(f"Priority must be 0, 1, or 2, got {new_priority}")
        
        index = self.index_map[request_id]
        old_item = self.heap[index]
        old_priority = old_item[0]
        
        if new_priority >= old_priority:
            raise ValueError(f"New priority {new_priority} must be less than old priority {old_priority}")
        
        # Update priority, keep same sequence number for FIFO
        new_item = (new_priority, old_item[1], old_item[2], old_item[3])
        self.heap[index] = new_item
        
        # Restore heap property (only need to heapify up since priority decreased)
        self._heapify_up(index)
    
    def size(self) -> int:
        """Return number of items in queue."""
        return len(self.heap)
    
    def is_empty(self) -> bool:
        """Check if queue is empty."""
        return len(self.heap) == 0
    
    def _heapify_up(self, index: int) -> None:
        """
        Restore heap property by moving element up.
        
        Args:
            index: Index of element to heapify up
        """
        while index > 0:
            parent_index = (index - 1) // 2
            
            # Check if heap property is satisfied
            if self._compare(self.heap[index], self.heap[parent_index]):
                # Swap with parent
                self.heap[index], self.heap[parent_index] = \
                    self.heap[parent_index], self.heap[index]
                
                # Update index map
                self.index_map[self.heap[index][2]] = index
                self.index_map[self.heap[parent_index][2]] = parent_index
                
                index = parent_index
            else:
                break
    
    def _heapify_down(self, index: int) -> None:
        """
        Restore heap property by moving element down.
        
        Args:
            index: Index of element to heapify down
        """
        size = len(self.heap)
        
        while True:
            smallest = index
            left = 2 * index + 1
            right = 2 * index + 2
            
            # Find smallest among node and its children
            if left < size and self._compare(self.heap[left], self.heap[smallest]):
                smallest = left
            
            if right < size and self._compare(self.heap[right], self.heap[smallest]):
                smallest = right
            
            # If smallest is not current node, swap and continue
            if smallest != index:
                self.heap[index], self.heap[smallest] = \
                    self.heap[smallest], self.heap[index]
                
                # Update index map
                self.index_map[self.heap[index][2]] = index
                self.index_map[self.heap[smallest][2]] = smallest
                
                index = smallest
            else:
                break
    
    def _compare(self, item1: Tuple, item2: Tuple) -> bool:
        """
        Compare two heap items.
        
        Returns True if item1 has higher priority than item2.
        Comparison: (priority1, seq1) < (priority2, seq2)
        
        Args:
            item1: First item (priority, sequence, request_id, data)
            item2: Second item (priority, sequence, request_id, data)
            
        Returns:
            True if item1 should come before item2
        """
        # Compare by priority first, then by sequence for FIFO
        return (item1[0], item1[1]) < (item2[0], item2[1])

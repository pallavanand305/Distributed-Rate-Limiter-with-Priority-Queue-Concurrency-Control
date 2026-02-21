import pytest
from algorithms.priority_queue import PriorityQueue

def test_empty_queue_extraction():
    pq = PriorityQueue()
    with pytest.raises(IndexError):
        pq.extract_min()

def test_single_element_operations():
    pq = PriorityQueue()
    pq.insert('req1', 1, {'data': 'test'})
    assert pq.size() == 1
    assert not pq.is_empty()
    result = pq.peek_min()
    assert result[0] == 'req1'
    assert result[1] == 1
    req_id, data = pq.extract_min()
    assert req_id == 'req1'
    assert pq.is_empty()

def test_fifo_ordering_same_priority():
    pq = PriorityQueue()
    pq.insert('req1', 1, {})
    pq.insert('req2', 1, {})
    pq.insert('req3', 1, {})
    req1, _ = pq.extract_min()
    req2, _ = pq.extract_min()
    req3, _ = pq.extract_min()
    assert [req1, req2, req3] == ['req1', 'req2', 'req3']

def test_decrease_key_nonexistent():
    pq = PriorityQueue()
    pq.insert('req1', 2, {})
    with pytest.raises(KeyError):
        pq.decrease_key('req2', 1)

def test_decrease_key_invalid_priority():
    pq = PriorityQueue()
    pq.insert('req1', 1, {})
    with pytest.raises(ValueError):
        pq.decrease_key('req1', 2)

def test_priority_ordering():
    pq = PriorityQueue()
    pq.insert('normal', 2, {})
    pq.insert('critical', 0, {})
    pq.insert('high', 1, {})
    req1, _ = pq.extract_min()
    req2, _ = pq.extract_min()
    req3, _ = pq.extract_min()
    assert [req1, req2, req3] == ['critical', 'high', 'normal']

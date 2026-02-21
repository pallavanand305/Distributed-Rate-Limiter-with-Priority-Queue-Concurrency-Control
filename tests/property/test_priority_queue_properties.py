from hypothesis import given, strategies as st, settings
from algorithms.priority_queue import PriorityQueue

@given(requests=st.lists(st.tuples(st.text(min_size=1, max_size=20), st.integers(min_value=0, max_value=2), st.dictionaries(st.text(min_size=1, max_size=10), st.integers())), min_size=1, max_size=100, unique_by=lambda x: x[0]))
@settings(max_examples=100)
def test_priority_queue_ordering(requests):
    pq = PriorityQueue()
    for request_id, priority, data in requests:
        pq.insert(request_id, priority, data)
    extracted = []
    while not pq.is_empty():
        request_id, data = pq.extract_min()
        extracted.append(request_id)
    expected_order = [req[0] for req in sorted([(req[0], req[1], idx) for idx, req in enumerate(requests)], key=lambda x: (x[1], x[2]))]
    assert extracted == expected_order

@given(operations=st.lists(st.one_of(st.tuples(st.just('insert'), st.text(min_size=1, max_size=20), st.integers(min_value=0, max_value=2), st.integers()), st.tuples(st.just('extract_min')), st.tuples(st.just('peek_min'))), min_size=1, max_size=50))
@settings(max_examples=100)
def test_heap_invariant_preservation(operations):
    pq = PriorityQueue()
    inserted_ids = set()
    for op in operations:
        if op[0] == 'insert':
            _, request_id, priority, data_val = op
            if request_id not in inserted_ids:
                pq.insert(request_id, priority, {'value': data_val})
                inserted_ids.add(request_id)
        elif op[0] == 'extract_min':
            if not pq.is_empty():
                request_id, _ = pq.extract_min()
                inserted_ids.discard(request_id)
        elif op[0] == 'peek_min':
            pq.peek_min()
    _verify_heap_invariant(pq)

def _verify_heap_invariant(pq):
    heap = pq.heap
    size = len(heap)
    for i in range(size):
        left = 2 * i + 1
        right = 2 * i + 2
        if left < size:
            assert pq._compare(heap[i], heap[left]) or heap[i] == heap[left]
        if right < size:
            assert pq._compare(heap[i], heap[right]) or heap[i] == heap[right]
    for request_id, index in pq.index_map.items():
        assert heap[index][2] == request_id

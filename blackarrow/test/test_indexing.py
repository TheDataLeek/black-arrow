from ..blackarrow import index_worker

import multiprocessing as mp


def test_not_empty():
    input_queue = mp.Queue()
    index_worker('.', None, 1, input_queue, None)

    vals = []
    while not input_queue.empty():
        vals.append(input_queue.get())

    assert len(vals) != 0

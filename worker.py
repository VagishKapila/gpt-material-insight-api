import os
from rq import Worker, Queue, Connection
from task_queue import conn  # ✅ use your own Redis connection, not Python’s queue module

listen = ['default']

if __name__ == '__main__':
    with Connection(conn):
        worker = Worker(list(map(Queue, listen)))
        worker.work()

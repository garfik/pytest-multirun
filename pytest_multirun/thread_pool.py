# -*- coding: utf-8 -*-
from queue import Queue
from threading import Thread
import time


class Worker(Thread):
    """Thread executing tasks from a given tasks queue"""

    def __init__(self, tasks):
        Thread.__init__(self)
        self.tasks = tasks
        self.daemon = True
        self.start()

    def run(self):
        while True:
            func, args, kargs = self.tasks.get()
            try:
                func(*args, **kargs)
            except Exception as e:
                print(e)
            finally:
                self.tasks.task_done()


class ThreadPool:
    """Pool of threads consuming tasks from a queue"""

    def __init__(self, num_threads):
        self.num_threads = num_threads
        self.tasks = Queue()

    def add_task(self, func, *args, **kargs):
        """Add a task to the queue"""
        self.tasks.put((func, args, kargs))

    def start_task(self):
        """Start tasks"""
        for _ in range(self.num_threads):
            Worker(self.tasks)

    def wait_completion(self):
        """Wait for completion of all the tasks in the queue"""
        try:
            while self.tasks.unfinished_tasks:
                time.sleep(1)
        except KeyboardInterrupt:
            print('---- KI in wait_completion ----')

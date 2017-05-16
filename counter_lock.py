# coding=utf8
"""
implments a lock will release after n-times touch
"""
from threading import Semaphore

class CounterLock:
    """
    implments a lock will release after n-times touch
    """
    def __init__(self, num):
        self.num = num
        self.count = 0
        self.mutex = Semaphore(1)
        self.barrier = Semaphore(0)

    def touch(self):
        """
        touch the counter
        """
        with self.mutex:
            self.count = self.count + 1
            if self.count == self.num:
                self.barrier.release()

    def wait(self):
        """
        acquired by those need to be blocked
        """
        self.barrier.acquire()

    def reset(self):
        """
        reset the counter
        """
        with self.mutex:
            self.count = 0

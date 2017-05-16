# coding=utf8
"""
implments barrier in python2.x
"""
from threading import Semaphore, Lock


class Barrier:
    """
    implments barrier in python2.x
    """

    def __init__(self, num):
        self.num = num
        self.count = 0
        self.mutex = Lock()
        self.barrier = Semaphore(0)


    def wait(self):
        """
        wait for other threads reach barrier
        """
        with self.mutex:
            self.count += 1
            #print('[%d] ****%d****' % (id(self), self.count))
            if self.count >= self.num:
                self.barrier.release()

        self.barrier.acquire()
        self.barrier.release()

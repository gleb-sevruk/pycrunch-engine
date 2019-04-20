from datetime import datetime
from queue import Queue
import time

class AbstractTask:
    def run(self):
        pass


# https://stackoverflow.com/questions/45369128/python-multithreading-queue

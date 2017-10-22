import queue
from requests.exceptions import HTTPError
from threading import Thread
from vapor.models import Log

task_queue = queue.Queue()

def size():
    return task_queue.qsize()

def is_empty():
    return task_queue.empty()

def push_task(f, *args, **kwargs):
    task_queue.put((f, args, kwargs))

def join():
    task_queue.join()


def worker(thread_id):
    print("Worker id = %d started!" % thread_id)
    while True:
        item = task_queue.get()
        print("Worker id = %d deqed!" % thread_id)
        fun, args, kwargs = item
        try:
            fun(*args, **kwargs)
        except HTTPError as e:
            Log.objects.create("Unhandled HttpError in Task %d" % thread_id)
        except:
             print("Unhandeled Exception in Job")
        task_queue.task_done()
        print("Worker id = %d done!" % thread_id)

def execute_with_workers(num_workers):
    for i in range(num_workers):
        t = Thread(target=worker, kwargs={'thread_id' : i})
        t.daemon = True
        t.start()



execute_with_workers(15)
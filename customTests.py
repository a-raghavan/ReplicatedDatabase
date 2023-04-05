from concurrent import futures
from time import sleep
def sleep2seconds():
    sleep(3)


threadpoolexecutor = futures.ThreadPoolExecutor(max_workers=2)
a = threadpoolexecutor.submit(sleep2seconds)
b = threadpoolexecutor.submit(sleep2seconds)
a.result()
print('a')
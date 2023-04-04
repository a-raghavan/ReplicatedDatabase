import unittest
import signal
import os, time, random, subprocess
import grpc
import database_pb2
import database_pb2_grpc


class TestTimeout(Exception):
    pass

class test_timeout:
  def __init__(self, seconds, error_message=None):
    if error_message is None:
      error_message = 'test timed out after {}s.'.format(seconds)
    self.seconds = seconds
    self.error_message = error_message

  def handle_timeout(self, signum, frame):
    raise TestTimeout(self.error_message)

  def __enter__(self):
    signal.signal(signal.SIGALRM, self.handle_timeout)
    signal.alarm(self.seconds)

  def __exit__(self, exc_type, exc_val, exc_tb):
    signal.alarm(0)

def log(msg, level='INFO'):
    print('[%s]: %s' % (level, msg))

server_ports = [30001, 30002, 30003]
raft_server_ports = [50001, 50002, 50003]


class ServerProcess:
    def pid_fname(self):
        return '.pid.server-%d.pid' % self.portnumber

    def __init__(self, portnumber,raftportnumber):
        self.portnumber = portnumber
        self.raftportnumber = raftportnumber
        self.instance = None
        self.base_url = 'localhost:%d' % self.portnumber

    def kill_if_running(self):
        fname = self.pid_fname()
        if not os.path.isfile(fname): return
        with open(fname, 'r') as f:
            try:
                pid = int(f.read().strip())
                #log('Killing process with pid: %d' % pid, 'INFO')
                os.kill(pid, 9)
                if self.instance is not None: self.instance.wait()
            except Exception as e:
                log('Unable to read/kill server: %s' % e, 'WARN')
        if os.path.isfile(fname):
            os.remove(fname)

    def restart(self):
        self.kill_if_running()
        if self.instance is not None:
            self.instance.stagger()
            self.instance = None

        time.sleep(0.1)
        if not os.path.exists('./server.py'):
            raise Exception('./server.py not found.')

        for _ in range(3):
            args = [
                'python3', './server.py',
                '-n', '10.10.1.6:30001 10.10.1.6:30002 10.10.1.6:30003',
                '-sp', str(self.portnumber),
                '-rp', str(self.raftportnumber)]


            process = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            pid = process.pid
            with open(self.pid_fname(), 'w') as f:
                f.write("%d\r\n" % pid)
            time.sleep(0.5)

            if process.poll() is None:
                self.instance = process
                break
        else:
            raise Exception("Unable to start the server. 99% of the time it means that your server crashed as soon as it started. Please check manually. 1% of the time it could be due to overloaded CSL machines, please try again in 10 seconds. This is almost never the case.")

    def check_process_alive(self):
        if self.instance is None: return False
        if self.instance.poll() is not None: return False
        try:
            os.kill(self.instance.pid, 0)
            return True
        except OSError:
            return False

    def putData(self, key, value):
        with grpc.insecure_channel(self.base_url) as channel:
            stub = database_pb2_grpc.DatabaseStub(channel)
            return stub.Put(database_pb2.PutRequest(key= key, value= value))
    
    def getData(self, key):
        with grpc.insecure_channel(self.base_url) as channel:
            stub = database_pb2_grpc.DatabaseStub(channel)
            return stub.Get(database_pb2.GetRequest(key= key))




class Test1AppendEntries(unittest.TestCase):
    def setUp(self):
        self.nodes = []
        for idx,port in enumerate(server_ports):
            self.nodes.append(ServerProcess(port, raft_server_ports[idx]))
        for node in self.nodes:
            node.restart()

        self.alive()
    
    def tearDown(self):
        self.alive() # check that all nodes are still alive
        for node in self.nodes:
            node.kill_if_running()
        
    def alive(self):
        for node in self.nodes:
            self.assertTrue(node.check_process_alive())

    def test_a_server_spinsup(self):
        self.alive()

    def test_simple_appentEntries_request(self):
        self.assertTrue(self.nodes[0].putData("akshay","awesome").errormsg =="")
        self.assertTrue(self.nodes[0].getData("akshay") == "awesome")

if __name__ == '__main__':
    unittest.main(exit=False)

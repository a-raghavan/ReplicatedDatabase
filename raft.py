from concurrent import futures
import grpc
import raft_pb2_grpc
import raft_pb2

import threading

class ReplicatedLogEntry:
    def __init__(self, key, value):
        self.command = "PUT"            # always be PUT
        self.key = key
        self.value = value              # empty for get requests
        self.term = 1                   # static for now, will change after leader election

class ReplicatedLog:
    def __init__(self):
        self.log = []                       # list of ReplicatedLogEntry
        self.commitIndex = 0
        self.processedIndex = -1
    
    def append(self, entry):
        self.log.append(entry)

class RaftGRPCServer(raft_pb2_grpc.RaftServicer):

    def AppendEntries(self, request, context):
        return

    def createGRPCServerThread():
        _thread = threading.Thread(target=__grpcServerThread)
        _thread.start()
        _thread.join()

    def __grpcServerThread():
        port = '50052'
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        raft_pb2_grpc.add_RaftServicer_to_server(Raft(), server)
        server.add_insecure_port('[::]:' + port)
        server.start()
        print("Raft Server started, listening on " + port)
        server.wait_for_termination()

class RafrGRPCClient():
    def __init__(self, raftmaininstance):
        self.raftmaininstance = raftmaininstance

    def createGRPCClientThread():
        _thread = threading.Thread(target=__grpcClientThread)
        _thread.start()
        _thread.join()
    
    def __grpcClientThread():
        while (True):
            # if new command to replicate:
            #     replicate in other replicas
            # else:
            #     send heartbeat 
            with self.raftmaininstance.logLock:
                pidx = self.raftmaininstance.replicatedlog.processedIndex
                loglen = len(self.raftmaininstance.replicatedlog.log)
            if pidx < loglen-1:
                for n in other_nodes:
                    # send appendEntries as seaprate threads            


class RaftMain():
    def __init__(self):
        self.replicatedlog = ReplicatedLog()
        self.grpcServer = RaftGRPCServer()
        self.grpcServer.createGRPCServerThread()
        self.grpcClient = RafrGRPCClient(self)
        self.grpcClient.createGRPCClientThread()
        self.logLock = threading.Lock()
    
    def addCommandToReplicatedLog(self, entry):
        # acquire lock for replicated log
        # return index where entry is appended
        retval = 0
        with self.logLock:
            self.replicatedlog.append(entry)
            retval = len(self.replicatedlog.log)-1
        return retval
    
    def getCommitIndex(self):
        retval = 0
        with self.logLock:
            retval = self.replicatedlog.commitIndex
        return retval


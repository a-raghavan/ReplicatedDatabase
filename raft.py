from concurrent import futures
import grpc
import raft_pb2_grpc
import raft_pb2

import threading
import math

class ReplicatedLogEntry:
    def __init__(self, key, value):
        self.command = "PUT"            # always be PUT
        self.key = key
        self.value = value              # empty for get requests
        self.term = 1                   # static for now, will change after leader election

class ReplicatedLog:
    def __init__(self):
        self.log = []                       # list of ReplicatedLogEntry
        self.commitIndex = -1
        self.processedIndex = -1
    
    def append(self, entry):
        self.log.append(entry)

class RaftGRPCServer(raft_pb2_grpc.RaftServicer):
    def __init__(self, raftmaininstance):
        self.raftmaininstance = raftmaininstance
    
    def AppendEntries(self, request, context):
        # if request.currterm < mycurrentterm:
        # return failure rpc response with current term 
        # if request.prevlogindex < loglen:
        # truncate replicated log until prevlogindex
        # if request.commitIdx > mycommitidx:
        # commit entries (i.e. write to levelDB) until request.commitIdx
        # if !(request.prevlogidx and request.prevlogterm match with our replicated log)
        #   return failure rpc response
        # else: append entry
        
        with self.raftmaininstance.logLock:
            myCurrTerm = self.raftmaininstance.currentTerm

        if request.currentterm < myCurrTerm:
            return raft_pb2.AppendEntriesResponse(success=False, term=myCurrTerm)
        
        with self.raftmaininstance.logLock:
            loglen = len(self.raftmaininstance.replicatedlog.log)
            if request.prevlogindex < loglen:
                self.raftmaininstance.replicatedlog.log = self.raftmaininstance.replicatedlog.log[:request.prevlogindex+1]
            else:
                return raft_pb2.AppendEntriesResponse(success=False, term=myCurrTerm)
      
            
        with self.raftmaininstance.logLock:
            myCommitIdx = self.raftmaininstance.replicatedlog.commitIdx
            if request.commitIdx > myCommitIdx:
                while myCommitIdx <= request.commitIdx:
                    self.raftmaininstance.db.Put(
                        bytearray(self.raftmaininstance.replicatedlog.log[myCommitIdx].key, 'utf-8'), 
                        bytearray(self.raftmaininstance.replicatedlog.log[myCommitIdx].value, 'utf-8'))
                    myCommitIdx += 1
                    self.raftmaininstance.replicatedlog.commitIdx += 1

        with self.raftmaininstance.logLock:
            if request.previousterm !=  self.raftmaininstance.replicatedlog.log[request.prevlogindex].term:
                return raft_pb2.AppendEntriesResponse(success=False, term=myCurrTerm)
            else:
                self.raftmaininstance.replicatedlog.log.append(ReplicatedLogEntry(request.entries[0].key, request.entries[0].value))
        
        return raft_pb2.AppendEntriesResponse(success=True, term=myCurrTerm)

    def createGRPCServerThread(self):
        _thread = threading.Thread(target=self.__grpcServerThread)
        _thread.start()
        #_thread.join()

    def __grpcServerThread(self):
        port = '50052'
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        raft_pb2_grpc.add_RaftServicer_to_server(raft_pb2_grpc.Raft(), server)
        server.add_insecure_port('[::]:' + port)
        server.start()
        print("Raft Server started, listening on " + port)
        server.wait_for_termination()

class RafrGRPCClient():
    def __init__(self, raftmaininstance):
        self.raftmaininstance = raftmaininstance
        self.threadpoolexecutor = futures.ThreadPoolExecutor(max_workers=10)
        self.nextIndices = {k:0 for k in self.raftmaininstance.othernodes}  # move it to appropriate function when candidate becomes leader
        self.RaftGRPCClientLock = threading.Lock()

    def createGRPCClientThread(self):
        _thread = threading.Thread(target=self.__grpcClientThread)
        _thread.start()
        #_thread.join()
    
    def __grpcClientThread(self):
        while (True):
            # if new command to replicate:
            #     replicate in other replicas
            # else:
            #     send heartbeat 
            with self.raftmaininstance.logLock:
                pidx = self.raftmaininstance.replicatedlog.processedIndex
                loglen = len(self.raftmaininstance.replicatedlog.log)
            if pidx < loglen-1:
                # send appendEntries as seaprate threads   
                # everytime we get a success response from the grpc.
                # create grpc append entries thread and start it

                # for i in len(range(majority)):
                #     t.join()
                for follower in self.raftmaininstance.othernodes:
                    futurelist = [self.threadpoolexecutor.submit(self.__appendEntriesThread, followerNodePort=nodePort) for nodePort in self.raftmaininstance.othernodes]
                
                with self.raftmaininstance.logLock:
                    self.raftmaininstance.replicatedlog.processedIndex += 1
                
                # TODO check for numCompleteVar
                print("Broadcast new entry to network")
                print("Majority occurs when ::"+ str(math.ceil(len(self.raftmaininstance.othernodes)/2)) +" approve")
                for fidx in range(math.ceil(len(self.raftmaininstance.othernodes)/2)):
                    out = futurelist[fidx].result() # always returns True?
                    print("Got result:: "+ out)
                
                # commit
                print("Commit new entry to StateMachine")
                self.raftmaininstance.db.Put(bytearray(request.key, 'utf-8'), bytearray(request.value, 'utf-8'))

                # replicated in majority, increment commit index
                with self.raftmaininstance.logLock:
                    self.raftmaininstance.replicatedlog.commitIndex += 1
    
    def __appendEntriesThread(self, followerNodePort):
        # implement append entries RPC logic
        # get log command from followerPrevIdx
        # send appendEntriesRPC
        # if success, return True
        # elif timeout : retry
        # elif failure : decrement self.nextIndices[followerNodePort] and retry
        response = raft_pb2.AppendEntriesResponse(term=1, success=False)
        while not response.success:
            with self.RaftGRPCClientLock:
                myFollowerNextIdx = self.nextIndices[followerNodePort]
                entry = self.raftmaininstance.replicatedlog.log[myFollowerNextIdx]
                cmtIdx =  self.raftmaininstance.replicatedlog.commitIndex
                prevTerm= self.raftmaininstance.replicatedlog.log[myFollowerNextIdx-1].term

            with grpc.insecure_channel(followerNodePort) as channel:
                stub = raft_pb2_grpc.RaftStub(channel)
                lgent = raft_pb2.LogEntry(command=entry.command, key=entry.key, value=entry.value, term=entry.term)
                try:
                    response = stub.AppendEntries(raft_pb2.AppendEntriesRequest(prevlogindex=myFollowerNextIdx-1, previousterm=prevTerm, 
                                entries= [lgent], commitindex=cmtIdx, currentterm=1))
                    print("Success Status::"+ response.success)
                    print("Response term::"+ response.term)

                    if not response.success:
                        with self.RaftGRPCClientLock:
                            self.nextIndices[followerNodePort] -= 1

                except Exception as e:
                    continue        

class RaftMain():
    def __init__(self, othernodes, leveldbinstance):
        # intializing data members
        self.replicatedlog = ReplicatedLog()
        from copy import deepcopy
        self.othernodes = deepcopy(othernodes)
        self.currentTerm = 1
        self.db = leveldbinstance
        self.logLock = threading.Lock()
        # Creating client and Server threads
        self.grpcServer = RaftGRPCServer(self)
        self.grpcServer.createGRPCServerThread()
        self.grpcClient = RafrGRPCClient(self)
        self.grpcClient.createGRPCClientThread()
        
        # TODO create heartbeat thread if state = leader
    
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


from concurrent import futures
import grpc
import raft_pb2_grpc
import raft_pb2

import threading
import math
import random

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
    def __init__(self, raftmaininstance, raftPort):
        self.raftmaininstance = raftmaininstance
        self.port = raftPort
    
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

        print("request.prevlogindex"+ str(request.prevlogindex))
        print("request.entries.key"+ str(request.entries[0].key))
        print("request.entries.value"+ str(request.entries[0].value))
        with self.raftmaininstance.logLock:
            print("replicated log len APpendEntries Raft server", len(self.raftmaininstance.replicatedlog.log))

        with self.raftmaininstance.logLock:
            myCurrTerm = self.raftmaininstance.currentTerm

        if request.currentterm < myCurrTerm:
            return raft_pb2.AppendEntriesResponse(success=False, term=myCurrTerm)
        
        with self.raftmaininstance.logLock:
            loglen = len(self.raftmaininstance.replicatedlog.log)
            if request.prevlogindex <= loglen-1:
                self.raftmaininstance.replicatedlog.log = self.raftmaininstance.replicatedlog.log[:request.prevlogindex+1]
            else:
                return raft_pb2.AppendEntriesResponse(success=False, term=myCurrTerm)
      
            
        with self.raftmaininstance.logLock:
            myCommitIdx = self.raftmaininstance.replicatedlog.commitIndex
            while myCommitIdx < request.commitindex:
                print("request.commitindex:: " + str(request.commitindex))
                print("myCommitIdx:: " + str(myCommitIdx))
                print("length of replicated log::" + str(len(self.raftmaininstance.replicatedlog.log)))
                print("raft main instance obj :", self.raftmaininstance)
                self.raftmaininstance.db.Put(
                    bytearray(self.raftmaininstance.replicatedlog.log[myCommitIdx].key, 'utf-8'), 
                    bytearray(self.raftmaininstance.replicatedlog.log[myCommitIdx].value, 'utf-8'))
                myCommitIdx += 1
                self.raftmaininstance.replicatedlog.commitIndex += 1

        with self.raftmaininstance.logLock:
            #Need to check request.prevlogindex!=-1 condition is safe
            if request.prevlogindex!=-1 and request.previousterm != self.raftmaininstance.replicatedlog.log[request.prevlogindex].term:
                return raft_pb2.AppendEntriesResponse(success=False, term=myCurrTerm)
            else:
                # Should we increase processedIdx, adding this for now to avoid client thread getting called
                print("Appending new Record")
                print("key::"+ request.entries[0].key)
                print("value::" + request.entries[0].value)
                self.raftmaininstance.replicatedlog.processedIndex+=1
                self.raftmaininstance.replicatedlog.append(ReplicatedLogEntry(request.entries[0].key, request.entries[0].value))
                print("length of replicated log::" + str(len(self.raftmaininstance.replicatedlog.log)))
                print("raft main instance obj :", self.raftmaininstance)
        
        return raft_pb2.AppendEntriesResponse(success=True, term=myCurrTerm)

    def createGRPCServerThread(self):
        _thread = threading.Thread(target= self.__grpcServerThread)
        _thread.start()
        #_thread.join()

    def __grpcServerThread(self):
        # port = '50052'
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        raft_pb2_grpc.add_RaftServicer_to_server(self, server)
        server.add_insecure_port('[::]:' + self.port)
        server.start()
        print("Raft Server started, listening on " + self.port)
        server.wait_for_termination()

class RafrGRPCClient():
    def __init__(self, raftmaininstance):
        self.raftmaininstance = raftmaininstance
        self.threadpoolexecutor = futures.ThreadPoolExecutor(max_workers=1)
        self.nextIndices = {k:0 for k in self.raftmaininstance.othernodes}  # move it to appropriate function when candidate becomes leader
        self.RaftGRPCClientLock = threading.Lock()

    def createGRPCClientThread(self):
        _thread = threading.Thread(target=self.__grpcClientThread, args=[random.randint(10000,20000)])
        _thread.start()
        #_thread.join()
    
    def __grpcClientThread(self, idx):
        print("__grpcClientThread idx ::", idx)
        while (True):
            # if new command to replicate:
            #     replicate in other replicas
            # else:
            #     send heartbeat 
            #print("after while true grpc client raft.py")
            with self.raftmaininstance.logLock:
                pidx = self.raftmaininstance.replicatedlog.processedIndex
                loglen = len(self.raftmaininstance.replicatedlog.log)
            if pidx < loglen-1:
                # send appendEntries as seaprate threads   
                # everytime we get a success response from the grpc.
                # create grpc append entries thread and start it

                # for i in len(range(majority)):
                #     t.join()
                print("Got new append Entry")

                futurelist = [self.threadpoolexecutor.submit(self.__appendEntriesThread, followerNodePort=nodePort, id=random.randint(0,10000)) for nodePort in self.raftmaininstance.othernodes]
                
                print("len of future list raft.py",len(futurelist))
                with self.raftmaininstance.logLock:
                    self.raftmaininstance.replicatedlog.processedIndex += 1
                
                # TODO check for numCompleteVar
                print("Broadcast new entry to network")
                print("Majority occurs when ::"+ str(math.ceil(len(self.raftmaininstance.othernodes)/2)) +" approve")
                for fidx in range(math.ceil(len(self.raftmaininstance.othernodes)/2)):
                    out = futurelist[fidx].result() # always returns True?
                    print("Got result from RPC Server:: "+ str(out))
                # replicated in majority, increment commit index
                with self.raftmaininstance.logLock:
                    # commit
                    print("Commit new entry to StateMachine")
                    cmtIdx =self.raftmaininstance.replicatedlog.commitIndex
                    print("key::"+ self.raftmaininstance.replicatedlog.log[cmtIdx].key)
                    print("value::"+ self.raftmaininstance.replicatedlog.log[cmtIdx].value)
                    self.raftmaininstance.db.Put(bytearray(self.raftmaininstance.replicatedlog.log[cmtIdx].key, 'utf-8'), bytearray(self.raftmaininstance.replicatedlog.log[cmtIdx].value, 'utf-8'))
                    self.raftmaininstance.replicatedlog.commitIndex += 1
    
    def __appendEntriesThread(self, followerNodePort, id):
        # implement append entries RPC logic
        # get log command from followerPrevIdx
        # send appendEntriesRPC
        # if success, return True
        # elif timeout : retry
        # elif failure : decrement self.nextIndices[followerNodePort] and retry
        print("__appendEntriesThread start")
        response = raft_pb2.AppendEntriesResponse(term=1, success=False)
        while not response.success: #need to change condition will fail if myFollowerNextIdx was 0 and it accepted and current idx  =10
            with self.raftmaininstance.logLock:
                myFollowerNextIdx = self.nextIndices[followerNodePort]
                entry = self.raftmaininstance.replicatedlog.log[myFollowerNextIdx]
                cmtIdx =  self.raftmaininstance.replicatedlog.commitIndex
                prevTerm = self.raftmaininstance.replicatedlog.log[myFollowerNextIdx-1].term if myFollowerNextIdx != 0 else -1
            print("__appendEntriesThread checkpoint 1")
            with grpc.insecure_channel(followerNodePort) as channel:
                stub = raft_pb2_grpc.RaftStub(channel)
                lgent = raft_pb2.LogEntry(command=entry.command, key=entry.key, value=entry.value, term=entry.term)
                try:
                    print("__appendEntriesThread checkpoint 2")
                    response = stub.AppendEntries(raft_pb2.AppendEntriesRequest(prevlogindex=myFollowerNextIdx-1, previousterm=prevTerm, 
                                entries= [lgent], commitindex=cmtIdx, currentterm=1), timeout=1)
                    print("hoi")
                    print("Success Status::"+ str(response.success))
                    print("Response term::"+ str(response.term))
                    print("Follower nodeport", followerNodePort)
                    print("appendEntriesThreadID",id)

                    if not response.success:
                        self.nextIndices[followerNodePort] -= 1
                    else:
                        self.nextIndices[followerNodePort] += 1

                except Exception as e:
                    print(e)
                    continue
        print("__appendEntriesThread checkpoint 3")
        return True  

class RaftMain():
    def __init__(self, othernodes, leveldbinstance, raftPort):
        # intializing data members
        self.replicatedlog = ReplicatedLog()
        from copy import deepcopy
        self.othernodes = deepcopy(othernodes)
        self.currentTerm = 1
        self.db = leveldbinstance
        self.logLock = threading.Lock()
        # Creating client and Server threads
        self.grpcServer = RaftGRPCServer(self,raftPort)
        self.grpcServer.createGRPCServerThread()
        self.grpcClient = RafrGRPCClient(self)
        self.grpcClient.createGRPCClientThread()
        
        # TODO create heartbeat thread if state = leader
    
    def addCommandToReplicatedLog(self, entry):
        # acquire lock for replicated log
        # return index where entry is appended
        print("adding the request to replicated log")
        retval = 0
        with self.logLock:
            self.replicatedlog.append(entry)
            retval = len(self.replicatedlog.log)-1
            print("length of replicated log:: " + str(len(self.replicatedlog.log)))
        return retval
    
    def getCommitIndex(self):
        retval = 0
        with self.logLock:
            retval = self.replicatedlog.commitIndex
        return retval


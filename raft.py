from concurrent import futures
import enum
import grpc
import raft_pb2_grpc
import raft_pb2

import threading
import math
import random
import time
from enum import Enum

from datetime import datetime


class Role(Enum):
    LEADER = 1
    CANDIDATE = 2
    FOLLOWER = 3


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
        self.requestVotesthreadpool = futures.ThreadPoolExecutor(max_workers=len(self.raftmaininstance.othernodes))
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

        #lastContactedTime for request Vote.
        with self.raftmaininstance.logLock:
            self.raftmaininstance.lastContactedTime = datetime.now()
            print("replicated log len APpendEntries Raft server", len(self.raftmaininstance.replicatedlog.log))

        with self.raftmaininstance.logLock:
            myCurrTerm = self.raftmaininstance.currentTerm

        if request.currentterm < myCurrTerm:
            return raft_pb2.AppendEntriesResponse(success=False, term=myCurrTerm)
        
        if len(request.entries) >0:
                print("request.prevlogindex", str(request.prevlogindex))
                print("len(request.entries)",len(request.entries))
                print("request.entries.key", str(request.entries[0].key))
                print("request.entries.value",  str(request.entries[0].value))
        else:
            print("received heartbeat request")
            return raft_pb2.AppendEntriesResponse(success=True, term=myCurrTerm)
        
        with self.raftmaininstance.logLock:
            loglen = len(self.raftmaininstance.replicatedlog.log)
            if request.prevlogindex <= loglen-1:
                self.raftmaininstance.replicatedlog.log = self.raftmaininstance.replicatedlog.log[:request.prevlogindex+1]
            else:
                return raft_pb2.AppendEntriesResponse(success=False, term=myCurrTerm)
      

        with self.raftmaininstance.logLock:
            #Need to check request.prevlogindex!=-1 condition is safe
            if request.prevlogindex>0 and request.previousterm != self.raftmaininstance.replicatedlog.log[request.prevlogindex].term:
                return raft_pb2.AppendEntriesResponse(success=False, term=myCurrTerm)
            elif len(request.entries)>0:
                # Should we increase processedIdx, adding this for now to avoid client thread getting called
                self.raftmaininstance.replicatedlog.processedIndex+=1
                self.raftmaininstance.replicatedlog.append(ReplicatedLogEntry(request.entries[0].key, request.entries[0].value))

        
        with self.raftmaininstance.logLock:
            myCommitIdx = self.raftmaininstance.replicatedlog.commitIndex
            print("request.commitindex:: " + str(request.commitindex))
            print("myCommitIdx:: " + str(myCommitIdx))
            print("length of replicated log::" + str(len(self.raftmaininstance.replicatedlog.log)))
            print("raft main instance obj :", self.raftmaininstance)
            while myCommitIdx < request.commitindex and myCommitIdx < len(self.raftmaininstance.replicatedlog.log):
                self.raftmaininstance.db.Put(
                    bytearray(self.raftmaininstance.replicatedlog.log[myCommitIdx].key, 'utf-8'), 
                    bytearray(self.raftmaininstance.replicatedlog.log[myCommitIdx].value, 'utf-8'))
                myCommitIdx += 1
                self.raftmaininstance.replicatedlog.commitIndex += 1
        
        return raft_pb2.AppendEntriesResponse(success=True, term=myCurrTerm)
    
    def dbGetKey(self,key):
        try:
            value = self.raftmaininstance.db.Get(bytearray(key, 'utf-8'))
            return value
        except KeyError:
            return None


    def RequestVotes(self,request,context):
        '''
            1) candidate term > my current term 
                

            2) if candiate term >= my current term 
                if( leader ) then become follower
                    if(vote grated != -1 and candidate last log is as completed as the local)
                        grant vote and store in the DB.

                if(candidate) then become follower

                if(vote grated != -1 and candidate last log is as completed as the local)
                    grant vote and store in the DB.
            3) else:
                    return back response with voteGranted as false
                    return response(voteGranted= False, term= myCurrentTerm)
        '''
        with self.raftmaininstance.logLock:
            myCurrentTerm = self.raftmaininstance.currentTerm
            if request.currentterm >= myCurrentTerm:
                self.raftmaininstance.currentTerm  = request.currentterm
                if self.raftmaininstance.role == Role.LEADER or self.raftmaininstance.role == Role.FOLLOWER :
                    self.raftmaininstance.role == Role.FOLLOWER
                    votedFor = self.dbGetKey('votedFor').decode() if self.dbGetKey('votedFor') != None else -1
                    votedTerm = int(self.dbGetKey('votedTerm').decode()) if self.dbGetKey('votedTerm') != None else -1
                    lastLogIndex = self.raftmaininstance.replicatedlog.processedIndex
                    lastLog = self.raftmaininstance.replicatedlog.log[lastLogIndex] if lastLogIndex != -1 else None
                    if((votedTerm == None or votedTerm < request.currentterm ) and 
                       (lastLog == None or (lastLog.term < request.lastLogTerm or (lastLog.term == request.lastLogTerm and lastLogIndex<=request.lastLogIndex)))):
                        self.raftmaininstance.db.Put(
                            bytearray('votedFor', 'utf-8'), 
                            bytearray(request.candidateId, 'utf-8'))
                        self.raftmaininstance.db.Put(
                            bytearray('votedTerm', 'utf-8'), 
                            bytearray(str(request.currentterm), 'utf-8'))
                        return raft_pb2.RequestVoteResponse(voteGranted=True,term = self.raftmaininstance.currentTerm)
                    else:
                        return raft_pb2.RequestVoteResponse(voteGranted=False,term = self.raftmaininstance.currentTerm)
                else:
                    self.raftmaininstance.role == Role.FOLLOWER
                    return raft_pb2.RequestVoteResponse(voteGranted=False,term = self.raftmaininstance.currentTerm)
            else:
                return raft_pb2.RequestVoteResponse(voteGranted=False,term = self.raftmaininstance.currentTerm)
                  


        
        #pass



    def __sendRequestVotes(self,followerNodePort,requestVoteInput):
        count = 10
        while(count>0):
            try:
                 with grpc.insecure_channel(followerNodePort) as channel:
                    stub = raft_pb2_grpc.RaftStub(channel)
                    response = stub.RequestVotes(requestVoteInput)
                    return response
            except Exception as e:
                print(e)
            count = count-1
        pass


    def checkCandidate(self):
        while(True):
            candidateFlag = False
            requestVoteInput = None
            with self.raftmaininstance.logLock:
                difference_seconds = (datetime.now() - self.raftmaininstance.lastContactedTime).total_seconds()
                if (self.raftmaininstance.role == Role.FOLLOWER  and (difference_seconds > self.raftmaininstance.electionTimer)):
                    self.raftmaininstance.role = Role.CANDIDATE
                    self.raftmaininstance.currentTerm = self.raftmaininstance.currentTerm+1
                    candidateId = self.raftmaininstance.candidateId
                    currentterm=self.raftmaininstance.currentTerm
                    #self voting
                    self.raftmaininstance.db.Put(
                            bytearray('votedFor', 'utf-8'), 
                            bytearray(candidateId, 'utf-8'))
                    self.raftmaininstance.db.Put(
                        bytearray('votedTerm', 'utf-8'), 
                        bytearray(str(currentterm), 'utf-8'))

                    lastLogIndex = self.raftmaininstance.replicatedlog.processedIndex
                    lastLogTerm = self.raftmaininstance.replicatedlog.log[lastLogIndex].term if lastLogIndex != -1 else -1
                    requestVoteInput = raft_pb2.RequestVoteRequest(candidateId=candidateId, currentterm=currentterm, lastLogIndex=lastLogIndex, lastLogTerm=lastLogTerm)
                    candidateFlag = True

            if candidateFlag :
                print("broadcasting request vote")
                requestVoteThreads = [self.requestVotesthreadpool.submit(self.__sendRequestVotes,followerNodePort = nodePort, requestVoteInput =requestVoteInput ) for nodePort in self.raftmaininstance.othernodes]
                majority = math.ceil(len(self.raftmaininstance.othernodes)/2)
                for fidx in range(len(self.raftmaininstance.othernodes)):
                    out = requestVoteThreads[fidx].result() # always returns True?
                    if(out != None and out.voteGranted == True):
                        majority = majority-1
                    print("Got result from Request Vote RPC Server:: "+ str(out))
                    if(majority == 0):
                        print("Elected as Leader")
                        with self.raftmaininstance.logLock:
                            self.raftmaininstance.role = Role.LEADER
                            nextIndex = self.raftmaininstance.replicatedlog.processedIndex+1
                            self.raftmaininstance.grpcClient.nextIndices = {k: nextIndex for k in self.raftmaininstance.othernodes}
                            
                            #start heart beats
                            _heartBeatThread = threading.Thread(target=self.raftmaininstance.grpcClient.grpcClientHeartBeatThread, args=[random.randint(10000,20000)])
                            _heartBeatThread.start()
                        break
            with self.raftmaininstance.logLock:
                if self.raftmaininstance.role == Role.CANDIDATE:
                    self.raftmaininstance.role= Role.FOLLOWER
                    self.raftmaininstance.electionTimer = random.random()*10+20
                    self.raftmaininstance.lastContactedTime = datetime.now()
        pass



    def createGRPCServerThread(self):
        _thread = threading.Thread(target= self.__grpcServerThread)
        _thread.start()

        #Trying to create a new request vote thread parallel with the server thread
        requestVotethread = threading.Thread(target=self.checkCandidate)
        requestVotethread.start()


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
        self.threadpoolexecutor = futures.ThreadPoolExecutor(max_workers=10)
        self.heartbeatthreadpool = futures.ThreadPoolExecutor(max_workers=len(self.raftmaininstance.othernodes))
        self.nextIndices = {k:0 for k in self.raftmaininstance.othernodes}  # move it to appropriate function when candidate becomes leader
        self.RaftGRPCClientLock = threading.Lock()

    def createGRPCClientThread(self):
        _appendEntriesThread = threading.Thread(target=self.__grpcClientThread, args=[random.randint(10000,20000)])
        _heartBeatThread = threading.Thread(target=self.grpcClientHeartBeatThread, args=[random.randint(10000,20000)])
        _appendEntriesThread.start()
        _heartBeatThread.start()
        #_thread.join()
    
    def __grpcClientThread(self, idx):
        print("__grpcClientThread idx ::", idx)
        while (True):
            # if new command to replicate:
            #     replicate in other replicas
            # else:
            #     send heartbeat 
            #print("welcome", self.raftmaininstance.role)

            with self.raftmaininstance.logLock:
                pidx = self.raftmaininstance.replicatedlog.processedIndex
                loglen = len(self.raftmaininstance.replicatedlog.log)
                role = self.raftmaininstance.role
            if role == Role.LEADER and pidx < loglen-1:
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
                    print("Got result from Append Entries RPC Server:: "+ str(out))
                # replicated in majority, increment commit index
                with self.raftmaininstance.logLock:
                    # commit
                    print("Commit new entry to StateMachine")
                    cmtIdx =self.raftmaininstance.replicatedlog.commitIndex
                    self.raftmaininstance.db.Put(bytearray(self.raftmaininstance.replicatedlog.log[cmtIdx].key, 'utf-8'), bytearray(self.raftmaininstance.replicatedlog.log[cmtIdx].value, 'utf-8'))
                    self.raftmaininstance.replicatedlog.commitIndex += 1

    def grpcClientHeartBeatThread(self, idx):
        print("grpcClientHeartBeatThread idx", idx)
        with self.raftmaininstance.logLock:
            role = self.raftmaininstance.role
            if role == Role.LEADER:
                print("submiting new jobs")
                heartBeatfuturelist = [self.heartbeatthreadpool.submit(self.__appendEntriesThread, followerNodePort=nodePort, id=random.randint(0,10000), isHeartBeat= True) for nodePort in self.raftmaininstance.othernodes]

    # def __appendEntriesThreadWrapper(self,followerNodePort, id, isHeartBeat=False):
    #     try:
    #         self.__appendEntriesThread(followerNodePort, id, isHeartBeat)
    #     except Exception as e:
    #         print(followerNodePort,"     ",e,"      ", isHeartBeat) 
    
    def __appendEntriesThread(self, followerNodePort, id, isHeartBeat=False):
        # implement append entries RPC logic
        # get log command from followerPrevIdx
        # send appendEntriesRPC
        # if success, return True
        # elif timeout : retry
        # elif failure : decrement self.nextIndices[followerNodePort] and retry

        response = raft_pb2.AppendEntriesResponse(term=1, success=False)
        while ( isHeartBeat or (not response.success)): #need to change condition will fail if myFollowerNextIdx was 0 and it accepted and current idx  =10
            try:
                with self.raftmaininstance.logLock:
                    myFollowerNextIdx = self.nextIndices[followerNodePort]
                    if myFollowerNextIdx >= len(self.raftmaininstance.replicatedlog.log) and not isHeartBeat:
                        break
                    entry = self.raftmaininstance.replicatedlog.log[myFollowerNextIdx] if not isHeartBeat else None
                    cmtIdx =  self.raftmaininstance.replicatedlog.commitIndex
                    prevTerm = self.raftmaininstance.replicatedlog.log[myFollowerNextIdx-1].term if myFollowerNextIdx != 0 and not isHeartBeat else -1
                prevlogidx = myFollowerNextIdx-1 if not isHeartBeat else -1
            except Exception as e:
                print(prevTerm,"         ", entry,"       ",myFollowerNextIdx,"    ",e)
                continue

            with grpc.insecure_channel(followerNodePort) as channel:
                stub = raft_pb2_grpc.RaftStub(channel)
                lgent = [raft_pb2.LogEntry(command=entry.command, key=entry.key, value=entry.value, term=entry.term)] if not isHeartBeat else []         
                try:
                    print("triggering request for followerNodePort",followerNodePort)
                    if(isHeartBeat):
                        time.sleep(5)
                    response = stub.AppendEntries(raft_pb2.AppendEntriesRequest(prevlogindex=prevlogidx, previousterm=prevTerm, 
                                entries= lgent, commitindex=cmtIdx, currentterm=1), timeout=1)
                    #print("followerNodePort", followerNodePort, "response.success", response.success,"response.term", response.term, "isHeartBeat", isHeartBeat)
                    with self.raftmaininstance.logLock:
                        if self.raftmaininstance.role != Role.LEADER and isHeartBeat:
                            isHeartBeat = False
                        if  not response.success:
                            if not isHeartBeat:
                                self.nextIndices[followerNodePort] -= 1
                        else:
                            if not isHeartBeat:
                                #print("incrementing followerNodePort", followerNodePort , "next index to:", self.nextIndices[followerNodePort]+1, "isHeartBeat", isHeartBeat, " len of replicated log",len(self.raftmaininstance.replicatedlog.log), "idx", id )
                                self.nextIndices[followerNodePort] += 1
                                if self.nextIndices[followerNodePort] < len(self.raftmaininstance.replicatedlog.log):
                                    response.success = False 
                except Exception as e:
                    time.sleep(1)
                    print(followerNodePort,"            ",e,"          ", isHeartBeat)
                    continue
        return True  

class RaftMain():
    def __init__(self, othernodes, leveldbinstance, raftPort,candidateId):
        # intializing data members
        self.replicatedlog = ReplicatedLog()
        from copy import deepcopy
        self.othernodes = deepcopy(othernodes)
        self.currentTerm = 1
        self.db = leveldbinstance       
        self.role = Role.LEADER if(raftPort == "30001") else Role.FOLLOWER
        print("role", self.role)
        self.logLock = threading.Lock()

        #If we didn't get any append entry for this much time then we will start an election.
        self.electionTimer = random.random()*10+20
        self.lastContactedTime = datetime.now()
        self.candidateId = candidateId

        # Creating client and Server threads
        self.grpcClient = RafrGRPCClient(self)
        self.grpcClient.createGRPCClientThread()
        self.grpcServer = RaftGRPCServer(self,raftPort)
        self.grpcServer.createGRPCServerThread()
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


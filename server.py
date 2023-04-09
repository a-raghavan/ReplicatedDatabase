from concurrent import futures
import logging

import grpc
import database_pb2
from database_pb2 import KVpair
import database_pb2_grpc
import leveldb
import shutil

import raft
from time import sleep

import signal
import sys
import json
from types import SimpleNamespace

count = 0
otherReplicas = []

class Database(database_pb2_grpc.DatabaseServicer):
    def __init__(self, raftPort,candidateId):
        # delete folder if exists - Remove after testing
        path ='./{}_db'.format(raftPort)
        #shutil.rmtree(path, ignore_errors=True)
        self.db = leveldb.LevelDB(path)
        self.raftinstance = raft.RaftMain(otherReplicas, self.db, raftPort,candidateId)
        try:
            rl = self.db.Get(bytearray("replicatedlog", 'utf-8'))
            print("before log import -", rl.decode())
            self.raftinstance.replicatedlog = json.loads(rl.decode(), object_hook=lambda d: SimpleNamespace(**d))
            print("replicated log import -", self.raftinstance.replicatedlog[0])

        except:
            pass
        signal.signal(signal.SIGINT, self.saveReplicatedLogAndKill)
    
    def saveReplicatedLogAndKill(self, sig, frame):
        global count
        if count != 0:
            sys.exit(0)
        count = 1
        print("before json dumps - ", self.raftinstance.replicatedlog)
        y = json.dumps(self.raftinstance.replicatedlog, cls=RLEncoder)
        print("replicated log json dump =", y)
        self.db.Put(bytearray("replicatedlog", 'utf-8'), bytearray(y, 'utf-8'))
        sys.exit(0) 

    def Get(self, request, context):
        print("Get request received at server with key = %s" % (request.key))
        try:
            val = self.db.Get(bytearray(request.key, 'utf-8'))
        except Exception as e:
            return database_pb2.GetReply(errormsg=str(e), value="")
        return database_pb2.GetReply(errormsg="", value=val.decode())

    def Put(self, request, context):
        # RAFT HERE, put in db only upon commit
        #self.db.Put(bytearray(request.key, 'utf-8'), bytearray(request.value, 'utf-8'))
        #return database_pb2.PutReply(errormsg="")
        print("Put request from client ::  key :"+ request.key +" val:"+ request.value)
        if self.raftinstance.role == raft.Role.LEADER:
            retIndex = self.raftinstance.addCommandToReplicatedLog(raft.ReplicatedLogEntry(request.key, request.value))
            # polling
            # while self.raftinstance.commitIndex < retIndex:
            #   pass
            # Get result from raft module, return as GRPC response back to client
            print("returnIndex for current request :: "+ str(retIndex))
            print("raftInstanceCoomitIndex:: "+ str(self.raftinstance.getCommitIndex()))
            while self.raftinstance.getCommitIndex() <= retIndex:
                if self.raftinstance.role != raft.Role.LEADER:
                    return database_pb2.PutReply(errormsg="Contact {}".format(self.raftinstance.LeaderIP))
                sleep(1)
            print("replicated log len in server.py", len(self.raftinstance.replicatedlog.log))
            print("Done with PUT Command Successfully")
            return database_pb2.PutReply(errormsg="")
        else:
            return database_pb2.PutReply(errormsg="Contact {}".format(self.raftinstance.LeaderIP))

    def GetAllKeys(self, request, context):
        print("GetAllKeys request received ")
        result = []
        try:
            for key, value in self.db.RangeIter(include_value=True):
                if key.decode() != 'replicatedlog' and key.decode() != 'votedFor' and key.decode() != 'votedTerm':
                    result.append(database_pb2.KVpair(key=key.decode(), value=value.decode()))
        except Exception as e:
            print(e)
            return database_pb2.GetAllKeysReply(errormsg=str(e), KVpairs=[], value = "",role= "", entries =[])
        
        role = str(self.raftinstance.role)
        entries = []
        for log in self.raftinstance.replicatedlog.log:
            entries.append(database_pb2.LogEntry(command = log.command, key = log.key, value = log.value, term = log.term))
        return database_pb2.GetAllKeysReply(errormsg="", KVpairs=result, role= role, entries =entries)

class RLEncoder(json.JSONEncoder):
    def default(self, obj):
            ret = obj.__dict__
            ret['log'] = [x.__dict__ for x in ret['log']]
            return ret               
        

def serve(port,raftPort,candidateId):
    # port = '50051'
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    database_pb2_grpc.add_DatabaseServicer_to_server(Database(raftPort,candidateId), server)
    server.add_insecure_port('[::]:' + port)
    server.start()
    print("Server started, listening on " + port)
    server.wait_for_termination()

def getMyIPAddress():
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    return s.getsockname()[0]

if __name__ == '__main__':
    print(grpc.__version__)
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('-sp', '--serverport', help='Replicated server launch port', required=True)
    parser.add_argument('-rp', '--raftport', help='Raft server launch port', required=True)
    parser.add_argument('-n', '--nodes', nargs='*', help='node-ports of all participating nodes (space separated). e.g. -n 10.0.0.1:5001 10.0.0.1:5002 10.0.0.1:5003', required=True)
    args = parser.parse_args()
    
    myIP = getMyIPAddress()
    for nodeport in args.nodes:
        # if nodeport.split(":")[0] != myIP:
        #     otherReplicas.append(nodeport)
        if args.raftport != nodeport.split(":")[1]:
            otherReplicas.append(nodeport)
        else:
            myIP=nodeport.split(":")[0]

    logging.basicConfig()
    serve(args.serverport, args.raftport,myIP+":"+str(args.raftport))
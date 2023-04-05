from concurrent import futures
import logging

import grpc
import database_pb2
import database_pb2_grpc
import leveldb
import shutil

import raft
from time import sleep

otherReplicas = []

class Database(database_pb2_grpc.DatabaseServicer):
    def __init__(self, raftPort):
        # delete folder if exists - Remove after testing
        path ='./{}_db'.format(raftPort)
        shutil.rmtree(path, ignore_errors=True)
        self.db = leveldb.LevelDB(path)
        self.raftinstance = raft.RaftMain(otherReplicas, self.db, raftPort)

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
        retIndex = self.raftinstance.addCommandToReplicatedLog(raft.ReplicatedLogEntry(request.key, request.value))
        # polling
        # while self.raftinstance.commitIndex < retIndex:
        #   pass
        # Get result from raft module, return as GRPC response back to client
        print("returnIndex for current request :: "+ str(retIndex))
        print("raftInstanceCoomitIndex:: "+ str(self.raftinstance.getCommitIndex()))
        while self.raftinstance.getCommitIndex() <= retIndex:
            sleep(1)
        print("replicated log len in server.py", len(self.raftinstance.replicatedlog.log))
        print("Done with PUT Command Successfully")
        return database_pb2.PutReply(errormsg="")
        

def serve(port,raftPort):
    # port = '50051'
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    database_pb2_grpc.add_DatabaseServicer_to_server(Database(raftPort), server)
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
    logging.basicConfig()
    serve(args.serverport, args.raftport)
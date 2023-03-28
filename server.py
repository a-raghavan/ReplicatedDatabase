from concurrent import futures
import logging

import grpc
import database_pb2
import database_pb2_grpc
import leveldb

import raft
from time import sleep

otherReplicas = []

class Database(database_pb2_grpc.DatabaseServicer):
    def __init__(self):
        self.db = leveldb.LevelDB('./db')
        self.raftinstance = raft.RaftMain(otherReplicas, self.db)

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

        retindex = self.raftinstance.addCommandToReplicatedLog(raft.ReplicatedLogEntry(request.key, request.value))
        # polling
        # while self.raftinstance.commitIndex < retIndex:
        #   pass
        # Get result from raft module, return as GRPC response back to client
        while self.raftinstance.getCommitIndex() < retIndex:
            sleep(1)
        return database_pb2.PutReply(errormsg="")
        

def serve():
    port = '50051'
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    database_pb2_grpc.add_DatabaseServicer_to_server(Database(), server)
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
    
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('-n', '--nodes', nargs='+', help='node-ports of all participating nodes (space separated). e.g. -n 10.0.0.1:5001 10.0.0.1:5002 10.0.0.1:5003', required=True)
    args = parser.parse_args()
    
    myIP = getMyIPAddress()

    for nodeport in args.nodes:
        if nodeport.split(":")[0] != myIP:
            otherReplicas.append(nodeport)
    
    logging.basicConfig()
    serve()
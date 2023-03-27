from concurrent import futures
import logging

import grpc
import database_pb2
import database_pb2_grpc
import leveldb

import raft
from time import sleep

class Database(database_pb2_grpc.DatabaseServicer):
    def __init__(self):
        self.db = leveldb.LevelDB('./db')
        self.raftinstance = raft.RaftMain()

    def Get(self, request, context):
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


if __name__ == '__main__':
    logging.basicConfig()
    serve()
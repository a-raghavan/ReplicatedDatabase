import logging
import grpc
import database_pb2
import database_pb2_grpc


def run():
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = database_pb2_grpc.DatabaseStub(channel)
        response = stub.Put(database_pb2.PutRequest(key='akshay', value='awesome'))
        response = stub.Get(database_pb2.GetRequest(key='akshay'))
        print(response.value)
        response = stub.Get(database_pb2.GetRequest(key='ll'))
        print(response.errormsg)

if __name__ == '__main__':
    logging.basicConfig()
    run()

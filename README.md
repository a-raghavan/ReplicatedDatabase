# ReplicatedDatabase
Implementing a replicated database using Raft

## Dependencies:
```sh
pip3 install virtualenv
pip3 install grpcio
pip3 install grpcio-tools 
pip3 install leveldb
```
## Building
### Create python virtual env
```sh
python3 -m virtualenv venv
source venv/bin/activate
```
### Build protobuffs 
```sh
python3 -m grpc_tools.protoc -I./protos --python_out=. --pyi_out=. --grpc_python_out=. ./protos/database.proto
python3 -m grpc_tools.protoc -I ./protos --python_out=. --pyi_out=. --grpc_python_out=. ./protos/*
```
### Run server
```sh
python3 server.py --nodes "IP address:port"
```
### Run client
```sh
python3 client.py
```

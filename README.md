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
python3 server.py -n 10.10.1.6:30001 10.10.1.6:30002 10.10.1.6:30003 -sp 50001 -rp 30001
python3 server.py -n 10.10.1.6:30001 10.10.1.6:30002 10.10.1.6:30003 -sp 50002 -rp 30002
python3 server.py -n 10.10.1.6:30001 10.10.1.6:30002 10.10.1.6:30003 -sp 50003 -rp 30003
```
### Run client
```sh
python3 client.py
```

### RUN UX
cd ReplicatedDatabase/ReplicatedDbDashboard
npm install
node app
![image](https://user-images.githubusercontent.com/23165664/231079397-0abd369d-7d28-467a-823d-a2bd09f52785.png)

var express = require('express');
var bodyParser = require('body-parser');
var appSettings = require('./Appsettings.json');


var app = express();

// Use Images icon
app.use(express.static(__dirname + '/public'));

//using ejs
app.set('view engine', 'ejs');

app.use(bodyParser.urlencoded({ extended: true }));

//using grpc
var PROTO_PATH = __dirname + './../protos/database.proto';
var grpc = require('@grpc/grpc-js');
var protoLoader = require('@grpc/proto-loader');
var packageDefinition = protoLoader.loadSync(
    PROTO_PATH,
    {keepCase: true,
     longs: String,
     enums: String,
     defaults: true,
     oneofs: true
    });
var database_proto = grpc.loadPackageDefinition(packageDefinition).database;
var grpcClients=[]

var grpcdata ={}


//Api Calls
app.get('/', async function (req, res) {
    if(!data){
        receiveGrpcData()
        console.log(grpcdata)
    }
    res.render('pages/index', {data: grpcdata});
});

app.post('/submitPutRequest', function(req, res, next){
    grpcPutRequest(req.body.ipaddr,req.body.key,req.body.value)
    res.render('pages/index', {data: grpcdata});
 });


//Set express app properties
app.set('port', process.env.PORT || 8000);

var server = app.listen(app.get('port'),async function () {
    console.log('server up and running' + server.address().port);
    setUpGrpcClient()
    setInterval(receiveGrpcData, 10000);
});


function setUpGrpcClient(){
    for(data in appSettings){
        grpcClients.push(new database_proto.Database(appSettings[data], grpc.credentials.createInsecure()))
    }
}

function receiveGrpcData() {
    var promises =[] 
   
    for(data in appSettings){
        promises.push(
        new Promise((resolve, reject) => grpcClients[data].GetAllKeys({}, function(err, response) {
            if(err) {
              resolve({"KVpairs": [], errormsg: "Server down"})
            }
            resolve(response)        
        })))

    }

    Promise.all(promises).then((values) => {
        for(data in values){
            grpcdata[appSettings[data]]=values[data]
        }
    });

} 


function grpcPutRequest(ip, key, value) {
    for(data in appSettings){
        console.log(appSettings[data])
        console.log(ip)
        if(appSettings[data] == ip){
            console.log("yoo")
            grpcClients[data].Put({key: key, value: value }, function(err, response){
                console.log("received Data")
                console.log(response)
                console.log(err)
            })
        }
    }

} 






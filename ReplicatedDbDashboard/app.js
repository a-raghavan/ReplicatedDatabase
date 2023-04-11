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
    // if(!data){
        var promises=receiveGrpcData()
        Promise.all(promises).then((values) => {
            for(data in values){
                grpcdata[appSettings[data]]=values[data]
            }
            res.render('pages/index', {data: grpcdata, errormsg: req.query.errormsg, redirected: req.query.redirected});
        });
        //console.log(grpcdata)
    //}
});

app.get('/getTime', async function (req, res) {
    var count = req.query.numGets
    var promises= []
    var start = Date.now();
    while(count>0){   
       promises.push(grpcGetRequestTest("akshay"+count))
        count-=1
    }
    Promise.all(promises).then((values) => {
        result = {}
        successRequests = 0
        failureRequests= 0
        for(data in values){
            if(!data.errormsg){
                successRequests+=1
            }
            else{
                failureRequests+=1
            }
        }
        var end = Date.now();
        result['successRequests'] = successRequests
        result['failureRequests'] = failureRequests
        result['totalOperationTime'] = (end- start)/1000
        res.json(result)

    });
    
});

app.get('/getTimeSignleNode', async function (req, res) {
    var count = req.query.numGets
    var promises= []
    var start = Date.now();
    while(count>0){   
       promises.push(grpcGetRequestTest("akshay"+count))
        count-=1
    }
    Promise.all(promises).then((values) => {
        result = {}
        successRequests = 0
        failureRequests= 0
        for(data in values){
            if(!data.errormsg){
                successRequests+=1
            }
            else{
                failureRequests+=1
            }
        }
        var end = Date.now();
        result['successRequests'] = successRequests
        result['failureRequests'] = failureRequests
        result['totalOperationTime'] = (end- start)/1000
        res.json(result)

    });
    
});

app.get('/putTime', async function (req, res) {
    var count = req.query.numPuts
    var promises= []
    var start = Date.now();
    while(count>0){   
       promises.push(grpcPutRequestTest("akshay"+count, "awesome"+count))
        count-=1
    }
    Promise.all(promises).then((values) => {
        result = {}
        successRequests = 0
        failureRequests= 0
        for(data in values){
            if(!data.errormsg){
                successRequests+=1
            }
            else{
                failureRequests+=1
            }
        }
        var end = Date.now();
        result['successRequests'] = successRequests
        result['failureRequests'] = failureRequests
        result['totalOperationTime'] = (end-start)/1000
        res.json(result)
    });
});


app.get('/logs', async function (req, res) {

    var promises=receiveGrpcData()
    Promise.all(promises).then((values) => {
        for(data in values){
            grpcdata[appSettings[data]]=values[data]
        }
        res.render('pages/userIndex', {data: grpcdata, errormsg: req.query.errormsg, redirected: req.query.redirected});
    });
});


app.post('/submitPutRequest', function(req, res, next){
    grpcPutRequest(req.body.ipaddr,req.body.key,req.body.value).then(data =>{
        if(!data.errormsg){
            res.redirect('/?redirected=True');
        }
        else{
            res.redirect('/?redirected=True&errormsg='+data.errormsg);
        }
    })
 });


//Set express app properties
app.set('port', process.env.PORT || 8000);

var server = app.listen(app.get('port'),async function () {
    console.log('server up and running' + server.address().port);
    setUpGrpcClient()
    setInterval(receiveGrpcData, 5000);
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
                console.log(err)
                resolve({"KVpairs": [], errormsg: "Server down", role: "Unknown", entries: []})
            }
            resolve(response)        
        })))

    }
    return promises
} 


function grpcPutRequest(ip, key, value) {
    for(data in appSettings){
        console.log(appSettings[data])
        console.log(ip)
        if(appSettings[data] == ip){
            console.log("yoo")
            return new Promise((resolve, reject) => grpcClients[data].Put({key: key, value: value }, function(err, response){
                if(err) {
                    console.log(err)
                    resolve({"KVpairs": [], errormsg: "Server down"})
                  }
                  resolve(response)        
            }))
        }
    }

} 

function getRandomInt(max) {
    return Math.floor(Math.random() * max);
}

function grpcGetRequestTest(key, value) {
    return new Promise((resolve, reject) => grpcClients[getRandomInt(appSettings.length)].Get({key: key}, function(err, response){
        if(err) {
            resolve({"value": "", errormsg: "Server down"})
            }
            resolve(response)        
    }))

} 

function grpcGetRequestTest(key, value) {
    return new Promise((resolve, reject) => grpcClients[0].Get({key: key}, function(err, response){
        if(err) {
            resolve({"value": "", errormsg: "Server down"})
            }
            resolve(response)        
    }))

} 

function grpcPutRequestTest(key, value) {
    return new Promise((resolve, reject) => grpcClients[0].Put({key: key, value: value }, function(err, response){
        if(err) {
            resolve({errormsg: "Server down"})
            }
            resolve(response)        
    }))
} 


// function grpcGetRequest(ip, key, value) {
//     for(data in appSettings){
//         console.log(appSettings[data])
//         console.log(ip)
//         if(appSettings[data] == ip){
//             console.log("yoo")
//             return new Promise((resolve, reject) => grpcClients[data].Put({key: key, value: value }, function(err, response){
//                 if(err) {
//                     //console.log(err)
//                     resolve({"KVpairs": [], errormsg: "Server down"})
//                   }
//                   resolve(response)        
//             }))
//         }
//     }
// } 



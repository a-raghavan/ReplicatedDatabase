import json
from collections import namedtuple
from types import SimpleNamespace

class person:
    def __init__(self):
        self.name = "LOL"

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

class RLEncoder(json.JSONEncoder):
    def default(self, obj):
        print("====",type(obj))
        ret = obj.__dict__
        ret['log'] = [x.__dict__ for x in ret['log']]
        #print(ret)
        return ret            

def customDecoder(ddict):
    if "log" in ddict:
        return namedtuple("ReplicatedLog", ddict.keys())(*ddict.values())
    else:
        return  namedtuple("ReplicatedLogEntry", ddict.keys())(*ddict.values())


a = ReplicatedLog()
a.append(ReplicatedLogEntry("key", "value"))
b = ReplicatedLog()
b.append(ReplicatedLogEntry("google", "sundar"))

# a Python object (dict):
x=a

print(x)
# convert into JSON:
y = json.dumps(x, cls=RLEncoder)

# the result is a JSON string:
print(y)
x = json.loads(y, object_hook=lambda d: SimpleNamespace(**d))
print(x)


y = json.dumps(x, cls=RLEncoder)
print(y)

x = json.loads(y, object_hook=lambda d: SimpleNamespace(**d))
print(x)

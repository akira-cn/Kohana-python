# coding=utf-8

import sys
import uuid
from types import *

class Handler():
    def __init__(self):
        self.rpc_instances = {}
    def execute(self, data):
        rpc_instances = self.rpc_instances;

        if('paths' in data): #set auto loading paths
            data['paths'].reverse()
            for i in range(len(data['paths'])):
                path = data['paths'][i] + 'classes'
                if(path not in sys.path):
                    sys.path.insert(1, path)
        
        #call the object instance func - {id, func, args[class, init]}
        if('id' in data):
            if(data['id'] in rpc_instances):    #the object has been created
                o = rpc_instances[data['id']]
            else:                               #create new object instance
                c = self.find_class(data['class'])
                o = apply(c, data['init'])
                rpc_instances[data['id']] = o  
            res =  apply(getattr(o, data['func']), data['args']) or ''  

        #call class func - {class, [func, args]}
        else:
            c = self.find_class(data['class'])
            #if not 'func', only to test wether the class exists or not
            if(not ('func' in data)): #TODO: get the detail info of the class?
                res = True
            else:
                res = apply(getattr(c, data['func']), data['args']) or ''
        
        if(type(res) is InstanceType):
            uid = str(uuid.uuid4())
            rpc_instances[uid] = res
            res = {'@id':uid, '@class':res.__class__.__name__, '@init':[]}   
        
        return {'err':'ok', 'data':res}

    def find_class(self, class_name):
        #resolve the path from class name like 'Model_Logic_Test'
        path = map(lambda s: s.lower(), class_name.split('_'))
        p = __import__(".".join(path))

        for i in range(len(path)):
            if(i > 0):
                p = getattr(p, path[i])
    
        return getattr(p, class_name)   
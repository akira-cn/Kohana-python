# coding=utf-8

import sys
import json
import traceback
import SocketServer
import uuid
from daemon import Daemon
from types import *

rpc_instances = {} #save obj instance
rpc_module_paths = [] #auto loading paths

class ThreadedTCPRequestHandler(SocketServer.BaseRequestHandler):
    def handle(self):
        while True:
            try:
                data = self.request.recv(2*1024*1024)
                if not data:
                    print('end')
                    break
                data = json.loads(data)

                if('paths' in data): #set auto loading paths
                    for i in range(len(rpc_module_paths),len(data['paths'])):
                        sys.path.append(data['paths'][i] + 'classes')
                        rpc_module_paths.append(data['paths'][i])
                
                #call the object instance func - {id, func, args[class, init]}
                if('id' in data):
                    if(data['func'] == '__destroy'):
                        if(data['id'] in rpc_instances):
                            rpc_instances.pop(data['id']) #if instance exists
                        res = True      #delete & restore
                    else:
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

                res = json.dumps({'err':'ok', 'data':res})  #+ str(len(rpc_instances.keys())) 

            except:
                res = ('error in ThreadedTCPRequestHandler :%s, res:%s' % (traceback.format_exc(), data))
                res = json.dumps({'err':'sys.socket.error', 'msg':res}) 
            res = str(len(res)).rjust(8, '0') + res 
            self.request.send(res)

    def find_class(self, class_name):
        #resolve the path from class name like 'Model_Logic_Test'
        path = map(lambda s: s.lower(), class_name.split('_'))
        p = __import__(".".join(path))

        for i in range(len(path)):
            if(i > 0):
                p = getattr(p, path[i])
    
        return getattr(p, class_name)

class ThreadedTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    pass

class Server(Daemon):        
    def conf(self, host, port):
        self.host = host
        self.port = port
        ThreadedTCPServer.allow_reuse_address = True
    def run(self):
        server = ThreadedTCPServer((self.host, self.port), ThreadedTCPRequestHandler)
        server.serve_forever()

if __name__ == '__main__':
    server = Server('/tmp/daemon-tortoise.pid')
    port = 1990
    if len(sys.argv) >= 3:
        port = sys.argv[2]
    server.conf('0.0.0.0', port) #change ip address if you want to call remotely
    if len(sys.argv) >= 2:
        if 'start' == sys.argv[1]:
            server.start()
        elif 'stop' == sys.argv[1]:
            server.stop()
        elif 'restart' == sys.argv[1]:
            server.restart()
        else:
            print("Unknown command")
            sys.exit(2)
        sys.exit(0)
    else:
        print("usage: %s start|stop|restart" % sys.argv[0])
        sys.exit(2)

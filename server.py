# coding=utf-8

import sys
import json
import traceback
import SocketServer
from daemon import Daemon

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
                
                #resolve the path from class name like 'Model_Logic_Test'
                path = map(lambda s: s.lower(), data['class'].split('_'))
                p = __import__(".".join(path))

                for i in range(len(path)):
                    if(i > 0):
                        p = getattr(p, path[i])
			
                c = getattr(p, data['class'])
		        
                #if not 'func', only to test wether the class exists or not
                if(not ('func' in data)): #TODO: get the detail info of the class?
                    res = '{"err":"ok", "data":true}'

                else:
                    #destroy the object instance if the php request end
                    if(data['func'] == '__destroy'):
                        rpc_instances.pop(data['id']) #if instance exists
                        res = 'item destroyed'      #delete & restore
		
                    else:
                        if(data['id'] in rpc_instances):    #the object has been created
                            o = rpc_instances[data['id']]
                        else:                               #create new object instance
                            o = apply(c, data['init'])
                            rpc_instances[data['id']] = o
                        res =  getattr(o, data['func'])(data['args']) or '' #str(len(rpc_instances.keys()))
                        res = json.dumps({'err':'ok', 'data':str(res)})

            except:
                res = ('error in ThreadedTCPRequestHandler :%s, res:%s' % (traceback.format_exc(), data))
                res = json.dumps({'err':'sys.socket.error', 'msg':res})
            res = str(len(res)).rjust(8, '0') + res
            self.request.send(res)

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
    server.conf('0.0.0.0', port) #change ip if you want to call remote
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

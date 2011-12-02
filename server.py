import sys
import json
import traceback
import SocketServer
from daemon import Daemon

rpc_instances = {}; #save obj instance
rpc_module_paths = [];

class ThreadedTCPRequestHandler(SocketServer.BaseRequestHandler):
    def handle(self):
        while True:
            try:
                data = self.request.recv(2*1024*1024)
                if not data:
                    print('end')
                    break
                data = json.loads(data)

                if('paths' in data): #only test if class exists or not
                    for i in range(len(rpc_module_paths),len(data['paths'])):
                        sys.path.append(data['paths'][i] + 'classes')
                        rpc_module_paths.append(data['paths'][i])

                path = map(lambda s: s.lower(), data['class'].split('_'));
                p = __import__(".".join(path))

                for i in range(len(path)):
                    if(i > 0):
                        p = getattr(p, path[i])
			
                c = getattr(p, data['class'])
		
                if(not ('func' in data)): #only test if class exists or not
                    res = '{"err":"ok"}'

                else:
                    if(data['func'] == '__destroy'):
                        rpc_instances.pop(data['id'])
                        res = 'item destroyed'
		
                    else:
                        if(data['id'] in rpc_instances):
                            o = rpc_instances[data['id']]
                        else:
                            o = apply(c, data['init'])
                            rpc_instances[data['id']] = o
                        res =  getattr(o, data['func'])(data['args']) or '' #str(len(rpc_instances.keys()))
                        res = json.dumps({'err':'ok', 'data':str(res)})

            except:
                res = ('error in ThreadedTCPRequestHandler :%s, res:%s' % (traceback.format_exc(), data))
                res = json.dumps({'err':'sys.socket.error', 'msg':res})
            res = str(len(res)).rjust(8, '0') + res
            self.request.send(res);

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
    server.conf('0.0.0.0', port)
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

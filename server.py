# coding=utf-8

import sys
import json
import traceback
import socket
from SocketServer import BaseRequestHandler, ThreadingTCPServer
from daemon import Daemon
import uuid
from types import *
from logger import logger

import select
import threading

logger = logger().instance()

class RequestHandler(BaseRequestHandler):
    def setup(self):
        logger.debug('setup')
        self.request.settimeout(60)
    def handle(self):
        rpc_instances = {}
        while True:
            try:
                data = self.request.recv(2*1024*1024)
                if not data:
                    break  #end
                data = json.loads(data)

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
                
                res = json.dumps({'err':'ok', 'data':res}) #+ str(len(rpc_instances.keys()))
                res = str(len(res)).rjust(8, '0') + res 
                self.request.send(res)
            except socket.timeout as err:
                res = ('error in RequestHandler :%s, res:%s' % (traceback.format_exc(), data))
                logger.debug(res)
                res = json.dumps({'err':'sys.socket.error', 'msg':format(err)})
                res = str(len(res)).rjust(8, '0') + res 
                self.request.send(res)
                self.request.close()
                break
            except Exception as err:
                res = ('error in RequestHandler :%s, res:%s' % (traceback.format_exc(), data))
                logger.debug(res)
                res = json.dumps({'err':'sys.socket.error', 'msg': format(err)})
                res = str(len(res)).rjust(8, '0') + res 
                self.request.send(res)
    def finish(self):
        logger.debug('finish')
        self.request.close()
    def find_class(self, class_name):
        #resolve the path from class name like 'Model_Logic_Test'
        path = map(lambda s: s.lower(), class_name.split('_'))
        p = __import__(".".join(path))

        for i in range(len(path)):
            if(i > 0):
                p = getattr(p, path[i])
    
        return getattr(p, class_name)

class EPollTCPServer(ThreadingTCPServer):
    __is_shut_down = threading.Event()
    def serve_forever(self, poll_interval=0.5):
        """Handle one request at a time until shutdown.

        Polls for shutdown every poll_interval seconds. Ignores
        self.timeout. If you need to do periodic tasks, do them in
        another thread.
        """
        self.__serving = True
        self.__is_shut_down.clear()

        epoll = select.epoll()
        epoll.register(self.fileno(), select.EPOLLIN | select.EPOLLET)
        
        try:
            while self.__serving:
                events = epoll.poll(poll_interval)
                for fileno, event in events:
                    if fileno == self.fileno():
                        try:
                            self._handle_request_noblock()
                        except socket.error:
                            return
        finally:
            epoll.unregister(self.fileno())
            epoll.close()
            self.__is_shut_down.set()

class Server(Daemon):        
    def conf(self, host, port):
        self.host = host
        self.port = port
        EPollTCPServer.allow_reuse_address = True
    def run(self):
        server = EPollTCPServer((self.host, self.port), RequestHandler)
        try:
            server.serve_forever()
        except Exception as err:
            logger.debug(traceback.format_exc())
    
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

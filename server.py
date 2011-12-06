# coding=utf-8

import sys
import json
import traceback
import socket
from SocketServer import BaseRequestHandler, ThreadingTCPServer
from daemon import Daemon

from handler import Handler

from logger import logger
logger = logger().instance()

class RequestHandler(BaseRequestHandler, Handler):
    def setup(self):
        logger.debug('setup')
        self.request.settimeout(60)
        self.rpc_instances = {}
    def handle(self):
        while True:
            try:
                data = self.request.recv(2*1024*1024)
                if not data:
                    break  #end
                data = json.loads(data)

                res = self.execute(data)
                
                logger.debug('instance count:' + str(len(self.rpc_instances.keys())))

                res = json.dumps(res) 
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

    def response(self, data):
        res = json.dumps(data)
        res = str(len(res)).rjust(8, '0') + res 
        self.transport.write(res)

class Server(Daemon):        
    def conf(self, host, port):
        self.host = host
        self.port = port
        ThreadingTCPServer.allow_reuse_address = True
    def run(self):
        server = ThreadingTCPServer((self.host, self.port), RequestHandler)
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

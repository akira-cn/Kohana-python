# coding=utf-8

import sys
import traceback
from daemon import Daemon

from twisted.internet import reactor
from twisted.internet.protocol import Protocol, Factory
from twisted.protocols.policies import TimeoutMixin

from handler import Handler

from logger import logger
logger = logger().instance()

import json

class PHPRequest(Protocol, TimeoutMixin, Handler):    
    def connectionMade(self):
        logger.debug('connection opened')
        self.setTimeout(self.factory.conn_timeout)
        self.clients = str(self.transport.getPeer().host)
        self.factory.connections = self.factory.connections + 1
        logger.debug('connections:' + str(self.factory.connections))
    
    def connectionLost(self,reason):
        self.setTimeout(None)
        self.factory.connections = self.factory.connections - 1
        logger.debug('connection closed:' + reason)
    
    def timeoutConnection(self):
        res = {'err' : 'sys.socket.error', 'msg':"timed out: %s" % self.clients}
        logger.debug("timed out: %s" % self.clients)
        self.response(res)
        self.transport.unregisterProducer()
        self.transport.loseConnection()

    def dataReceived(self,data):
        try:
            data = json.loads(data)
            res = self.execute(data)
            logger.debug('instance count:' + str(len(self.rpc_instances.keys())))
        except Exception as err:
            res = ('error in RequestHandler :%s, res:%s' % (traceback.format_exc(), data))
            logger.debug(res)
            res = {'err':'sys.socket.error', 'msg':format(err)}
        finally:
            self.response(res)
    
    def response(self, data):
        res = json.dumps(data)
        res = str(len(res)).rjust(8, '0') + res 
        self.transport.write(res)

class PHPRequestFactory(Factory):
    protocol = PHPRequest
    connections = 0
    def __init__(self, conn_timeout):
        self.conn_timeout = conn_timeout

class Server(Daemon):        
    def conf(self, host, port):
        self.host = host
        self.port = port 
    def run(self):
        try:
            logger.debug('run')
            factory = PHPRequestFactory(60)
            reactor.listenTCP(self.port, factory)
            reactor.run()
        except:
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
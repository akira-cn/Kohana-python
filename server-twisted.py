import sys
import traceback
from daemon import Daemon

from twisted.internet import reactor
from twisted.internet.protocol import Protocol, Factory
from twisted.protocols.policies import TimeoutMixin

import uuid
from types import *

from logger import logger
logger = logger().instance()

import json

class PHPRequest(Protocol, TimeoutMixin):    
    def connectionMade(self):
        logger.debug('connection opened')
        self.setTimeout(self.factory.conn_timeout)
        self.clients = str(self.transport.getPeer().host)
        self.factory.connections = self.factory.connections + 1
        self.rpc_instances = {}
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
            res = self.handle(data)
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

    def find_class(self, class_name):
        #resolve the path from class name like 'Model_Logic_Test'
        path = map(lambda s: s.lower(), class_name.split('_'))
        p = __import__(".".join(path))

        for i in range(len(path)):
            if(i > 0):
                p = getattr(p, path[i])
    
        return getattr(p, class_name)
        
    def handle(self, data):
        data = json.loads(data)
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
            factory = PHPRequestFactory(1)
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
<?php defined('SYSPATH') or die('No direct script access.');

class Socket_Instance{
	protected $_class;
	protected $_id;
	protected $_args; //构造函数参数
	protected $_server;
	
	public static $default_server = null;

	public function __construct($class, $args = array(), $server = null){
		if(!isset(self::$default_server)){
			if(!isset($server)){
				$server = new Socket_Server();
			}
			self::$default_server = $server;
		}
		else if(!isset($server)){
			$server = self::$default_server;
		}

		$this->_server = $server;
		$this->_class = $class;
		$this->_args = $args;
		$this->_id = 'i'.rand(0,99999999).preg_replace('/\./', '_', microtime(true).'');

		$server->instances[$this->_id] = $this;
	}

	protected static function _rpc_call($server, $data){
		$data = json_encode($data);
		$socket = $server->socket();
		$res = socket_write($socket, $data, strlen($data));
		if($res===false){
			return $server->_error('error socket_write'.socket_strerror(socket_last_error()));
		}
		$res = socket_read($socket, 1024, PHP_BINARY_READ);
		$result = substr($res, 8);
		$len = intval(substr($res, 0, 8));
		while(true){
			if($len != strlen($result)) {
				$result .= socket_read($socket, 1024, PHP_BINARY_READ);
			}else{
				break;
			}
		}
		$ret = json_decode($result, true);

		if($ret['err'] == 'sys.socket.error'){
			throw new Socket_Exception($result);
		}
		return $ret;	
	}

	public function __call($func, $args) {
		return self::_rpc_call($this->_server, 
			array('class' => $this->_class, 'init' => $this->_args, 'func' => $func, 'args' => $args, 'id' => $this->_id));
	}

	public static function find_class($class, $paths = array()){
		if(!isset(self::$default_server)){
			self::$default_server = new Socket_Server();
		}
		return self::_rpc_call(self::$default_server,array('class' => $class, 'paths' => $paths));	
	}

	public function __destruct(){
		if(isset($this->_server->instances[$this->_id])){
			$this->__destroy();
			unset($this->_server->instances[$this->_id]);
		}
	}
}
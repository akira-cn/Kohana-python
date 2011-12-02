<?php defined('SYSPATH') or die('No direct script access.');

class Socket_Server{
	private $_host;
	private $_port;
	private $_socket;
	private $_error;

	public $instances = array();
	
	function __construct($host = '127.0.0.1', $port = 1990) {
		$this->_host = $host;
		$this->_port = $port;
		$this->_connect();
	}

	private function _connect() {
		$sock = socket_create(AF_INET, SOCK_STREAM, SOL_TCP);
		if($sock === false){
			return $this->_error('error socket_create'.socket_strerror(socket_last_error()));
		}

		$ret = socket_connect($sock, $this->_host, $this->_port);
		if($ret === false){
			return $this->_error('error socket_connect'.socket_strerror(socket_last_error()));
		}
 
		$this->_socket = $sock;
	}
 

	public function socket(){
		return $this->_socket;
	}

	public function __destruct() {
		foreach($this->instances as $key => $instance){
			$instance->__destroy();
			unset($this->instances[$key]);
		}
		$socket = $this->_socket;
		socket_write($socket, '', 0);
		socket_close($socket);
	}

	private function _error($errMsg = '') {
		$this->_error = array(
			'err' => 'sys.socket.error',
			'msg' => $errMsg,
		);
		throw new Socket_Exception($errMsg);
	}
}
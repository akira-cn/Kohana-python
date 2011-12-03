<?php defined('SYSPATH') or die('No direct script access.');

/**
 * the socket instanc handle an unique object instance from the socket server
 *
 * @package    Python
 * @category   Socket
 * @author     akira.cn@gmail.com
 * @copyright  (c) 2011 WED Team
 * @license    http://kohanaframework.org/license
 */
class Socket_Instance{
	/**
	 * the class of the object instance
	 */
	protected $_class;
	/**
	 * unique identifier to hold the instance
	 */
	protected $_id;
	/**
	 * constructor arguments
	 */
	protected $_args; 
	/**
	 * socket client object
	 */
	protected $_client;
	
	/**
	 * default socket client
	 */
	public static $default_client = null;
	
	/**
	 * create a new socket instance to operate an object instance from the socket server 
	 *
	 * @param	String			$class	class name
	 * @param	Array			$args	construct arguments
	 * @param	Socket_Client	$client
	 */
	public function __construct($class, $args = array(), $client = null){
		if(!isset(self::$default_client)){
			if(!isset($client)){
				$client = new Socket_Client();
			}
			self::$default_client = $client;
		}
		else if(!isset($client)){
			$client = self::$default_client;
		}

		$this->_client = $client;
		$this->_class = $class;
		$this->_args = $args;
		$this->_id = uniqid('i',true);

		$client->instances[$this->_id] = $this;
	}
	
	/**
	 * make a rpc_call, send data to server
	 *
	 * @param	Socket_Client	$client
	 * @param	Array			$data
	 * @return	mixed	
	 */
	protected static function _rpc_call($client, $data){
		$data = json_encode($data);
		$socket = $client->socket();
		$res = socket_write($socket, $data, strlen($data));
		if($res===false){
			return $client->_error('error socket_write'.socket_strerror(socket_last_error()));
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
		return $ret['data'];	
	}
	
	/**
	 * call a function from remote server
	 *
	 * @param	String	$func	method name
	 * @param	Array	$args	method arguments
	 * @return	mixed
	 */
	public function __call($func, $args) {
		return self::_rpc_call($this->_client, 
			array('class' => $this->_class, 'init' => $this->_args, 'func' => $func, 'args' => $args, 'id' => $this->_id));
	}
	
	/**
	 * find a class from remote server
	 *
	 * @param	String	$class	class name
	 * @param	Array	$paths	root paths
	 * @return	boolean
	 */
	public static function find_class($class, $paths = array()){
		if(!isset(self::$default_client)){
			self::$default_client = new Socket_Client();
		}
		return self::_rpc_call(self::$default_client,array('class' => $class, 'paths' => $paths));	
	}

	/**
	 * remove the instances handled from the socket server
	 */	
	public function __destruct(){
		//if the client socket haven't been closed yet
		//destroy the object instance from the server 
		if(isset($this->_client) && isset($this->_client->instances[$this->_id])){
			$this->__destroy();
			unset($this->_client->instances[$this->_id]);
		}
	}
}
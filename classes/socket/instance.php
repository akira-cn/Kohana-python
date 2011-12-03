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
	 * unique identifier to hold the instance
	 */
	protected $_id;
	/**
	 * constructor arguments
	 */
	protected $_args; 
	
	/**
	 * socket client
	 */
	public static $client = null;
	
	/**
	 * create a new socket instance to operate an object instance from the socket server 
	 *
	 * @param	String			$class	class name
	 * @param	Array			$args	construct arguments
	 * @param	Socket_Client	$client
	 */
	public function __construct($args = array()){
		$this->_args = $args;
		$this->_id = uniqid('i',true);

		self::$client->instances[$this->_id] = $this;
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
		return unserialize($ret['data']);	
	}
	
	/**
	 * call a static function from remote server
	 * As of PHP 5.3.0
	 *
	 * @param	String	$func	method name
	 * @param	Array	$args	method arguments
	 * @return	mixed
	 */
	public static function __callStatic($func, $args){
		return self::_rpc_call(self::$client, 
			array('class' => self::$_class, 'func' => $func, 'args' => $args));	
	}

	/**
	 * find a class from remote server
	 *
	 * @param	String	$class	class name
	 * @param	Array	$paths	root paths
	 * @return	boolean
	 */
	public static function find_class($class, $paths = array()){
		return self::_rpc_call(self::$client,array('class' => $class, 'paths' => $paths));	
	}

	/**
	 * remove the instances handled from the socket server
	 */	
	public function __destruct(){
		//if the client socket haven't been closed yet
		//destroy the object instance from the server 
		if(isset(self::$client) && isset(self::$client->instances[$this->_id])){
			$this->__destroy();
			unset(self::$client->instances[$this->_id]);
		}
	}
}
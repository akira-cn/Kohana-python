<?php defined('SYSPATH') or die('No direct script access.');

/**
 * Creating socket handles connected to the socket server
 *
 * @package    Python
 * @category   Socket
 * @author     akira.cn@gmail.com
 * @copyright  (c) 2011 WED Team
 * @license    http://kohanaframework.org/license
 */
class Socket_Client{
	/**
	 * socket server ip address
	 */
	private $_host;
	/**
	 * socket server port
	 */
	private $_port;
	/**
	 * socket connection
	 */
	private $_socket;
	/**
	 * error reports
	 */
	private $_error;
	
	/**
	 * the object instances handled
	 */
	public $instances = array();
	
	/**
	 * create a new socket client object
	 *
	 * @param	String	$host
	 * @param	Int		$port 
	 */
	function __construct($host = '127.0.0.1', $port = 1990) {
		$this->_host = $host;
		$this->_port = $port;
		$this->_connect();
	}
	
	/**
	 * create the connection
	 *
	 * @return	Socket 
	 */
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
 
	/**
	 * get the socket handle
	 *
	 * @return Socket
	 */ 
	public function socket(){
		return $this->_socket;
	}
	
	/**
	 * remove the instances handled from the socket server
	 */
	public function __destruct() {
		$socket = $this->_socket;
		socket_write($socket, '', 0);
		socket_close($socket);
	}
	
	/**
	 * provide errors
	 *
	 * @throws Socket_Exception
	 */
	private function _error($errMsg = '') {
		$this->_error = array(
			'err' => 'sys.socket.error',
			'msg' => $errMsg,
		);
		throw new Socket_Exception($errMsg);
	}
}
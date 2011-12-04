<?php defined('SYSPATH') or die('No direct script access.');

class Socket_Test extends Socket_Instance{
	protected static $_class = 'Sample_Logic_Test';

	public function __construct(){
		$args = func_get_args();
		parent::__construct(self::$_class, $args);
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
			array(	
					"func" => $func, 
					"args" => $args, )
		);													
	}
}
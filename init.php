<?php defined('SYSPATH') or die('No direct script access.');

Socket_Instance::$client = new Socket_Client('127.0.0.1', 1990);

class Python_Env_Init extends Kohana{
	/**
	 * add auto_load to create php local classes associate to remove python classes
	 */
	public static function auto_load($class){
		try{
				$data = Socket_Instance::find_class($class, self::$_paths);
				$code = 
					'class '.$class.' extends Socket_Instance
						{
							protected static $_class="'.$class.'";
							function __construct(){
								$args = func_get_args();
								parent::__construct(self::$_class,$args);
							}
							static function __callStatic($func, $args){
								return self::_rpc_call(self::$client, 
									array(
											"class" => self::$_class, 
											"func" => $func, 
											"args" => $args, )
								);													
							}
					}';
				eval($code);
				return true;
		}catch(Exception $ex){
				return false;
		}
	}
}

spl_autoload_register(array('Python_Env_Init', 'auto_load'));
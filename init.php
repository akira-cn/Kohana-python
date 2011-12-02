<?php defined('SYSPATH') or die('No direct script access.');

class Python_Env_Init extends Kohana{
	/**
	 * 改写auto_load方法以增加对python的支持
	 */
	public static function auto_load($class){
		try{
				Socket_Instance::find_class($class, self::$_paths);
				$code = 'class '.$class.' extends Socket_Instance{function __construct(){$args = func_get_args();parent::__construct("'
						.$class.'", $args);}}';
				eval($code);
		}catch(Exception $ex){}
	}
}

spl_autoload_register(array('Python_Env_Init', 'auto_load'));
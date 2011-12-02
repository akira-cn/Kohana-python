<?php defined('SYSPATH') or die('No direct script access.');

class Socket_Test extends Socket_Instance{
	public function __construct(){
		$args = func_get_args();
		parent::__construct('Model_Logic_Test', $args);
	}
}
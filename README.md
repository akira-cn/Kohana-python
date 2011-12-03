# Kohana Python Module

## Usage: 

### Loading module

     Kohana::register_modules(array(
         'python' => MODPATH.'python'
     ));

### Write Python Class:

     import sys

     class Model_Logic_Sample:
         def __init__(self, name):
             self.name = name;
         def test (self):
             return self.name;
         def test2 (self):
             return 'test';

### Use it in your Controller like Normal PHP Class

     class Controller_My extends Controller{
         public function action_foo(){
             $obj = new Model_Logic_Sample("john");
             echo $obj->test();
             exit;
         }
     }
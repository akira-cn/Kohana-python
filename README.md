# Kohana Python Module

## Usage: 

### Run Server

     python server.py start

### Loading module

     Kohana::register_modules(array(
         'python' => MODPATH.'python'
     ));

### Write Python Class:

     import sys

     class Sample_Basic_Test:
         def __init__(self, name):
             self.name = name;
         def greet (self, greet):
             return greet + ' ' + self.name;
         def add (self, x, y):
             return x + y;
         def ok (self):
             return {'err':'ok'};
         def arr (self):
             return [1,2,3,4];

         @classmethod
         def greet_static(cls):
             return "Hello World";

### Use it in your Controller like Normal PHP Class

     class Controller_Foo extends Controller{
         public function action_bar(){
             $obj = new Sample_Basic_Test("john");
             echo $obj->greet("Hello");
             exit;
         }
     }
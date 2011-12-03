""" 
Collection of functions to serialize Python variables to the native PHP format 
 
@version 0.1 
@author Daniel Cousineau <dcousineau@gmail.com> 
@copyright Copyright (c) 2008 Daniel Cousineau 
@license http://www.opensource.org/licenses/mit-license.php MIT License 
"""  
  
from types import *  
  
def serialize(var):  
    """ 
    Serialize var to the native PHP serialization format 
    """  
    if type(var) is IntType or type(var) is LongType:  
        return serialize_int(var)  
  
    elif type(var) is FloatType:  
        return serialize_decimal(var)  
  
    elif type(var) is BooleanType:  
        return serialize_boolean(var)  
  
    elif type(var) is StringType:  
        return serialize_string(var)  
    
    elif type(var) is UnicodeType:  
        return serialize_string(var)  

    elif type(var) is NoneType:  
        return serialize_null()  
  
    elif type(var) is ListType or type(var) is TupleType:  
        return serialize_array(var)  
  
    elif type(var) is DictType:  
        return serialize_dictionary(var)  
  
    elif type(var) is InstanceType:  
        return serialize_object(var)  
  
    else:  
        raise TypeError("Invalid Type %s" % (type(var)))  
  
def serialize_string(string):  
    """ 
    Format: s:L:"STRING"; 
        L: Length of the string 
        STRING: The string itself. No need to escape quotes (") 
    """  
    return "s:%d:\"%s\";" % (len(string), string)  
  
def serialize_int(int):  
    """ 
    Format: i:D; 
        D: the integer 
    """  
    return "i:%d;" % (int)  
  
def serialize_decimal(decimal):  
    """ 
    Format: d:D; 
        D: the decimal (accepts expontent notation) 
    """  
    return "d:%s;" % (decimal)  
  
def serialize_boolean(boolean):  
    """ 
    Format: b:B; 
        B: 1 for True, 0 for False 
    """  
    return "b:%d;" % (boolean)  
  
def serialize_null():  
    """ 
    Format: N; 
    """  
    return "N;"  
  
def serialize_array(array):  
    """ 
    Format: a:K:{VALUES} 
        K: Number of entries (number of keys for dictionaries) 
        VALUES: serialized key appended to serialized value. Do not worry about ; 
                if a value is an array 
 
    DOES NOT END WITH A ; 
    """  
    values = []  
    for index, value in enumerate(array):  
        values.append(serialize_array_key(index))  
        values.append(serialize(value))  
    return "a:%d:{%s}" % (len(array), "".join(values))  
  
def serialize_array_key(var):  
    """ 
    Decimals and Boolans are automatically converted to integers for key values. 
    Arrays and Objects throw errors if they are set as a key 
    """  
    if type(var) is IntType or type(var) is FloatType or type(var) is BooleanType:  
        return serialize_int(int(var))  
  
    elif type(var) is NoneType:  
        return serialize_int(0)  
  
    elif type(var) is StringType:  
        return serialize_string(var)  
  
    else:  
        raise TypeError("Invalid Key Type %s" % (type(var)))  
  
def serialize_dictionary(array):  
    """ 
    See serialize_array() 
    """  
    values = []  
    for index, value in array.iteritems():  
        values.append(serialize_array_key(index))  
        values.append(serialize(value))  
    return "a:%d:{%s}" % (len(array), "".join(values))  
  
def serialize_object(obj):  
    """ 
    Format: O:L:"CLASS":K:{MEMBERS} 
        L: Length of class name 
        CLASS: class name (string) 
        K: Number of class members (ignore 'static' members) 
        MEMBERS: Members as an associative array (dictionary) (ignore 'static' members) 
    """  
    objClass = obj.__class__.__name__  
  
    values = []  
    for index, value in obj.__dict__.iteritems():  
        values.append(serialize_array_key(index))  
        values.append(serialize(value))  
  
    return "O:%d:\"%s\":%d:{%s}" % (len(objClass), objClass, len(obj.__dict__), "".join(values))
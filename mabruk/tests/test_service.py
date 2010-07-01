from nose.tools import *

from mabruk.service import Service, MethodNotFound

from mabruk.tests.mock import (
    bad_service_missing_handler,
    bad_service_wrong_handler,
    service_addition,
    service_simple_hierarchy,
    bad_service_wrong_nested_handler
)

@raises(ValueError)
def create_with_missing_handler_test():
    Service(bad_service_missing_handler)
    
@raises(TypeError)
def create_with_wrong_handler_test():
    Service(bad_service_wrong_handler)
    
def create_simple_test():
    s = Service(service_addition)
    assert s.call('add', 1, 1) == 2
    
@raises(MethodNotFound)
def method_not_found_test():
    s = Service(service_addition)
    s.call('subtract', 5, 2)
    
@raises(MethodNotFound)
def accessing_hidden_methods_test():
    s = Service(service_addition)
    s.call('__class__', 5, 2)
    
@raises(ValueError)
def junk_method_name_test():
    s = Service(service_addition)
    s.call(42)
    
def simple_handler_hierarchy_test():
    s = Service(service_simple_hierarchy)
    value = 'silly walk'
    assert s.call('example.echo', value) == value
    
@raises(TypeError)
def create_with_nested_wrong_handler_test():
    s = Service(bad_service_wrong_nested_handler)
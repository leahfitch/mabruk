"""Tests of the service wrapper implementation"""

from nose.tools import raises

from mabruk.service import Service, MethodNotFound

from mabruk.tests.mock import (
    bad_service_missing_handler,
    bad_service_wrong_handler,
    service_addition,
    service_simple_hierarchy,
    bad_service_wrong_nested_handler
)

@raises(ValueError)
def create_missing_handler_test():
    """
    Check that an appropriate error is raised when a 
    service is instantiated with a module that does
    not contain a handler object.
    """
    Service(bad_service_missing_handler)
    
@raises(TypeError)
def create_wrong_handler_test():
    """
    Check that an appropriate error is raised when a 
    service is instantiated with a module that does
    not contain a handler object that is an instance of Handler.
    """
    Service(bad_service_wrong_handler)
    
def create_simple_test():
    """
    Check that we can instantiate a service with a simplest
    possible module and call a service method.
    """
    s = Service(service_addition)
    assert s.call('add', 1, 1) == 2
    
@raises(MethodNotFound)
def method_not_found_test():
    """
    Check that an appropriate error is raised when
    attempting to call an undefined method.
    """
    s = Service(service_addition)
    s.call('subtract', 5, 2)
    
@raises(MethodNotFound)
def access_hidden_methods_test():
    s = Service(service_addition)
    s.call('__class__', 5, 2)
    
@raises(ValueError)
def junk_method_name_test():
    """
    Check that an appropriate error is raised when
    attempting to call a method using junk.
    """
    s = Service(service_addition)
    s.call(42)
    
@raises(TypeError)
def nested_wrong_handler_test():
    """
    Check that an appropriate error is raised when
    attempting to instantiate a service with a module
    that contains handler with a child that is not an
    instance of Handler
    """
    Service(bad_service_wrong_nested_handler)
    
def simple_hierarchy_test():
    """
    Check that we can instantiate a service with the simplest
    possible module that implements hierarchy and call a nested
    method.
    """
    s = Service(service_simple_hierarchy)
    value = 'silly walk'
    assert s.call('example.echo', value) == value
    
    
def simple_hierarchy_deeper_test():
    """
    Again checking we can call a simple nested method but this time
    a little deeper.
    """
    s = Service(service_simple_hierarchy)
    value = 'silly walk'
    assert s.call('example.foo.bar.echo', value) == value
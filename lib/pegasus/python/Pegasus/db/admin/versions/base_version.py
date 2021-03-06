__author__ = "Rafael Ferreira da Silva"

import sys
import abc
from Pegasus.tools import properties

class BaseVersion(object):
    __metaclass__  = abc.ABCMeta
    
    def __init__(self, config_properties, verbose=False, debug=False):
        self.set_properties(config_properties)
        self._vbs = verbose
        self._dbg = debug
    
    @abc.abstractmethod
    def update(self, force):
        """Used for the update command."""
        
    @abc.abstractmethod
    def downgrade(self, force):
        """Used for the downgrade command."""
        
    @abc.abstractmethod
    def is_compatible(self):
        """Used for checking the compatibility of the database with the version class."""

    @abc.abstractmethod
    def dispose(self):
        """Dispose the class."""
        
    def verbose(self, message):
        if (self._vbs):
            sys.stdout.write(message)
            
    def debug(self, message):
        if (self._dbg):
            sys.stdout.write(message)
            
    def set_properties(self, config_properties):
        self.props = properties.Properties()
        self.props.new(config_file=config_properties)
        
    def get_property(self, name):
        return self.props.property(name)
    
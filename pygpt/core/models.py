"""
Models:
Class models for the tests and test set used across pygpt.

Author: Martino Ferrari (CS-SI) <martino.ferrari@c-s.fr>
License: GPLv3
"""
from enum import Enum

import core.log as log


class TestScope(Enum):
    """
    Test Scope for filtering tests.
    """
    Regular = 'regular'
    Daily = 'daily'
    Weekly = 'weekly'
    Release = 'release'
    
    @staticmethod
    def compatibility_map():
        """
        Compatibility relations between tag classes
        """
        return {
            TestScope.Regular : set([TestScope.Regular]),
            TestScope.Daily : set([TestScope.Regular, TestScope.Daily]),
            TestScope.Weekly : set([TestScope.Regular, TestScope.Daily,
                                    TestScope.Weekly]),
            TestScope.Release : set([TestScope.Regular, TestScope.Daily, 
                                     TestScope.Weekly, TestScope.Release])
        }

    @staticmethod
    def init(value):
        """
        Initializes a TestScope from its string value.
        
        Parameters:
        -----------
         - value: test scope string value

        Returns:
        --------
        A testscope enum if the value is a standard scope otherwise its lower case value
        """
        value = str(value).lower()
        if value in TestScope._value2member_map_:
            return TestScope._value2member_map_[value]
        return value
    
    @staticmethod
    def compatible(source, target):
        """
        Check compatibility between the source scope and the target scope.
        The compatibility is achived in the following cases:
         - target == source or target.startswith(source)
         - source is a regular scope and the target is compatible with it
        
        Parameters:
        -----------
         - source: selected source test scope
         - target: target test scope
        """
        if source == target:
            return True
        if isinstance(source, TestScope):
            if not isinstance(target, TestScope):
                return False
            return target in TestScope.compatibility_map()[source]
        else:
            value = str(target._value_ if isinstance(target, TestScope) else target).lower()
            return value.startswith(str(source).lower())
        return False

    @staticmethod
    def compatibleN(source, targets):
        """
        Resolves compatibility between a source and a list of targets sperated by a `/` character.

        Parameters:
        -----------
         - source: source TestScope
         - targets: string contains all target scope separted by `/`

        Returns:
        --------
        `True` if any of the target tag is compatible with the source one. 
        """
        targets = [TestScope.init(x) for x in str(targets).split('/')]
        return any([TestScope.compatible(source, x) for x in targets])


class Test(log.Printable):
    """
    Represents a test and its configuration using the information
    stored in the json file and on the XML graph.

    Parameters:
    -----------
     - struct: json data structure
     - source_path: source json path
    """
    def __init__(self, struct, source_path):
        super().__init__()
        struct['json_file'] = source_path # add the source information to the data structure
        self.raw_json = struct
        self.name = struct['id']
        
    
class TestReuslt(log.Printable):
    """
    Represents the results of execution of a test
    """

class TestResutlSet(log.Printable):
    """
    Set of tests representing the result of a single JSON 
    tests set.
    """
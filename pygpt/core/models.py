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


def __normalize_struct__(struct):
    """
    Normalize struct by putting keys in lower case.
    """
    res = {}
    for item in struct.items():
        res[str(item[0]).lower()] = item[1]
    return res


class Test(log.Printable):
    """
    Represents a test and its configuration using the information
    stored in the json file and on the XML graph.

    Parameters:
    -----------
     - struct: json data structure
     - source_path: source json path
    """
    def __init__(self, struct, source_path=None):
        super().__init__()
        if source_path is not None:
            # add the source information to the data structure
            struct['json_file'] = source_path 
        self._raw = __normalize_struct__(struct)
        self._name = struct['id']
    
    @property
    def name(self):
        """
        Test name.
        """
        return self._name
    
    @property
    def uuid(self):
        """
        Test UUID is the name replacing `.` and ` ` with `_`.
        """
        return self._name.replace(' ', '_').replace('.', '_')

    @property
    def author(self):
        """
        Test author, it should contains the organization as well.
        """
        return self._raw['author']

    @property
    def description(self):
        """
        Test description.
        """
        return self._raw['description']
    
    @property
    def frequency(self):
        """
        Test frequency, a string containing all the frequency tags 
        separated by '/'.
        """
        return self._raw['frequency']

    @property
    def graph_path(self):
        """
        Path of the graph.
        """
        return self._raw['graphpath']

    @property
    def source_path(self):
        """
        Source TestSet JSON path.
        """
        return self._raw['json_file']
    
    @property
    def inputs(self):
        """
        Graph inputs definition.
        """
        return self._raw['inputs']
    
    @property
    def outputs(self):
        """
        Resulting outputs with optional expected value.
        """
        return self._raw['outputs']

    @property
    def parameters(self):
        """
        Additional needed graph parameters.
        """
        return self._raw['parameters']
    
    @property
    def jvm_config(self):
        """
        """
        if 'configvm' in self._raw:
            return self._raw['configvm']
        return None


class TestReuslt(log.Printable, Test):
    """
    Represents the results of execution of a test
    """

class TestResutlSet(log.Printable):
    """
    Set of tests representing the result of a single JSON 
    tests set.
    """
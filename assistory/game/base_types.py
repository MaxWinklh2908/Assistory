"""
Basic Data Types
            Used as Amounts     Used as Flags

- Items             x               x
- Buildings         x               x
- Recipes           x               x
- Resource Nodes    x
- Schematics                        x
"""

import copy
import difflib
import os
from typing import Set, Dict, Iterable, Any, Optional
import yaml

import numpy as np


class Flags(set):
    """
    Collection of flags that acts like a set with additional
    functionality:
     - basic logic (& and |)
     - check keys to be valid
     - IO methods
    """
    def __init__(
            self,
            data: Iterable[str],
            omega: Iterable[str]
        ):
        """
        Ceate a new Values object

        Args:
            data (Iterable[str]): Active flags
            omega (Iterable[str]): Valid flags. The order is used for as_array.
        """
        data_ = set(data)
        self._omega = tuple(omega)
        super().__init__()
        self.update(data_)

    def add(self, value: str):
        if not isinstance(value, str):
            raise ValueError('Accept only str')
        if not value in self._omega:
            closest_matches = difflib.get_close_matches(value, self._omega, n=1)
            hint = f' Did you mean: "{closest_matches[0]}"?' if closest_matches else ''
            raise ValueError(f'Unknown flag: "{value}".{hint}')
        set.add(self, value)

    def update(self, data: Set[str]):
        for value in data:
            self.add(value)

    def copy(self) -> 'Flags':
        return type(self)(
            data=self,
            omega=self._omega
        )
    
    @classmethod
    def _from_array(cls, array: np.ndarray, omega: Iterable[str]) -> 'Flags':
        omega_ = list(omega)
        if len(omega_) != len(array):
            raise ValueError('Array and omega must have equal length')
        data = {
            flag_name
            for i, flag_name in enumerate(omega_)
            if bool(array[i])
        }
        return cls(data, omega)

    def __or__(self, other: 'Flags') -> 'Flags':
        if not isinstance(other, Flags):
            raise ValueError('Can only apply operation with other Flags objects')
        if set(self._omega) != set(other._omega):
            raise ValueError('Incompatible flags')
        return type(self)(set(self) | set(other), self._omega)
    
    def __ior__(self, other: 'Flags') -> 'Flags':
        self.update(self | other)
        return self

    def __and__(self, other: 'Flags') -> 'Flags':
        if not isinstance(other, Flags):
            raise ValueError('Can only apply operation with other Flags objects')
        if set(self._omega) != set(other._omega):
            raise ValueError('Incompatible flags')
        return type(self)(set(self) & set(other), self._omega)

    def __iand__(self, other: 'Flags') -> 'Flags':
        self.update(self & other)
        return self

    def as_array(self) -> np.ndarray:
        """
        Return flags as numpy array based omega with contained flag set to 1
        and all other set to 0.

        Returns:
            np.ndarray: Array with same order of values as omega
        """
        return np.array([flag_name in self for flag_name in self._omega], dtype=bool)

    def save(self, file_path: os.PathLike):
        """
        Store the values to file

        Args:
            file_path (os.PathLike): Path of the file
        """
        if str(file_path).endswith('.yaml') or str(file_path).endswith('.yml'):
            with open(file_path, 'w') as fp:
                yaml.dump(sorted(list(self)), fp)
        else:
            raise ValueError('Path must be .yml or .yaml')

    @classmethod
    def _load(
        cls,
        file_path: os.PathLike,
        omega: Iterable[str]
    ) -> 'Values':
        if str(file_path).endswith('.yaml') or str(file_path).endswith('.yml'):
            with open(file_path, 'r') as fp:
                data = yaml.safe_load(fp)
        else:
            raise ValueError('Path must be a .yml or .yaml')
        return cls(data, omega)


class Values(dict):
    """
    Collection of named values that acts like a dict with additional
    functionality:
     - basic math (+ and -)
     - check keys to be valid
     - IO methods
    """

    def __init__(
            self,
            data: Dict[str, Any],
            omega: Iterable[str],
            default_value: Any=0
        ):
        """
        Ceate a new Values object

        Args:
            data (Dict[str, Any]): Named values
            omega (Iterable[str]): Valid keys. The order is used for as_array.
            default_value (Any, optional): Default value for undefined keys of
                omega in data. Value is copied for every entry. Defaults to 0.
        """
        self._omega = tuple(omega)
        self._default_value = default_value
        super().__init__()
        self.update(data)
        # Idea: data is completed on construction
        # + easy handling in methods, reuse dict methods `__getitem__`, `__iter__`, ...
        # - larger in memory, need to overwrite method `clear`
        self.update({
            k: copy.deepcopy(default_value)
            for k in set(self._omega) - set(data)
        })

    # Overwrite dict.__setitem__ to check key
    def __setitem__(self, key: str, value):
        if not isinstance(key, str):
            raise ValueError('Expect keys of data to be of type str')
        if not key in self._omega:
            closest_matches = difflib.get_close_matches(key, self._omega, n=1)
            hint = f' Did you mean: "{closest_matches[0]}"?' if closest_matches else ''
            raise ValueError(f'Unknown key: {key}.{hint}')
        dict.__setitem__(self, key, value)

    # Overwrite dict.update as it doesn't call __setitem__
    def update(self, *args, **kwargs):
        for k, v in dict(*args, **kwargs).items():
            self[k] = v

    def set_values(self, val: Any):
        """
        Set all values to a new value. Value is copied for every entry.

        Args:
            val (Any): The new value
        """
        self.update({k: copy.deepcopy(val) for k in self._omega})

    # Overwrite dict.copy as it outputs only a dict
    def copy(self) -> 'Values':
        return type(self)(
            data=self,
            omega=self._omega,
            default_value=self._default_value
        )

    # Overwrites dict.clear as self must always contain all keys
    def clear(self):
        """
        Reset all values to the default value
        """
        self.set_values(self._default_value)

    ########################### Numpy interface ###############################
    
    @classmethod
    def _from_array(cls, array: np.ndarray, omega: Iterable[str]) -> 'Values':
        omega_ = list(omega)
        if len(omega_) != len(array):
            raise ValueError('Array and omega must have equal length')
        data = {
            k: v
            for k, v in zip(omega_, array)
        }
        return cls(data, omega)

    def as_array(self) -> np.ndarray:
        """
        Return values as numpy array based omega

        Returns:
            np.ndarray: Array with same order of values as omega
        """
        return np.array([self[k] for k in self._omega], np.float64)

    ########################### Arithmetics ###################################

    def __add__(self, other: 'Values') -> 'Values':
        if not isinstance(other, Values):
            raise ValueError('Can only apply operation with other Amounts objects')
        if set(self._omega) != set(other._omega):
            raise ValueError('Incompatible amounts')
        out = self.copy()
        for key in self:
            out[key] += other[key]
        return out
    
    def __iadd__(self, other: 'Values') -> 'Values':
        self.update(self + other)
        return self

    def __sub__(self, other: 'Values') -> 'Values':
        if not isinstance(other, Values):
            raise ValueError('Can only apply operation with other Amounts objects')
        if set(self._omega) != set(other._omega):
            raise ValueError('Incompatible amounts')
        out = self.copy()
        for key in self:
            out[key] -= other[key]
        return out

    def __isub__(self, other: 'Values') -> 'Values':
        self.update(self - other)
        return self

    def __mul__(self, factor):
        if isinstance(factor, Values):
            raise ValueError('Can not multiply Values with itself')
        return type(self)(
            {
                name: val * factor
                for name, val in self.items()
            },
            omega=self._omega
        )

    def __rmul__(self, factor):
        return self * factor
    
    ################################ I/O ######################################

    def round(self, ndigits: Optional[int]=None) -> 'Values':
        """
        Round each value according to the digits provided.

        Args:
            ndigits (int, optional): Number of digits after rounding. Output is
                in integer format if None. Defaults to None.

        Returns:
            Values: Rounded values
        """
        return type(self)(
            {
                k: round(v, ndigits)
                for k, v in self.items()
            },
            omega=self._omega
        )

    # can not use default value because ortools variables have no comparison method
    def as_dict_ignoring(self, ignore_value: Any) -> Dict[str, Any]:
        """
        Return values as dict with specific values removed

        Args:
            ignore_value (Any, optional): Do not include these values to the
                output dict.

        Returns:
            Dict[str, Any]: result dict
        """
        return {k:v for k,v in self.items() if v != ignore_value}
    
    def __str__(self) -> str:
        return str(self.as_dict_ignoring(0))
    
    def __repr__(self) -> str:
        return self.__str__()

    def save(self, file_path: os.PathLike, ignore_value: Optional[float]=None):
        """
        Store the values to file

        Args:
            file_path (os.PathLike): Path of the file
            ignore_value (float, optional): Do not include these values to
                the output dict. Include all if None. Check after rounding.
                Defaults to None.
            round_ndigits (int): Round result up to n digits if value
                nonnegative. Defaults to -1.
        """
        if not ignore_value is None:
            data = self.as_dict_ignoring(ignore_value)
        else:
            data = dict(self)
            
        if str(file_path).endswith('.yaml') or str(file_path).endswith('.yml'):
            with open(file_path, 'w') as fp:
                yaml.dump(data, fp)
        else:
            raise ValueError('Path must be .yml or .yaml')

    def pprint(self, ignore_value: Optional[float]=None):
        """
        Print the data as aligned table with two columns: Key left, Values right

        Args:
            ignore_value (float, optional), optional): Don't print values equal
                to this value. Don't skip if None. Defaults to None.
        """
        if ignore_value is None:
            data = self
        else:
            data = self.as_dict_ignoring(ignore_value)
        if len(data) == 0:
            print('{}')
            return
        key_width = max(len(k) for k in data)
        for key in sorted(data):
            print(key.ljust(key_width), data[key])

    @classmethod
    def _load(
        cls,
        file_path: os.PathLike,
        omega: Iterable[str]
    ) -> 'Values':
        if str(file_path).endswith('.yaml') or str(file_path).endswith('.yml'):
            with open(file_path, 'r') as fp:
                data = yaml.safe_load(fp)
        else:
            raise ValueError(f'Path must be a .yml or .yaml. Is {file_path}')
        return cls(data, omega)

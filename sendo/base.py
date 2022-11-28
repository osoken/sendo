from abc import ABCMeta, abstractmethod
from datetime import datetime, timezone
from itertools import chain

from typing import Generic, TypeVar, Optional, Callable

try:
    from typing import Mapping, Hashable, Iterable
except ImportError:
    from collections.abc import Mapping, Hashable, Iterable


class BaseError(Exception):
    """Base class for exceptions in sendo"""

    pass


def get_dt():
    return datetime.utcnow().replace(tzinfo=timezone.utc)


class BaseObject(metaclass=ABCMeta):
    def __init__(self, updated_at: datetime = None):
        self._updated_at = updated_at if updated_at is not None else get_dt()

    @property
    def updated_at(self) -> datetime:
        return self._updated_at

    @property
    @abstractmethod
    def value(self):
        pass

    def __bool__(self) -> bool:
        return bool(self.value)


T = TypeVar("T")


class Exec(BaseObject):
    def __init__(self, func, *args, **kwargs):
        super(Exec, self).__init__()
        self._func = func
        self._args = args
        self._kwargs = kwargs
        self._updated_at = None

    def _try_cache_result(self) -> None:
        try:
            newest = max(
                map(
                    lambda d: d.updated_at,
                    chain([self._func], self._args, self._kwargs.values()),
                )
            )
        except ValueError:
            newest = get_dt()
        if self._updated_at is None or newest > self._updated_at:
            self._cache_result()
            self._updated_at = newest

    @property
    def updated_at(self) -> datetime:
        self._try_cache_result()
        return self._updated_at

    def _cache_result(self) -> None:
        self._cached_result = self._func.value(
            *(a.value for a in self._args),
            **{k: v.value for k, v in self._kwargs.items()}
        )

    @property
    def value(self) -> T:
        self._try_cache_result()
        return self._cached_result


class BaseFunction(BaseObject):
    def __init__(self):
        super(BaseFunction, self).__init__()

    @property
    def value(self):
        return self.exec

    @abstractmethod
    def exec(self, *args, **kwargs):
        pass

    def __call__(self, *args, **kwargs) -> T:
        return Exec(self, *args, **kwargs)


class Function(BaseObject):
    def __init__(self, func: Callable):
        super(Function, self).__init__()
        self._func = func

    @property
    def value(self):
        return self._func

    def __call__(self, *args, **kwargs):
        return Exec(self, *args, **kwargs)


class EqBase(BaseFunction):
    def __init__(self):
        super(EqBase, self).__init__()

    def exec(self, a, b):
        return a == b


class LtBase(BaseFunction):
    def __init__(self):
        super(LtBase, self).__init__()

    def exec(self, a, b):
        return a < b


class LeBase(BaseFunction):
    def __init__(self):
        super(LeBase, self).__init__()

    def exec(self, a, b):
        return a <= b


class NeBase(BaseFunction):
    def __init__(self):
        super(NeBase, self).__init__()

    def exec(self, a, b):
        return a != b


class BoolBase(BaseFunction):
    def __init__(self):
        super(BoolBase, self).__init__()

    def exec(self, a):
        return bool(a)


class NotBase(BaseFunction):
    def __init__(self):
        super(NotBase, self).__init__()

    def exec(self, a):
        return not a


Eq = EqBase()
Lt = LtBase()
Le = LeBase()
Ne = NeBase()
Bool = BoolBase()
Not = NotBase()


class Variable(BaseObject, Generic[T]):
    def __init__(self, value: T):
        super(Variable, self).__init__()
        self._value = value

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value: T):
        self._updated_at = get_dt()
        self._value = value

    def __eq__(self, other):
        return Exec(Eq, self, other)

    def __lt__(self, other):
        return Exec(Lt, self, other)

    def __le__(self, other):
        return Exec(Le, self, other)

    def __ne__(self, other):
        return Exec(Ne, self, other)

    def __bool__(self):
        raise TypeError(
            "sendo object cannot cast directly to bool. Use sendo.Not(obj) instead"
        )


class BaseEnumerator(BaseObject):
    def __init__(
        self,
        key_updated_at_map: Optional[Mapping[Hashable, datetime]] = None,
        updated_at: Optional[datetime] = None,
    ):
        self._key_updated_at_map = (
            {} if key_updated_at_map is None else key_updated_at_map
        )
        if updated_at is None:
            try:
                self._updated_at = max(self._key_updated_at_map.values())
            except ValueError:
                self._updated_at = None
        else:
            self._updated_at = updated_at

    @abstractmethod
    def enumerate(self) -> Iterable:
        pass

    @abstractmethod
    def get_key(self, x) -> Hashable:
        pass

    @abstractmethod
    def enter(self, x) -> None:
        pass

    def add(self, x) -> None:
        self.enter(x)
        self._key_updated_at_map[self.get_key(x)] = x.updated_at
        self._try_update_updated_at(self.get_addition_dt())

    @abstractmethod
    def update(self, x) -> None:
        pass

    def update_value(self, x) -> None:
        self.update(x)
        self._key_updated_at_map[self.get_key(x)] = x.updated_at
        self._try_update_updated_at(x.updated_at)

    @abstractmethod
    def exit(self, k) -> None:
        pass

    def discard(self, k) -> None:
        self.exit(k)
        del self._key_updated_at_map[k]
        self._try_update_updated_at(self.get_deletion_dt())

    def _try_update_updated_at(self, x: datetime) -> None:
        if self._updated_at is None or self._updated_at < x:
            self._updated_at = x

    def _try_update(self) -> None:
        unchecked = set(self._key_updated_at_map.keys())
        for d in self.enumerate():
            key = self.get_key(d)
            if key not in self._key_updated_at_map:
                self.add(d)
            else:
                if self._key_updated_at_map[key] < d.updated_at:
                    self.update_value(d)
            unchecked.discard(key)
        for k in unchecked:
            self.discard(k)

    def get_addition_dt(self) -> datetime:
        return get_dt()

    def get_deletion_dt(self) -> datetime:
        return get_dt()

    @property
    def updated_at(self):
        self._try_update()
        return self._updated_at

    @property
    def value(self):
        self._try_update()
        return self._cached_result

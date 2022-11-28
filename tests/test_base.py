from unittest import TestCase

import time

from sendo import base


class VaribaleTestCase(TestCase):
    def test_variable_has_value(self):
        t1 = base.get_dt()
        time.sleep(0.1)
        sut = base.Variable(23)
        time.sleep(0.1)
        t2 = base.get_dt()
        self.assertEqual(sut.value, 23)
        self.assertTrue(t1 < sut.updated_at)
        self.assertTrue(sut.updated_at < t2)
        time.sleep(0.1)
        t3 = base.get_dt()
        time.sleep(0.1)
        sut.value = 53
        time.sleep(0.1)
        t4 = base.get_dt()
        self.assertEqual(sut.value, 53)
        self.assertTrue(t2 < sut.updated_at)
        self.assertTrue(t3 < sut.updated_at)
        self.assertTrue(sut.updated_at < t4)


class FunctionTestCase(TestCase):
    class Add2(base.BaseFunction):
        def __init__(self):
            super(FunctionTestCase.Add2, self).__init__()
            self._call_count = 0

        def exec(self, a, b):
            self._call_count += 1
            return a + b

    def test_function_executes_the_process(self):
        Integer = base.Variable[int]
        a = Integer(3)
        b = Integer(5)
        f = FunctionTestCase.Add2()
        sut = f(a, b)
        expected = 8
        actual = sut.value
        self.assertEqual(actual, expected)

    def test_function_executes_the_process_recursively(self):
        Integer = base.Variable[int]
        f = FunctionTestCase.Add2()
        a = Integer(3)
        b = Integer(5)
        c = f(a, b)
        sut = f(a, c)
        expected = 11
        actual = sut.value
        self.assertEqual(actual, expected)

    def test_function_updates_the_result(self):
        Integer = base.Variable[int]
        f = FunctionTestCase.Add2()
        a = Integer(3)
        b = Integer(5)
        sut = f(a, b)
        expected = 8
        actual = sut.value
        self.assertEqual(actual, expected)
        time.sleep(0.1)
        a.value = 4
        time.sleep(0.1)
        actual = sut.value
        expected = 9
        self.assertEqual(actual, expected)
        self.assertEqual(sut.updated_at, a.updated_at)

    def test_function_recalculate_only_if_argument_updated(self):
        Integer = base.Variable[int]
        f = FunctionTestCase.Add2()
        a = Integer(3)
        b = Integer(5)
        sut = f(a, b)
        self.assertEqual(f._call_count, 0)
        expected = 8
        actual = sut.value
        self.assertEqual(f._call_count, 1)
        self.assertEqual(actual, expected)
        actual = sut.value
        self.assertEqual(f._call_count, 1)
        a.value = 4
        actual = sut.value
        expected = 9
        self.assertEqual(actual, expected)
        self.assertEqual(f._call_count, 2)

    def test_function_function(self):
        Integer = base.Variable[int]

        def some_function(a, b):
            return a ** 2 + b ** 2 - 2 * a * b

        def another_function(a):
            return a ** 3

        a = 2
        b = 3
        c = another_function(a)
        lazy_a = Integer(a)
        lazy_b = Integer(b)
        some_lazy_function = base.Function(some_function)
        another_lazy_function = base.Function(another_function)
        lazy_c = another_lazy_function(lazy_a)
        sut1 = some_lazy_function(lazy_a, lazy_b)
        sut2 = some_lazy_function(lazy_c, lazy_b)
        self.assertEqual(some_function(a, b), sut1.value)
        self.assertEqual(some_function(c, b), sut2.value)
        a = 4
        lazy_a.value = a
        self.assertEqual(some_function(a, b), sut1.value)
        self.assertNotEqual(some_function(c, b), sut2.value)
        self.assertEqual(some_function(another_function(a), b), sut2.value)


class BaseEnumeratorTestCase(TestCase):
    class EnumListMember(base.BaseEnumerator):
        def __init__(self, target_list):
            super(BaseEnumeratorTestCase.EnumListMember, self).__init__(
                {d.value.key: d.updated_at for d in target_list}
            )
            self._target_list = target_list

        def enumerate(self):
            return iter(self._target_list)

        def get_key(self, x):
            return x.value.key

        def enter(self, x):
            pass

        def update(self, x):
            pass

        def exit(self, k):
            pass

    from dataclasses import dataclass

    @dataclass
    class KeyValue:
        key: str
        value: int

    def test_enumerator_can_detect_member_update(self):
        KV = base.Variable[self.KeyValue]
        a = KV(self.KeyValue(key="a", value=3))
        time.sleep(0.1)
        b = KV(self.KeyValue(key="b", value=5))
        time.sleep(0.1)
        c = KV(self.KeyValue(key="c", value=7))
        time.sleep(0.1)
        target_list = [a, b, c]
        sut = self.EnumListMember(target_list)
        self.assertEqual(sut.updated_at, c.updated_at)
        time.sleep(0.1)
        a.value = self.KeyValue(key="a", value=1)
        self.assertEqual(sut.updated_at, a.updated_at)

    def test_enumerator_can_detect_member_addition(self):
        KV = base.Variable[self.KeyValue]
        a = KV(self.KeyValue(key="a", value=3))
        time.sleep(0.1)
        b = KV(self.KeyValue(key="b", value=5))
        time.sleep(0.1)
        c = KV(self.KeyValue(key="c", value=7))
        time.sleep(0.1)
        target_list = [a, b]
        sut = self.EnumListMember(target_list)
        self.assertEqual(sut.updated_at, b.updated_at)
        time.sleep(0.1)
        target_list.append(c)
        t = base.get_dt()
        time.sleep(0.1)
        self.assertTrue(sut.updated_at > t)
        time.sleep(0.1)
        t = base.get_dt()
        self.assertTrue(sut.updated_at < t)


class EqTestCase(TestCase):
    def test_eq_returns_true_if_a_eq_b(self):
        Int = base.Variable[int]
        a = Int(3)
        b = Int(3)
        sut = a == b
        expected = True
        actual = sut.value
        self.assertEqual(actual, expected)

    def test_eq_returns_false_if_a_ne_b(self):
        Int = base.Variable[int]
        a = Int(3)
        b = Int(4)
        sut = a == b
        expected = False
        actual = sut.value
        self.assertEqual(actual, expected)

    def test_eq_changes_its_value_when_variable_changed(self):
        Int = base.Variable[int]
        a = Int(3)
        b = Int(4)
        sut = a == b
        expected = False
        actual = sut.value
        self.assertEqual(actual, expected)
        a.value = 4
        expected = True
        actual = sut.value
        self.assertEqual(actual, expected)

    def test_eq_evaluated_as_bool(self):
        Int = base.Variable[int]
        a = Int(3)
        b = Int(4)
        self.assertFalse(a == b)
        a.value = 4
        self.assertTrue(a == b)

    def test_eq_is_accepted_as_if_statement(self):
        Int = base.Variable[int]
        a = Int(3)
        b = Int(3)
        c = None
        if a == b:
            c = 1
        else:
            c = 2
        self.assertEqual(c, 1)
        a.value = 2
        if a == b:
            c = 1
        else:
            c = 2
        self.assertEqual(c, 2)


class LtTestCase(TestCase):
    def test_lt_returns_true_if_a_lt_b(self):
        Int = base.Variable[int]
        a = Int(3)
        b = Int(4)
        sut = a < b
        expected = True
        actual = sut.value
        self.assertEqual(actual, expected)

    def test_lt_returns_false_if_not_a_lt_b(self):
        Int = base.Variable[int]
        a = Int(4)
        b = Int(4)
        sut = a < b
        expected = False
        actual = sut.value
        self.assertEqual(actual, expected)
        a = Int(5)
        b = Int(4)
        sut = a < b
        expected = False
        actual = sut.value
        self.assertEqual(actual, expected)

    def test_lt_changes_its_value_when_variable_changed(self):
        Int = base.Variable[int]
        a = Int(3)
        b = Int(4)
        sut = a < b
        expected = True
        actual = sut.value
        self.assertEqual(actual, expected)
        a.value = 4
        expected = False
        actual = sut.value
        self.assertEqual(actual, expected)


class LeTestCase(TestCase):
    def test_le_returns_true_if_a_le_b(self):
        Int = base.Variable[int]
        a = Int(3)
        b = Int(4)
        sut = a <= b
        expected = True
        actual = sut.value
        self.assertEqual(actual, expected)
        a = Int(4)
        b = Int(4)
        sut = a <= b
        expected = True
        actual = sut.value
        self.assertEqual(actual, expected)

    def test_le_returns_false_if_not_a_le_b(self):
        Int = base.Variable[int]
        a = Int(5)
        b = Int(4)
        sut = a <= b
        expected = False
        actual = sut.value
        self.assertEqual(actual, expected)

    def test_le_changes_its_value_when_variable_changed(self):
        Int = base.Variable[int]
        a = Int(3)
        b = Int(4)
        sut = a <= b
        expected = True
        actual = sut.value
        self.assertEqual(actual, expected)
        a.value = 4
        expected = True
        actual = sut.value
        self.assertEqual(actual, expected)
        a.value = 5
        expected = False
        actual = sut.value
        self.assertEqual(actual, expected)


class GtTestCase(TestCase):
    def test_gt_returns_true_if_a_gt_b(self):
        Int = base.Variable[int]
        a = Int(5)
        b = Int(4)
        sut = a > b
        expected = True
        actual = sut.value
        self.assertEqual(actual, expected)

    def test_gt_returns_false_if_not_a_gt_b(self):
        Int = base.Variable[int]
        a = Int(4)
        b = Int(4)
        sut = a > b
        expected = False
        actual = sut.value
        self.assertEqual(actual, expected)
        a = Int(3)
        b = Int(4)
        sut = a > b
        expected = False
        actual = sut.value
        self.assertEqual(actual, expected)

    def test_gt_changes_its_value_when_variable_changed(self):
        Int = base.Variable[int]
        a = Int(3)
        b = Int(4)
        sut = a > b
        expected = False
        actual = sut.value
        self.assertEqual(actual, expected)
        a.value = 5
        expected = True
        actual = sut.value
        self.assertEqual(actual, expected)
        a.value = 4
        expected = False
        actual = sut.value
        self.assertEqual(actual, expected)


class GeTestCase(TestCase):
    def test_ge_returns_true_if_a_ge_b(self):
        Int = base.Variable[int]
        a = Int(5)
        b = Int(4)
        sut = a >= b
        expected = True
        actual = sut.value
        self.assertEqual(actual, expected)
        a = Int(4)
        b = Int(4)
        sut = a >= b
        expected = True
        actual = sut.value
        self.assertEqual(actual, expected)

    def test_ge_returns_false_if_not_a_ge_b(self):
        Int = base.Variable[int]
        a = Int(3)
        b = Int(4)
        sut = a >= b
        expected = False
        actual = sut.value
        self.assertEqual(actual, expected)

    def test_ge_changes_its_value_when_variable_changed(self):
        Int = base.Variable[int]
        a = Int(20)
        b = Int(4)
        sut = a >= b
        expected = True
        actual = sut.value
        self.assertEqual(actual, expected)
        a.value = 2
        expected = False
        actual = sut.value
        self.assertEqual(actual, expected)
        a.value = 4
        expected = True
        actual = sut.value
        self.assertEqual(actual, expected)


class NeTestCase(TestCase):
    def test_ne_returns_true_if_a_ne_b(self):
        Int = base.Variable[int]
        a = Int(5)
        b = Int(3)
        sut = a != b
        actual = sut.value
        expected = True
        self.assertEqual(actual, expected)

    def test_ne_returns_false_if_a_eq_b(self):
        Int = base.Variable[int]
        a = Int(3)
        b = Int(3)
        sut = a != b
        actual = sut.value
        expected = False
        self.assertEqual(actual, expected)

    def test_ne_changes_its_value_when_variable_changed(self):
        Int = base.Variable[int]
        a = Int(20)
        b = Int(4)
        sut = a != b
        expected = True
        actual = sut.value
        self.assertEqual(actual, expected)
        a.value = 4
        expected = False
        actual = sut.value
        self.assertEqual(actual, expected)
        a.value = 10
        expected = True
        actual = sut.value
        self.assertEqual(actual, expected)


class NotTestCase(TestCase):
    def test_direct_use_of_builtin_not_operator_causes_type_error_exception(self):
        MyBool = base.Variable[bool]
        a = MyBool(False)
        with self.assertRaises(TypeError):
            _ = not a

    def test_not_returns_true_if_a_is_false(self):
        MyBool = base.Variable[bool]
        a = MyBool(False)
        sut = base.Not(a)
        expected = True
        actual = sut.value
        self.assertEqual(actual, expected)

    def test_not_retrns_false_if_a_is_true(self):
        MyBool = base.Variable[bool]
        a = MyBool(True)
        sut = base.Not(a)
        expected = False
        actual = sut.value
        self.assertEqual(actual, expected)

    def test_not_changes_its_value_when_variable_changed(self):
        MyBool = base.Variable[bool]
        a = MyBool(True)
        sut = base.Not(a)
        expected = False
        actual = sut.value
        self.assertEqual(actual, expected)
        a.value = False
        expected = True
        actual = sut.value
        self.assertEqual(actual, expected)


class BoolTestCase(TestCase):
    def test_direct_use_of_builtin_bool_operator_causes_type_error_exception(self):
        Int = base.Variable[int]
        a = Int(123)
        with self.assertRaises(TypeError):
            _ = bool(a)

    def test_bool_returns_true_if_a_is_true(self):
        Int = base.Variable[int]
        a = Int(123)
        sut = base.Bool(a)
        expected = True
        actual = sut.value
        self.assertEqual(actual, expected)

    def test_bool_returns_false_if_a_is_false(self):
        Int = base.Variable[int]
        a = Int(0)
        sut = base.Bool(a)
        expected = False
        actual = sut.value
        self.assertEqual(actual, expected)

    def test_bool_changes_its_value_when_variable_changed(self):
        Int = base.Variable[int]
        a = Int(0)
        sut = base.Bool(a)
        expected = False
        actual = sut.value
        self.assertEqual(actual, expected)
        a.value = 1
        expected = True
        actual = sut.value
        self.assertEqual(actual, expected)

    def test_if_statement_accepts_bool_object(self):
        Int = base.Variable[int]
        a = Int(0)
        with self.assertRaises(TypeError):
            _ = bool(a)
        sut = base.Bool(a)
        expected = False
        actual = bool(sut)
        self.assertEqual(actual, expected)
        a.value = 1
        expected = True
        actual = bool(sut)
        self.assertEqual(actual, expected)

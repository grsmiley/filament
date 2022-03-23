from argparse import ArgumentError
from unittest import IsolatedAsyncioTestCase
from filament import AsyncInjector, Injector, BindingContext, BindingScope

class BindingContextCase(IsolatedAsyncioTestCase):
    async def test_init(self):
        bc = BindingContext()

    async def test_init_singletons(self):
        bc = BindingContext(singletons = {'x': 'y'})
        result_map, result_scope = bc.get('x')
        self.assertEqual(result_map, 'y')
        self.assertEqual(result_scope, BindingScope.Singleton)

    async def test_init_locals(self):
        bc = BindingContext(locals = {'x': 'y'})
        result_map, result_scope = bc.get('x')
        self.assertEqual(result_map, 'y')
        self.assertEqual(result_scope, BindingScope.Local)

    async def test_init_transients(self):
        bc = BindingContext(transients = {'x': 'y'})
        result_map, result_scope = bc.get('x')
        self.assertEqual(result_map, 'y')
        self.assertEqual(result_scope, BindingScope.Transient)

    async def test_str_must_be_explicit_singleton(self):
        bc = BindingContext()
        with self.assertRaises(ValueError):
            bc.singleton('x')
        bc.singleton('x', 'y')

    async def test_str_must_be_explicit_local(self):
        bc = BindingContext()
        with self.assertRaises(ValueError):
            bc.local('x')
        bc.local('x', 'y')

    async def test_str_must_be_explicit_transient(self):
        bc = BindingContext()
        with self.assertRaises(ValueError):
            bc.transient('x')
        bc.transient('x', 'y')

    async def test_get(self):
        bc = BindingContext(locals={'x':'y'})
        not_found = object()
        result = bc.get('y', not_found)
        self.assertIs(result, not_found)
        result = bc.get('x', not_found)
        self.assertEqual(result, ('y', BindingScope.Local))

    async def test_falsy_callable(self):
        bc = BindingContext()
        dict_ = dict()
        bc.transient('test', dict_)
        
        # Async
        i = AsyncInjector(bc)
        result = await i.resolve('test')
        self.assertIs(result, dict_)

        # Sync
        i = Injector(bc)
        result = i.resolve('test')
        self.assertIs(result, dict_)

    async def test_falsy_base_binding(self):
        bc = BindingContext()
        with self.assertRaises(ValueError):
            bc.transient('', lambda:'test')

class Resolve(IsolatedAsyncioTestCase):
    async def test_resolve_callable(self):
        class A:
            pass

        # Async
        i = AsyncInjector()
        result = await i.resolve(A)
        self.assertIsInstance(result, A)

        # Sync
        i = Injector()
        result = i.resolve(A)
        self.assertIsInstance(result, A)

    async def test_resolve_noncallable(self):
        class A:
            pass
        bc = BindingContext(transients={A:'y'})
        
        # Async
        i = AsyncInjector(context=bc)
        result = await i.resolve(A)
        self.assertEqual(result, 'y')

        # Sync
        i = Injector(context=bc)
        result = i.resolve(A)
        self.assertEqual(result, 'y')

    async def test_resolve_string(self):
        bc = BindingContext(transients={'x':'y'})
        
        # Async
        i = AsyncInjector(context=bc)
        result = await i.resolve('x')
        self.assertEqual(result, 'y')

        # Sync
        i = AsyncInjector(context=bc)
        result = await i.resolve('x')
        self.assertEqual(result, 'y')

    async def test_resolve_awaitable(self):
        class A:
            pass    
        async def B(a:A):
            return ('_', a)

        # Async only
        i = AsyncInjector()
        _, result = await i.resolve(B)
        self.assertIsInstance(result, A)

    async def test_resolve_recursive(self):
        class A:
            pass

        class B:
            def __init__(self, a:A):
                self.a = a

        class C:
            def __init__(self, b:B):
                self.b = b

        # Async
        i = AsyncInjector()
        result = await i.resolve(C)
        self.assertIsInstance(result, C)
        self.assertIsInstance(result.b, B)
        self.assertIsInstance(result.b.a, A)

        # Sync
        i = Injector()
        result = i.resolve(C)
        self.assertIsInstance(result, C)
        self.assertIsInstance(result.b, B)
        self.assertIsInstance(result.b.a, A)


    async def test_scope_transient(self):
        class A:
            pass
        class B:
            def __init__(self, a1:A, a2:A):
                self.a1 = a1
                self.a2 = a2
        bc = BindingContext()
        bc.transient(A)

        # Async
        i = AsyncInjector(bc)
        result = await i.resolve(B)
        self.assertIsInstance(result.a1, A)
        self.assertIsInstance(result.a2, A)
        self.assertIsNot(result.a1, result.a2)

        # Sync
        i = Injector(bc)
        result = i.resolve(B)
        self.assertIsInstance(result.a1, A)
        self.assertIsInstance(result.a2, A)
        self.assertIsNot(result.a1, result.a2)

    async def test_scope_local(self):
        class A:
            pass
        class B:
            def __init__(self, a1:A, a2:A):
                self.a1 = a1
                self.a2 = a2
        bc = BindingContext()
        bc.local(A)
        
        # Async
        i = AsyncInjector(bc)
        result1 = await i.resolve(B)
        self.assertIsInstance(result1.a1, A)
        self.assertIsInstance(result1.a2, A)
        self.assertIs(result1.a1, result1.a2)

        result2 = await i.resolve(B)
        self.assertIsInstance(result2.a1, A)
        self.assertIsInstance(result2.a2, A)
        self.assertIs(result2.a1, result2.a2)

        self.assertIsNot(result1.a1, result2.a1)
        self.assertIsNot(result1.a2, result2.a2)

        # Sync
        i = Injector(bc)
        result1 = i.resolve(B)
        self.assertIsInstance(result1.a1, A)
        self.assertIsInstance(result1.a2, A)
        self.assertIs(result1.a1, result1.a2)

        result2 = i.resolve(B)
        self.assertIsInstance(result2.a1, A)
        self.assertIsInstance(result2.a2, A)
        self.assertIs(result2.a1, result2.a2)

        self.assertIsNot(result1.a1, result2.a1)
        self.assertIsNot(result1.a2, result2.a2)

    async def test_scope_singleton(self):
        class A:
            pass
        class B:
            def __init__(self, a1:A, a2:A):
                self.a1 = a1
                self.a2 = a2
        bc = BindingContext()
        bc.singleton(A)

        # Async
        i = AsyncInjector(bc)
        result1 = await i.resolve(B)
        self.assertIsInstance(result1.a1, A)
        self.assertIsInstance(result1.a2, A)
        self.assertIs(result1.a1, result1.a2)

        result2 = await i.resolve(B)
        self.assertIsInstance(result2.a1, A)
        self.assertIsInstance(result2.a2, A)
        self.assertIs(result2.a1, result2.a2)

        self.assertIs(result1.a1, result2.a1)
        self.assertIs(result1.a2, result2.a2)

        # Sync
        i = Injector(bc)
        result1 = i.resolve(B)
        self.assertIsInstance(result1.a1, A)
        self.assertIsInstance(result1.a2, A)
        self.assertIs(result1.a1, result1.a2)

        result2 = i.resolve(B)
        self.assertIsInstance(result2.a1, A)
        self.assertIsInstance(result2.a2, A)
        self.assertIs(result2.a1, result2.a2)

        self.assertIs(result1.a1, result2.a1)
        self.assertIs(result1.a2, result2.a2)

    async def test_default_mapping(self):
        class A:
            pass
        class B:
            def __init__(self, a:A):
                self.a = a

        # Async
        i = AsyncInjector()
        result = await i.resolve(B)
        self.assertIsInstance(result.a, A)

        # Sync
        i = Injector()
        result = i.resolve(B)
        self.assertIsInstance(result.a, A)

    async def test_implicit_mapping(self):
        class A:
            pass
        class B:
            def __init__(self, a:A):
                self.a = a
        bc = BindingContext()
        bc.local(A)

        # Async
        i = AsyncInjector(bc)
        result = await i.resolve(B)
        self.assertIsInstance(result.a, A)

        # Sync
        i = Injector(bc)
        result = i.resolve(B)
        self.assertIsInstance(result.a, A)

    async def test_explicit_mapping(self):
        class A:
            pass
        class A_:
            pass
        class B:
            def __init__(self, a:A):
                self.a = a
        bc = BindingContext(locals={A:A_})
        
        # Async
        i = AsyncInjector(bc)
        result = await i.resolve(B)
        self.assertIsInstance(result.a, A_)

        # Sync
        i = Injector(bc)
        result = i.resolve(B)
        self.assertIsInstance(result.a, A_)

    async def test_resolution_order(self):
        class A:
            pass
        class A_:
            pass
        class B:
            def __init__(self, a:A_):
                self.a = a

        bc = BindingContext(locals={'a':A})
        
        # Async
        i = AsyncInjector(bc)
        result = await i.resolve(B)
        self.assertIsInstance(result.a, A)

        # Sync
        i = Injector(bc)
        result = i.resolve(B)
        self.assertIsInstance(result.a, A)

    async def test_no_binding_for_positional(self):
        class A:
            def __init__(self, a):
                self.a = a
        
        # Async
        i = AsyncInjector()
        with self.assertRaises(TypeError):
            result = await i.resolve(A)

        # Sync
        i = Injector()
        with self.assertRaises(TypeError):
            result = i.resolve(A)

    async def test_default_scope(self):
        class A:
            pass
        
        class B:
            def __init__(self, a1:A, a2:A):
                self.a1 = a1
                self.a2 = a2
        
        # Async
        i = AsyncInjector(default_scope = BindingScope.Transient)
        result = await i.resolve(B)
        self.assertIsInstance(result.a1, A)
        self.assertIsInstance(result.a2, A)
        self.assertIsNot(result.a1, result.a2)
        
        i = AsyncInjector(default_scope = BindingScope.Local)
        result1 = await i.resolve(B)
        self.assertIsInstance(result1.a1, A)
        self.assertIsInstance(result1.a2, A)
        self.assertIs(result1.a1, result1.a2)
        result2 = await i.resolve(B)
        self.assertIsInstance(result2.a1, A)
        self.assertIsInstance(result2.a2, A)
        self.assertIsNot(result1.a1, result2.a1)

        i = AsyncInjector(default_scope = BindingScope.Singleton)
        result1 = await i.resolve(B)
        self.assertIsInstance(result1.a1, A)
        self.assertIsInstance(result1.a2, A)
        self.assertIs(result1.a1, result1.a2)
        result2 = await i.resolve(B)
        self.assertIsInstance(result2.a1, A)
        self.assertIsInstance(result2.a2, A)
        self.assertIs(result1.a1, result2.a1)

        # Sync
        i = Injector(default_scope = BindingScope.Transient)
        result = i.resolve(B)
        self.assertIsInstance(result.a1, A)
        self.assertIsInstance(result.a2, A)
        self.assertIsNot(result.a1, result.a2)
        
        i = Injector(default_scope = BindingScope.Local)
        result1 = i.resolve(B)
        self.assertIsInstance(result1.a1, A)
        self.assertIsInstance(result1.a2, A)
        self.assertIs(result1.a1, result1.a2)
        result2 = i.resolve(B)
        self.assertIsInstance(result2.a1, A)
        self.assertIsInstance(result2.a2, A)
        self.assertIsNot(result1.a1, result2.a1)

        i = Injector(default_scope = BindingScope.Singleton)
        result1 = i.resolve(B)
        self.assertIsInstance(result1.a1, A)
        self.assertIsInstance(result1.a2, A)
        self.assertIs(result1.a1, result1.a2)
        result2 = i.resolve(B)
        self.assertIsInstance(result2.a1, A)
        self.assertIsInstance(result2.a2, A)
        self.assertIs(result1.a1, result2.a1)

    async def test_duplicate_bindings(self):
        bc1 = BindingContext(singletons={'x':'y'})
        bc2 = BindingContext(locals={'x':'z'})
        
        # Async
        i = AsyncInjector(bc1)
        with self.assertRaises(AssertionError):
            result = await i.resolve('x', context=bc2)

        # Sync
        i = Injector(bc1)
        with self.assertRaises(AssertionError):
            result = i.resolve('x', context=bc2)

    async def test_falsy_cache(self):
        dict_ = {}
        class A:
            def __init__(self, a1:'test', a2:'test'): # noqa: F821
                self.a1 = a1
                self.a2 = a2

        bc = BindingContext()
        bc.local('test', lambda: {})
        
        # Async
        i = AsyncInjector(bc)
        result = await i.resolve(A)
        self.assertIs(result.a1, result.a2)

        # Sync
        i = Injector(bc)
        result = i.resolve(A)
        self.assertIs(result.a1, result.a2)

    async def test_falsy_name_with_annotation(self):
        dict_ = {}
        class A:
            pass

        class B:
            def __init__(self, test:A):
                self.test = test
        
        bc = BindingContext()
        bc.transient('test', lambda: dict_)
        
        # Async
        i = AsyncInjector(bc)
        result = await i.resolve(B)
        self.assertIs(result.test, dict_)

        # Sync
        i = Injector(bc)
        result = i.resolve(B)
        self.assertIs(result.test, dict_)

class UseCases(IsolatedAsyncioTestCase):
    async def test_string_injection(self):
        class A:
            pass

        class B:
            def __init__(self, a):
                self.a = a

        bc = BindingContext()
        bc.transient('a', A)
        bc.transient('b', B)

        # Async
        i = AsyncInjector(bc)
        result = await i.resolve('b')
        self.assertIsInstance(result, B)
        self.assertIsInstance(result.a, A)

        # Sync
        i = Injector(bc)
        result = i.resolve('b')
        self.assertIsInstance(result, B)
        self.assertIsInstance(result.a, A)

    async def test_default_type_injection(self):
        class A:
            pass

        class B:
            def __init__(self, a:A):
                self.a = a

        # Async
        i = AsyncInjector()
        result = await i.resolve(B)
        self.assertIsInstance(result, B)
        self.assertIsInstance(result.a, A)

        # Sync
        i = Injector()
        result = i.resolve(B)
        self.assertIsInstance(result, B)
        self.assertIsInstance(result.a, A)

    async def test_implicit_type_injection(self):
        class A:
            pass

        class B:
            def __init__(self, a:A):
                self.a = a

        bc = BindingContext()
        bc.transient(A)
        bc.transient(B)

        # Async
        i = AsyncInjector(bc)
        result = await i.resolve(B)
        self.assertIsInstance(result, B)
        self.assertIsInstance(result.a, A)

        # Sync
        i = Injector(bc)
        result = i.resolve(B)
        self.assertIsInstance(result, B)
        self.assertIsInstance(result.a, A)

    async def test_explicit_type_injection(self):
        class A:
            pass

        class B:
            def __init__(self, a:A):
                self.a = a

        bc = BindingContext()
        bc.transient(A, A)
        bc.transient(B, B)
        
        # Async
        i = AsyncInjector(bc)
        result = await i.resolve(B)
        self.assertIsInstance(result, B)
        self.assertIsInstance(result.a, A)

        # Sync
        i = Injector(bc)
        result = i.resolve(B)
        self.assertIsInstance(result, B)
        self.assertIsInstance(result.a, A)

    async def test_mixed_injection(self):
        class A:
            pass

        class B:
            def __init__(self, a:A, my_value):
                self.a = a
                self.my_value = my_value

        bc = BindingContext()
        bc.transient(A)
        bc.transient(B, B)
        bc.transient('my_value', 7)
        
        # Async
        i = AsyncInjector(bc)
        result = await i.resolve(B)
        self.assertIsInstance(result, B)
        self.assertIsInstance(result.a, A)
        self.assertEqual(result.my_value, 7)

        # Sync
        i = Injector(bc)
        result = i.resolve(B)
        self.assertIsInstance(result, B)
        self.assertIsInstance(result.a, A)
        self.assertEqual(result.my_value, 7)

    async def test_falsy_resolution(self):
        dict_ = {}

        class A:
            def __init__(self, test):
                self.test = test

        bc = BindingContext()
        bc.transient('test', dict_)
        
        # Async
        i = AsyncInjector(bc)
        result = await i.resolve(A)
        self.assertIs(result.test, dict_)

        # Sync
        # Async
        i = Injector(bc)
        result = i.resolve(A)
        self.assertIs(result.test, dict_)
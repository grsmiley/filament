from enum import Enum
import inspect

class BindingScope(Enum):
        Transient = 1
        Local = 2
        Singleton = 3

class BindingContext:
    def __init__(self, singletons = None, locals = None, transients = None):
        self._bindings = {} # (callable, binding type)
   
        if singletons:
            for k,v in singletons.items():
                self.singleton(k, v)

        if locals:
            for k,v in locals.items():
                self.local(k, v)

        if transients:
            for k,v in transients.items():
                self.transient(k, v)

    def singleton(self, base, callable=None):
        self._bind(base, callable, BindingScope.Singleton)

    def local(self, base, callable=None):
        self._bind(base, callable, BindingScope.Local)

    def transient(self, base, callable=None):
        self._bind(base, callable, BindingScope.Transient)

    def _bind(self, base, callable, scope):
        if not base:
            # intentionally checking falsiness rather than None
            raise ValueError(f"Base {base} cannot be falsy.")

        if isinstance(base, str) and callable is None:
            raise ValueError(f"Base {base} of type str must be explicitly mapped.")

        # can't coalesce with (callable or base, scope) because 'data', {} should be valid
        self._bindings[base] = (base if callable is None else callable, scope)

    def get(self, target, default=None):
        return self._bindings.get(target, default)

class Injector:
    def __init__(self, context:BindingContext=None, default_scope = BindingScope.Local):
        self._context = context or BindingContext()
        self._default_scope = default_scope
        self._cache = {} # singletons

    def resolve(self, target, context:BindingContext=None):
        context = context or BindingContext()

        # ensure contexts both locally and at the injector level don't have collisions        
        collision = context._bindings.keys() & self._context._bindings.keys()
        assert not collision, f"Injector context and local context have duplicate bindings ({collision})."

        cache = {} # local scope
        
        def resolve_(target):
            # search cache first
            cached = cache.get(target)
            if cached is None:
                cached = self._cache.get(target)
            if cached is not None:
                return cached
            
            # get binding definition or default - local before global
            # ok to coalesce here since target shouldn't be falsy
            binding = context.get(target) or self._context.get(target)

            if not binding and isinstance(target, str):
                return None

            concrete, scope = binding or (target, self._default_scope)

            if callable(concrete):
                args = {}
                for param in inspect.signature(concrete).parameters.values():
                    result = resolve_(param.name)
                    if result is None and param.annotation is not inspect.Parameter.empty:
                        result = resolve_(param.annotation)

                    if result is not None:
                        args[param.name] = result

                result = concrete(**args)
            else:
                # not a callable
                result = concrete

            # set cache
            match scope:
                case BindingScope.Singleton:
                    self._cache[target] = result
                case BindingScope.Local:
                    cache[target] = result

            return result

        return resolve_(target)


class AsyncInjector:
    def __init__(self, context:BindingContext=None, default_scope = BindingScope.Local):
        self._context = context or BindingContext()
        self._default_scope = default_scope
        self._cache = {} # singletons

    async def resolve(self, target, context:BindingContext=None):
        context = context or BindingContext()

        # ensure contexts both locally and at the injector level don't have collisions        
        collision = context._bindings.keys() & self._context._bindings.keys()
        assert not collision, f"Injector context and local context have duplicate bindings ({collision})."

        cache = {} # local scope
        
        async def resolve_(target):
            # search cache first
            cached = cache.get(target)
            if cached is None:
                cached = self._cache.get(target)
            if cached is not None:
                return cached
            
            # get binding definition or default - local before global
            # ok to coalesce here since target shouldn't be falsy
            binding = context.get(target) or self._context.get(target)

            if not binding and isinstance(target, str):
                return None

            concrete, scope = binding or (target, self._default_scope)

            if callable(concrete):
                args = {}
                for param in inspect.signature(concrete).parameters.values():
                    result = await resolve_(param.name)
                    if result is None and param.annotation is not inspect.Parameter.empty:
                        result = await resolve_(param.annotation)

                    if result is not None:
                        args[param.name] = result

                result = concrete(**args)
                if inspect.isawaitable(result):
                    result = await result
            else:
                # not a callable
                result = concrete

            # set cache
            match scope:
                case BindingScope.Singleton:
                    self._cache[target] = result
                case BindingScope.Local:
                    cache[target] = result

            return result

        return await resolve_(target)
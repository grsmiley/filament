[![tests](https://github.com/grsmiley/filament/actions/workflows/tests.yml/badge.svg)](https://github.com/grsmiley/filament/actions/workflows/tests.yml)
[![linting](https://github.com/grsmiley/filament/actions/workflows/linting.yml/badge.svg)](https://github.com/grsmiley/filament/actions/workflows/linting.yml)

# filament
Async python dependency injection for beautiful code.

### Why choose filament?
- It's simple: With just over 100 lines of code, you can master it in an hour
- It's powerful: It scales with your codebase, from a single file script to a massively decoupled project
- It's flexible: use it implicitly, imperatively, or declaratively
- It gets out of your way: Your code remains the focal point without a bunch of decorators and configuration plumbing

### Key features
- Asynchronous where needed
- Supports three scopes: singleton, local, and transient
- Injects through type annotations or argument names
- Injects any callable (classes, dataclasses,functions, etc.)
- Handles circular dependencies with singleton and local scopes

## Quick start
```python
import asyncio
from filament import Injector

async def driver_name():
    return 'Fernando'

class Driver:
    def __init__(self, name:driver_name):
        self.name = name

class Car:
    def __init__(self, driver:Driver):
        self.driver = driver

async def main():
    injector = Injector()
    car = await injector.resolve(Car)
    print(f"Driver's name: {car.driver.name}")

asyncio.run(main())
```
Outputs:
```
Driver's name: Fernando
```
In this example, Filament is using the type declarations to instantiate and inject the classes. Notice that the driver name, however, is injected from an asynchronous function.

## Injection targets
Any callable can be used as a target for injection. Here are some examples:

Classes:
```python
class Dependency:
    pass

class A:
    def __init__(self, dep:Dependency):
        self.dependency = dep
```

DataClasses:
```python
from dataclasses import dataclass

class Dependency:
    pass

@dataclass
class A:
    dep:Dependency
```

Synchronous functions:
```python
class Dependency:
    pass

def a(dep:Dependency):
    pass
```

Asynchronous functions:
```python
class Dependency:
    pass

async def a(dep:Dependency):
    pass
```

## Injection by type annotation
By default, Filament will inject a callable using type annotations.

Example:
```python
import asyncio
from filament import Injector

class Logger:
    def log(self, message):
        print(message)

class AuthenticationService:
    def __init__(self, logger:Logger):
        self.logger = logger

    def authenticate(self, login, password):
        if (login, password) != ('tim', 'secret123'):
            self.logger.log('Authentication failed')

async def main():
    injector = Injector()
    auth_service = await injector.resolve(AuthenticationService)
    auth_service.authenticate('tim', 'wrongpass')

asyncio.run(main())
```
Outputs:
```
Authentication failed
```
The key part here is the type annotation `logger:Logger` in the AuthenticationService constructor.

## Injection by parameter name
In some cases, you may want to avoid type annotations or importing types just for the sake of injecting dependencies. You can explicitly map bindings through the `BindingContext`.
```python
import asyncio
from filament import Injector, BindingContext

class Logger:
    def log(self, message):
        print(message)

class AuthenticationService:
    def __init__(self, logger):
        self.logger = logger

    def authenticate(self, login, password):
        if (login, password) != ('tim', 'secret123'):
            self.logger.log('Authentication failed')

async def main():
    context = BindingContext()
    context.transient('logger', Logger)
    injector = Injector(context)
    auth_service = await injector.resolve(AuthenticationService)
    auth_service.authenticate('tim', 'wrongpass')

asyncio.run(main())
```
Outputs:
```
Authentication failed
```
To create a binding, you create a `BindingContext`, define the mapping (in this case it's scoped as `transient`), and link the parameter name `logger` to the type `Logger`. Then, pass the `BindingContext` into the `Injector`.

## Binding Context
A `BindingContext` can be used to explicitly control how objects are built and the scope of their lifecycle. It is optionally created and passed into the injector:
```python
from filament import Injector, BindingContext
context = BindingContext()
injector = Injector(context)
```
The binding context can now be used to map objects and set scope.

### Scopes
Filament offers support for three scopes: singleton, local, and transient. Each of these scopes determines the lifecycle of the injected object. Consider this hierarchy:

```python
class Dependency:
    pass

class B:
    dependency2:Dependency
    dependency3:Dependency

class A:
    b:B
    dependency1:Dependency
```

*Transient* scope instantiates a new object every time it is needed. `dependency1`, `dependency2`, and `dependency3` will each be a separate instance.

*Local* scope instantiates a new object and reuses it only to resolve the call chain. `dependency1`, `dependency2`, and `dependency3` will be the same instance. If `injector.resolve(A)` is called a second time, a new instance will be created to resolve all three again. This is the default scope.

*Singleton* scope instantiates a new object and reuses it for as long as your application is running. It will only be instantiated once.

The scope is defined on the `BindingContext`:
```python
from filament import BindingContext

class A:
    pass

class B:
    pass

class C:
    pass

context = BindingContext()
context.transient(A)
context.local(B)
context.singleton(C)
```

### Mappings
Types can be mapped with the `BindingContext` to control which class should be injected. This is helpful to define concrete classes that inherit from a base:
```python
import asyncio
from filament import Injector, BindingContext

class Base:
    pass

class Concrete(Base):
    pass

class Logger:
    def __init__(self, my_dependency:Base):
        self.my_dependency = my_dependency

async def main():
    context = BindingContext()
    context.transient(Base, Concrete)
    injector = Injector(context)    
    logger = await injector.resolve(Logger)
    assert isinstance(logger.my_dependency, Concrete)

asyncio.run(main())
```

Parameters can also be mapped as strings:
```python
import asyncio
from filament import Injector, BindingContext

class Concrete:
    pass

class Logger:
    def __init__(self, my_dependency:Concrete):
        self.my_dependency = my_dependency

async def main():
    context = BindingContext()
    context.transient('my_dependency', Concrete)
    injector = Injector(context)    
    logger = await injector.resolve(Logger)
    assert isinstance(logger.my_dependency, Concrete)

asyncio.run(main())
```

Lamdas and functions can be mapped to use as factories:
```python
import asyncio
from filament import Injector, BindingContext

class Concrete:
    def __init__(self, name):
        self.name = name

class Logger:
    def __init__(self, my_dependency:Concrete):
        self.my_dependency = my_dependency

async def main():
    context = BindingContext()
    context.transient(Concrete, lambda: Concrete('Tim'))
    injector = Injector(context)
    logger = await injector.resolve(Logger)
    assert logger.my_dependency.name == 'Tim'

asyncio.run(main())
```
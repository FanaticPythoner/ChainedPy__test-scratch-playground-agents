"""ChainedPy registration system for decorators and plugins.

This module provides the core registration decorators ([then][chainedpy.register.then], [as_][chainedpy.register.as_], [processor][chainedpy.register.processor])
that dynamically add methods to the [Chain][chainedpy.chain.Chain] class. It enables the plugin system by allowing
developers to register custom transformation methods, conversion methods, and processors
that become available on all Chain instances.

The registration system works by decorating factory functions that create [Link][chainedpy.link.Link], [Wrapper][chainedpy.link.Wrapper],
or [Processor][chainedpy.link.Processor] instances. When a decorated function is imported, it automatically registers
the corresponding method on the Chain class, making it available for use in chain pipelines.

Note:
    All registration happens at import time. Simply importing a module with decorated
    functions will register those methods on the Chain class. This enables the plugin
    architecture where importing plugin modules automatically extends Chain functionality.

Example:
    ```python
    from chainedpy.register import then, as_, processor
    from chainedpy.link import Link, Wrapper, Processor
    from chainedpy import Chain

    # Register a transformation method
    @then("multiply")
    def create_multiply_link(factor: int) -> Link[int, int]:
        class MultiplyLink(Link[int, int]):
            name = "multiply"
            async def __call__(self, arg: int) -> int:
                return arg * factor
        return MultiplyLink()

    # Now available on all Chain instances
    result = await (
        Chain(5)
        .then_multiply(3)  # Uses the registered method
    )
    assert result == 15
    ```

See Also:
    - [then][chainedpy.register.then]: Decorator for transformation methods
    - [as_][chainedpy.register.as_]: Decorator for conversion methods
    - [processor][chainedpy.register.processor]: Decorator for processor methods
    - [Chain][chainedpy.chain.Chain]: Class that receives the registered methods
"""

from __future__ import annotations
import inspect
from typing import Callable, TypeVar, Type, Any, TYPE_CHECKING

from importlib import import_module
import pkgutil
import pathlib

from .typing    import P, I_co, O_co
from .link      import Link, Wrapper, Processor
from .chain     import Chain
from .exceptions import ValidationError

# @@ STEP 1: Define helper utilities. @@

def _clone_sig(dst: Callable[..., object], src: Callable[..., object]) -> None:
    """Copy signature and annotations from source to destination function.

    This helper ensures IDEs see the real types for dynamically created methods.

    :param dst: Destination function to copy signature to.
    :type dst: Callable[..., object]
    :param src: Source function to copy signature from.
    :type src: Callable[..., object]
    """
    # @@ STEP 1: Copy function metadata from source to destination. @@
    dst.__annotations__ = src.__annotations__.copy()
    dst.__signature__   = inspect.signature(src)       # type: ignore[attr-defined]
    dst.__doc__         = src.__doc__

# @@ STEP 2: Define @then decorator. @@

ThenFactory = Callable[P, Link[I_co, O_co]]

def then(name: str) -> Callable[[ThenFactory], ThenFactory]:
    """Register a transformation; adds .then_<name>() to Chain immediately.

    :param name: Name of the transformation method to create.
    :type name: str
    :return Callable[[ThenFactory], ThenFactory]: Decorator function for the transformation factory.
    """
    def decorator(factory: ThenFactory) -> ThenFactory:
        """Decorator that registers the transformation factory.

        :param factory: Factory function that creates Link instances.
        :type factory: ThenFactory
        :return ThenFactory: The original factory function.
        """
        def method(self: Chain[I_co], /, *a: P.args, **k: P.kwargs) -> Chain[O_co]:  # type: ignore[name-defined]
            """Dynamically created then_ method for Chain class.

            :param self: Chain instance.
            :type self: Chain[I_co]
            :param a: Positional arguments for the factory.
            :type a: P.args
            :param k: Keyword arguments for the factory.
            :type k: P.kwargs
            :return Chain[O_co]: New Chain with the added link.
            """
            # @@ STEP 1: Create link from factory and add to chain. @@
            link = factory(*a, **k)
            return self._add_link(link)  # pylint: disable=protected-access

        # @@ STEP 2: Set method metadata for proper IDE support. @@
        method.__qualname__ = f"Chain.then_{name}"
        method.__name__     = f"then_{name}"
        _clone_sig(method, factory)
        setattr(Chain, method.__name__, method)
        return factory
    return decorator

# ------------------------------------------------------------------ #
# 2)  @as_                                                           #
# ------------------------------------------------------------------ #
AsFactory = Callable[P, Wrapper[I_co, O_co]]

def as_(name: str) -> Callable[[AsFactory], AsFactory]:
    """Register a wrapper; adds .as_<name>() to Chain immediately.

    :param name: Name of the wrapper method to create.
    :type name: str
    :return Callable[[AsFactory], AsFactory]: Decorator function for registering wrapper factories.
    """
    def decorator(factory: AsFactory) -> AsFactory:
        """Decorator that registers the wrapper factory.

        :param factory: Factory function that creates Wrapper instances.
        :type factory: AsFactory
        :return AsFactory: The original factory function.
        """
        def method(self: Chain[O_co], /, *a: P.args, **k: P.kwargs) -> Chain[O_co]:  # type: ignore[name-defined]
            """Dynamically created as_ method for Chain class.

            :param self: Chain instance.
            :type self: Chain[O_co]
            :param a: Positional arguments for the factory.
            :type a: P.args
            :param k: Keyword arguments for the factory.
            :type k: P.kwargs
            :return Chain[O_co]: New Chain with the wrapped last link.
            :raises ValidationError: If no previous link exists to wrap.
            """
            # @@ STEP 1: Validate that there's a previous link to wrap. @@
            if not self._links:  # pylint: disable=protected-access
                raise ValidationError(f"no previous link to wrap for 'as_{name}'")

            # @@ STEP 2: Create wrapper and wrap the last link. @@
            wrapper = factory(*a, **k)
            new_last = wrapper.wrap(self._links[-1])  # type: ignore[arg-type] # pylint: disable=protected-access
            return self._replace_last(new_last)        # pylint: disable=protected-access

        # @@ STEP 3: Set method metadata for proper IDE support. @@
        method.__qualname__ = f"Chain.as_{name}"
        method.__name__     = f"as_{name}"
        _clone_sig(method, factory)
        setattr(Chain, method.__name__, method)
        return factory
    return decorator

# ------------------------------------------------------------------ #
# 3)  @processor                                                     #
# ------------------------------------------------------------------ #
TProc = TypeVar("TProc", bound=Processor[Any, Any])

if TYPE_CHECKING:
    # Imports only for the stub signature
    from .link  import Processor as _P
    from .chain import Chain as _C

def _then_process_stub(
    self: "Chain[I_co]",
    proc: "Processor[I_co, O_co]",
    *,
    param: str | None = None
) -> "Chain[O_co]": ...

def processor(name: str) -> Callable[[Type[TProc]], Type[TProc]]:
    """Decorator for Processor classes - no registry needed.

    :param name: Name of the processor.
    :type name: str
    :return Callable[[Type[TProc]], Type[TProc]]: Decorator function for registering processor classes.
    """
    def decorator(cls: Type[TProc]) -> Type[TProc]:
        """Decorator that registers the processor class.

        :param cls: Processor class to register.
        :type cls: Type[TProc]
        :return Type[TProc]: The original processor class.
        """
        # @@ STEP 1: Add universal then_process method once. @@
        if not hasattr(Chain, "then_process"):
            def then_process(
                self: Chain[I_co],
                proc: Processor[I_co, O_co],
                *,
                param: str | None = None
            ) -> Chain[O_co]:
                """Process method for Chain class.

                :param self: Chain instance.
                :type self: Chain[I_co]
                :param proc: Processor instance to apply.
                :type proc: Processor[I_co, O_co]
                :param param: Optional parameter for processor, defaults to None.
                :type param: str | None, optional
                :return Chain[O_co]: New Chain with the processor link.
                """
                # || S.S. 1.1: Create processor link class. ||
                class _ProcLink(Link[I_co, O_co]):
                    name = f"process_{proc.name}"
                    async def __call__(self, arg: I_co) -> O_co:
                        return proc.apply(arg, param=param)
                return self._add_link(_ProcLink())  # pylint: disable=protected-access

            # || S.S. 1.2: Set method metadata and attach to Chain. ||
            _clone_sig(then_process, _then_process_stub)
            setattr(Chain, "then_process", then_process)

        return cls
    return decorator


def init_plugins(package_path: pathlib.Path) -> None:
    """Initialize all plugins in the specified package path.

    Example:
        ```python
        from chainedpy.register import init_plugins
        from pathlib import Path
        import shutil

        # Create test plugin structure
        plugin_dir = Path("test_plugins")
        plugin_dir.mkdir(exist_ok=True)
        (plugin_dir / "__init__.py").write_text("")

        # Create then plugin
        then_dir = plugin_dir / "then"
        then_dir.mkdir(exist_ok=True)
        (then_dir / "__init__.py").write_text("")
        (then_dir / "then_custom.py").write_text('''
from chainedpy.register import then
from chainedpy.link import Link

@then("custom")
def create_custom_link() -> Link[str, str]:
    class CustomLink(Link[str, str]):
        async def __call__(self, arg: str) -> str:
            return f"custom: {arg}"
    return CustomLink()
        ''')

        # Initialize plugins
        init_plugins(plugin_dir)

        # Now custom method should be available
        from chainedpy import Chain
        result = await (
            Chain("test")
            .then_custom()
        )
        assert result == "custom: test"

        # Cleanup
        shutil.rmtree(plugin_dir, ignore_errors=True)
        ```

    :param package_path: Path to the package containing plugins.
    :type package_path: [pathlib.Path][pathlib.Path]
    """
    # @@ STEP 1: Import each plugin module to trigger decorator registration. @@
    for mod in pkgutil.iter_modules([str(package_path)]):
        import_module(f"chainedpy.plugins.{mod.name}")

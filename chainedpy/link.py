"""ChainedPy Link, Wrapper, and Processor abstractions.

This module defines the core abstractions for ChainedPy's transformation system,
including async links, decorating wrappers, and stateless processors. These abstractions
form the foundation of the chain execution pipeline, providing type-safe transformation
interfaces that support both synchronous and asynchronous operations.

The module provides three main abstractions: [Link][chainedpy.link.Link] for pure transformations,
[Wrapper][chainedpy.link.Wrapper] for decorating existing links, and [Processor][chainedpy.link.Processor] for stateless
transformations with optional parameters. All abstractions are designed to be composable
and maintain strict type safety throughout the transformation pipeline.

Note:
    All abstractions use generic type parameters to ensure type safety and proper
    type inference throughout the chain execution pipeline.

Example:
    ```python
    from chainedpy.link import Link, Processor
    from chainedpy import Chain

    # Custom Link implementation
    class UppercaseLink(Link[str, str]):
        name = "uppercase"

        async def __call__(self, arg: str) -> str:
            return arg.upper()

    # Custom Processor implementation
    class PrefixProcessor(Processor[str, str]):
        name = "add_prefix"

        def apply(self, value: str, *, param: str | None = None) -> str:
            prefix = param or "PREFIX: "
            return prefix + value

    # Usage in chains
    result = await (
        Chain("hello")
        .then_map(UppercaseLink())
        .then_process(PrefixProcessor(), param="GREETING: ")
    )
    ```

See Also:
    - [Chain][chainedpy.chain.Chain]: Main chain class that uses these abstractions
    - [typing][chainedpy.typing]: Type definitions used by these abstractions
    - [maybe_await][chainedpy.link.maybe_await]: Utility for handling async/sync values
"""
from __future__ import annotations
import abc
import inspect
from typing import Generic, Awaitable
from .typing import I_co, O_co

class Link(Generic[I_co, O_co], abc.ABC):
    """Pure async transformation from I->O.

    Abstract base class for all async transformations in ChainedPy.
    Links represent pure functions that transform input of type I to output of type O,
    forming the fundamental building blocks of the chain execution pipeline.

    Each Link must have a name for debugging and error reporting purposes, and must
    implement the async __call__ method to perform the actual transformation.

    Example:
        ```python
        from chainedpy.link import Link

        class MultiplyLink(Link[int, int]):
            name = "multiply"

            def __init__(self, factor: int):
                self.factor = factor

            async def __call__(self, arg: int) -> int:
                return arg * self.factor

        # Usage
        link = MultiplyLink(3)
        result = await link(5)  # Returns 15
        ```
    """
    name: str

    @abc.abstractmethod
    async def __call__(self, arg: I_co) -> O_co:
        """Apply the transformation to the input argument.

        Example:
            ```python
            # Implementation example
            async def __call__(self, arg: str) -> str:
                # Perform transformation
                result = arg.upper()
                return result
            ```

        :param arg: Input value to transform.
        :type arg: [I_co][chainedpy.typing.I_co]
        :return [O_co][chainedpy.typing.O_co]: Transformed output value.
        """
        ...

class Wrapper(Generic[I_co, O_co], abc.ABC):
    """Decorates another Link without changing its types.

    Abstract base class for decorators that wrap existing Links
    while preserving their input and output types. Wrappers enable
    cross-cutting concerns like logging, caching, or error handling
    to be applied to any Link without modifying the Link itself.

    Example:
        ```python
        from chainedpy.link import Wrapper, Link

        class LoggingWrapper(Wrapper[str, str]):
            def wrap(self, inner: Link[str, str]) -> Link[str, str]:
                class LoggedLink(Link[str, str]):
                    name = f"logged_{inner.name}"

                    async def __call__(self, arg: str) -> str:
                        print(f"Input: {arg}")
                        result = await inner(arg)
                        print(f"Output: {result}")
                        return result

                return LoggedLink()
        ```
    """

    @abc.abstractmethod
    def wrap(self, inner: Link[I_co, O_co]) -> Link[I_co, O_co]:
        """Wrap an inner Link with additional behavior.

        Example:
            ```python
            def wrap(self, inner: Link[str, str]) -> Link[str, str]:
                # Create a new Link that wraps the inner one
                class WrappedLink(Link[str, str]):
                    name = f"wrapped_{inner.name}"

                    async def __call__(self, arg: str) -> str:
                        # Add behavior before
                        processed_arg = self.preprocess(arg)
                        # Call inner link
                        result = await inner(processed_arg)
                        # Add behavior after
                        return self.postprocess(result)

                return WrappedLink()
            ```

        :param inner: The Link to wrap.
        :type inner: [Link][chainedpy.link.Link][[I_co][chainedpy.typing.I_co], [O_co][chainedpy.typing.O_co]]
        :return [Link][chainedpy.link.Link][[I_co][chainedpy.typing.I_co], [O_co][chainedpy.typing.O_co]]: Wrapped Link with same types.
        """
        ...

class Processor(Generic[I_co, O_co], abc.ABC):
    """Stateless transform function used by then_process.

    Abstract base class for stateless processors that transform values
    with optional parameters. Processors are designed to be reusable
    transformation functions that can accept configuration parameters
    to modify their behavior.

    Example:
        ```python
        from chainedpy.link import Processor

        class FormatProcessor(Processor[str, str]):
            name = "format"

            def apply(self, value: str, *, param: str | None = None) -> str:
                template = param or "Value: {}"
                return template.format(value)

        # Usage
        processor = FormatProcessor()
        result = processor.apply("hello", param="Greeting: {}")
        # Returns "Greeting: hello"
        ```
    """
    name: str

    @abc.abstractmethod
    def apply(self, value: I_co, *, param: str | None = None) -> O_co:
        """Apply the processor transformation to a value.

        Example:
            ```python
            def apply(self, value: str, *, param: str | None = None) -> str:
                # Use parameter to modify behavior
                if param:
                    return f"{param}: {value}"
                else:
                    return value.upper()
            ```

        :param value: Input value to process.
        :type value: [I_co][chainedpy.typing.I_co]
        :param param: Optional parameter for the transformation, defaults to None.
        :type param: [str][str] | [None][None], optional
        :return [O_co][chainedpy.typing.O_co]: Processed output value.
        """
        ...

# @@ STEP 1: Define helper utilities. @@

async def maybe_await(value: Awaitable[O_co] | O_co) -> O_co:
    """Await a value if it's a coroutine, otherwise return it directly.

    Note:
        This utility function enables seamless handling of both synchronous and
        asynchronous transformations within the chain pipeline.

    Example:
        ```python
        from chainedpy.link import maybe_await

        # With synchronous value
        result = await maybe_await("hello")
        assert result == "hello"

        # With asynchronous value
        async def async_func():
            return "world"

        result = await maybe_await(async_func())
        assert result == "world"
        ```

    :param value: Value that may or may not be awaitable.
    :type value: [Awaitable][typing.Awaitable][[O_co][chainedpy.typing.O_co]] | [O_co][chainedpy.typing.O_co]
    :return [O_co][chainedpy.typing.O_co]: The resolved value.
    """
    return await value if inspect.iscoroutine(value) else value

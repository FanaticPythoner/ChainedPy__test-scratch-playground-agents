"""ChainedPy Core Chain Implementation.

This module contains the core [Chain][chainedpy.chain.Chain] class that provides the fluent chaining API.
The Chain class is the heart of ChainedPy, enabling asynchronous pipeline execution with type safety
and extensibility. It implements a minimal asynchronous pipeline runner that supports method chaining
with full type safety through TypeScript-style generic parameters and protocol-based type checking.

The module provides both runtime implementation and static typing shims to ensure optimal type
inference while maintaining clean separation between runtime behavior and type checking concerns.
The runtime [Chain][chainedpy.chain.Chain] class handles execution, while the [_ChainMethods][chainedpy.chain._ChainMethods]
protocol provides comprehensive type hints for all available chain methods.

Note:
    This module uses TYPE_CHECKING blocks to provide enhanced type hints without affecting
    runtime performance. The Chain class is designed to be both performant at runtime and
    fully type-safe during development.

Example:
    ```python
    from chainedpy import Chain

    # Basic chain execution
    result = await (
        Chain("hello")
        .then_map(str.upper)
        .then_map(lambda s: s + " WORLD")
    )

    assert result == "HELLO WORLD"

    # Chain with conditional logic
    result = await (
        Chain(42)
        .then_if(
            lambda x: x > 0,
            lambda x: x * 2,
            lambda x: x * -1
        )
    )

    assert result == 84
    ```

See Also:
    - [Link][chainedpy.link.Link]: Individual pipeline steps module
    - [register][chainedpy.register]: Method registration decorators module
    - [exceptions][chainedpy.exceptions]: Chain-specific exceptions module
"""
from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Awaitable,
    Callable,
    Generic,
    Iterable,
    Literal,
    Protocol,
    TypeVar,
    overload,
)

from .exceptions import ValidationError, ChainError
from .link import Link

# @@ STEP 1: Define generic parameters. @@
_T = TypeVar("_T", covariant=True)
"""[TypeVar][typing.TypeVar]: Primary type variable for values carried by the [Chain][chainedpy.chain.Chain].

    This is a covariant type variable used throughout the [Chain][chainedpy.chain.Chain] class to represent
    the type of value being carried through the chain operations. Covariance allows
    for proper type inheritance in chain transformations.

    :type: [TypeVar][typing.TypeVar] (covariant=True)
"""

_I = TypeVar("_I")
"""[TypeVar][typing.TypeVar]: Input type variable for transformations and key functions.

    Used to represent the input type for transformation functions, key extractors,
    and other operations that accept values from external sources.

    :type: [TypeVar][typing.TypeVar]
"""

_O = TypeVar("_O")
"""[TypeVar][typing.TypeVar]: Output type variable for transformation results.

    Represents the output type for transformation functions and operations
    that produce new values from chain transformations.

    :type: [TypeVar][typing.TypeVar]
"""

_E = TypeVar("_E")
"""[TypeVar][typing.TypeVar]: Element type variable for iterable operations.

    Used for operations that work with individual elements of collections,
    such as mapping, filtering, and reducing operations.

    :type: [TypeVar][typing.TypeVar]
"""

_V = TypeVar("_V")
"""[TypeVar][typing.TypeVar]: Value type variable for collection transformations.

    Represents value types in key-value operations, dictionary transformations,
    and other collection-based operations.

    :type: [TypeVar][typing.TypeVar]
"""

# ---------------------------------------------------------------------------
#                       ********  RUNTIME CORE  ********
# ---------------------------------------------------------------------------
class Chain(Generic[_T]):
    """Minimal asynchronous pipeline runner (runtime part).

    The [Chain][chainedpy.chain.Chain] class provides the core fluent chaining API for ChainedPy.
    It enables asynchronous pipeline execution with type safety and extensibility.
    Each Chain instance carries a seed value and a sequence of [Link][chainedpy.link.Link] objects that
    define the transformation pipeline. The chain is immutable - each method call
    returns a new Chain instance with the additional transformation.

    :ivar _seed: The initial value that starts the chain execution
    :vartype _seed: _T
    :ivar _links: Tuple of [Link][chainedpy.link.Link] objects representing the transformation pipeline
    :vartype _links: tuple[Link[object, object], ...]

    Note:
        Chain instances are immutable. Each method call returns a new Chain
        with the additional transformation, preserving the original chain.

    See Also:
        - [Link][chainedpy.link.Link]: Individual pipeline transformation steps
        - [_run][chainedpy.chain.Chain._run]: Core execution method for the pipeline
    """

    __slots__ = ("_seed", "_links")

    _links: tuple[Link[object, object], ...]

    def __init__(self, value: _T | None = None, **kwargs):
        """Initialize a Chain with a seed value or kwargs.

        :param value: Initial value for the chain, defaults to None.
        :type value: _T | None, optional
        :param kwargs: Keyword arguments as initial value.
        :type kwargs: Any
        :raises ValidationError: If both value and kwargs are provided.

        Example:
            ```python
            from chainedpy import Chain

            # Initialize with a value
            chain1 = Chain("hello")

            # Initialize with kwargs
            chain2 = Chain(name="John", age=30)

            # Initialize with None (empty chain)
            chain3 = Chain()

            # Error case - cannot provide both
            try:
                Chain("value", name="John")
            except ValidationError as e:
                print(f"Expected error: {e}")
            ```
        """
        # @@ STEP 1: Validate input parameters. @@
        if value is not None and kwargs:
            raise ValidationError("Cannot provide both value and kwargs")

        # @@ STEP 2: Set seed value. @@
        if kwargs:
            self._seed: _T = kwargs  # type: ignore[assignment]
        else:
            self._seed: _T = value  # type: ignore[assignment]

        # @@ STEP 3: Initialize empty links tuple. @@
        self._links = ()

    # ------ helpers ------------------------------------------------------
    def _add_link(self, link: Link[_T, _O]) -> "Chain[_O]":  # type: ignore[type-var]
        """Add a link to the chain and return a new chain.

        Note:
            This method creates a new Chain instance rather than modifying the existing one,
            maintaining immutability of chain objects.

        Example:
            ```python
            from chainedpy import Chain
            from chainedpy.link import Link

            # Create a transformation link
            upper_link = Link(str.upper, "to_upper")

            # Add link to chain (internal method)
            original_chain = Chain("hello")
            new_chain = original_chain._add_link(upper_link)

            # Original chain is unchanged
            assert original_chain._links == ()
            assert len(new_chain._links) == 1
            ```

        :param link: Link to add to the chain.
        :type link: [Link][chainedpy.link.Link][[_T][chainedpy.chain._T], [_O][chainedpy.chain._O]]
        :return [Chain][chainedpy.chain.Chain][[_O][chainedpy.chain._O]]: New chain with the added link.
        """
        # @@ STEP 1: Create new chain instance. @@
        nxt: Chain[_O] = Chain.__new__(Chain)  # type: ignore[valid-type]

        # @@ STEP 2: Copy seed and add new link. @@
        nxt._seed = self._seed  # type: ignore[assignment]
        nxt._links = self._links + (link,)
        return nxt

    def _replace_last(self, link: Link[_I, _T]) -> "Chain[_T]":  # type: ignore[type-var]
        """Replace the last link in the chain with a new link.

        Note:
            This method is used internally for optimization when the last transformation
            can be replaced rather than adding a new one.

        Example:
            ```python
            from chainedpy import Chain
            from chainedpy.link import Link

            # Create chain with multiple links
            chain = Chain("hello")
            link1 = Link(str.upper, "upper")
            link2 = Link(lambda s: s + "!", "add_exclamation")
            link3 = Link(lambda s: s + "?", "add_question")

            # Build chain and replace last link
            chain_with_links = chain._add_link(link1)._add_link(link2)
            modified_chain = chain_with_links._replace_last(link3)

            # Last link is replaced
            assert len(modified_chain._links) == 2
            assert modified_chain._links[-1].name == "add_question"
            ```

        :param link: New link to replace the last link.
        :type link: [Link][chainedpy.link.Link][[_I][chainedpy.chain._I], [_T][chainedpy.chain._T]]
        :return [Chain][chainedpy.chain.Chain][[_T][chainedpy.chain._T]]: New chain with the replaced link.
        """
        # @@ STEP 1: Create new chain instance. @@
        nxt: Chain[_T] = Chain.__new__(Chain)

        # @@ STEP 2: Copy seed and replace last link. @@
        nxt._seed = self._seed  # type: ignore[assignment]
        nxt._links = self._links[:-1] + (link,)
        return nxt

    # ------ executor -----------------------------------------------------
    async def _run(self) -> _T:
        """Execute the chain by running all links sequentially.

        Note:
            This is the core execution method that processes the entire chain pipeline.
            Each link is executed in sequence, with the output of one becoming the input
            of the next.

        Example:
            ```python
            from chainedpy import Chain

            # Create and execute a chain
            chain = (
                Chain("hello")
                .then_map(str.upper)
                .then_map(lambda s: s + " WORLD")
            )

            # Execute the chain
            result = await chain._run()
            assert result == "HELLO WORLD"

            # Error handling
            try:
                error_chain = (
                    Chain("hello")
                    .then_map(lambda s: 1 / 0)  # Will raise ZeroDivisionError
                )
                await error_chain._run()
            except ChainError as e:
                print(f"Chain execution failed: {e}")
            ```

        :return [_T][chainedpy.chain._T]: Final result after executing all links.
        :raises ChainError: If any link execution fails.
        """
        # @@ STEP 1: Initialize with seed value. @@
        current: object = self._seed

        # @@ STEP 2: Execute each link in sequence. @@
        for idx, lk in enumerate(self._links):
            try:
                current = await lk(current)  # type: ignore[arg-type]
            except Exception as exc:
                raise ChainError(
                    f"Error in link {idx} ({lk.name}): {exc}",
                    context={"link_index": idx, "link_name": lk.name},
                ) from exc

        return current  # type: ignore[return-value]

    def __await__(self):
        """Make Chain awaitable by delegating to _run method.

        Note:
            This method enables Chain instances to be used with the `await` keyword,
            making chain execution feel natural and intuitive.

        Example:
            ```python
            from chainedpy import Chain

            # Chain can be awaited directly
            result = await (
                Chain("hello")
                .then_map(str.upper)
                .then_map(lambda s: s + "!")
            )

            assert result == "HELLO!"

            # Equivalent to calling _run() explicitly
            chain = Chain("test").then_map(str.upper)
            result1 = await chain
            result2 = await chain._run()
            assert result1 == result2 == "TEST"
            ```

        :return: Awaitable object for chain execution.
        """
        # @@ STEP 1: Delegate to _run method's awaitable. @@
        return self._run().__await__()

    def __repr__(self) -> str:
        """Return string representation of the Chain.

        Note:
            The representation includes both the seed value and the names of all
            links in the chain, providing useful debugging information.

        Example:
            ```python
            from chainedpy import Chain

            # Simple chain representation
            chain = Chain("hello")
            print(repr(chain))
            # Output: Chain(seed='hello', links=[])

            # Chain with transformations
            chain_with_links = (
                Chain(42)
                .then_map(str)
                .then_map(str.upper)
            )
            print(repr(chain_with_links))
            # Output: Chain(seed=42, links=[then_map, then_map])
            ```

        :return: String representation showing seed value and link names.
        :return [str][str]: Representation of the chain.
        """
        # @@ STEP 1: Get link names. @@
        names = ", ".join(getattr(l, "name", "?") for l in self._links)

        # @@ STEP 2: Return formatted representation. @@
        return f"Chain(seed={self._seed!r}, links=[{names}])"


# ---------------------------------------------------------------------------
#                 ********  STATIC-TYPING SHIM  ********
# ---------------------------------------------------------------------------
if TYPE_CHECKING:
    # pylint: disable=duplicate-code,missing-class-docstring,function-redefined
    from .link import Processor
    from .plugins.processors import Proc

    class _ChainMethods(Generic[_T], Protocol):
        """Protocol defining the complete Chain method interface for type checking.

        This protocol class defines all the chain methods available on [Chain][chainedpy.chain.Chain] instances
        for static type checking purposes. It provides comprehensive type hints for
        all transformation methods, conditional methods, and processor methods.

        The protocol is used only during type checking and does not affect runtime
        behavior. It ensures that all chain methods have proper type signatures
        and return types for optimal IDE support and static analysis.

        Note:
            This protocol is only active during TYPE_CHECKING and provides
            enhanced type hints without runtime overhead. All method implementations
            are provided by the plugin system at runtime.

        Example:
            ```python
            # This protocol enables proper type checking for:
            from chainedpy import Chain

            # Type checker knows the return type is Chain[str]
            chain: Chain[str] = (
                Chain(42)
                .then_map(str)  # Chain[int] -> Chain[str]
                .then_map(str.upper)  # Chain[str] -> Chain[str]
            )
            ```

        See Also:
            - [Chain][chainedpy.chain.Chain]: The runtime implementation
            - [chainedpy.plugins][chainedpy.plugins]: Plugin method implementations
        """
        def then_map(
            self,
            fn: Callable[[_T], _O | Awaitable[_O]],
        ) -> "Chain[_O]":
            """Transform the chain value using a function.

            Example:
                ```python
                from chainedpy import Chain

                # Transform string to uppercase
                result = await (
                    Chain("hello")
                    .then_map(str.upper)
                )
                assert result == "HELLO"

                # Transform with lambda
                result = await (
                    Chain(5)
                    .then_map(lambda x: x * 2)
                )
                assert result == 10

                # Async transformation
                async def async_transform(x):
                    return x + " world"

                result = await (
                    Chain("hello")
                    .then_map(async_transform)
                )
                assert result == "hello world"
                ```

            :param fn: Function to transform the value.
            :type fn: [Callable][typing.Callable][[[_T][chainedpy.chain._T]], [_O][chainedpy.chain._O] | [Awaitable][typing.Awaitable][[_O][chainedpy.chain._O]]]
            :return [Chain][chainedpy.chain.Chain][[_O][chainedpy.chain._O]]: New chain with transformed value.
            """
            ...

        def then_if(
            self,
            *,
            condition: bool
            | Callable[[_T], bool | Awaitable[bool]],
            then: _O
            | Callable[
                [_T], _O | Awaitable[_O] | "Chain[_O]"
            ],
            otherwise: _O
            | Callable[
                [_T], _O | Awaitable[_O] | "Chain[_O]"
            ],
        ) -> "Chain[_O]":
            """Conditionally execute one of two branches based on a condition.

            Example:
                ```python
                from chainedpy import Chain

                # Simple boolean condition
                result = await (
                    Chain(10)
                    .then_if(
                        condition=True,
                        then=lambda x: x * 2,
                        otherwise=lambda x: x + 1
                    )
                )
                assert result == 20

                # Function-based condition
                result = await (
                    Chain(5)
                    .then_if(
                        condition=lambda x: x > 3,
                        then=lambda x: "big",
                        otherwise=lambda x: "small"
                    )
                )
                assert result == "big"

                # Async condition and branches
                async def async_condition(x):
                    return x % 2 == 0

                async def async_then(x):
                    return f"even: {x}"

                result = await (
                    Chain(4)
                    .then_if(
                        condition=async_condition,
                        then=async_then,
                        otherwise=lambda x: f"odd: {x}"
                    )
                )
                assert result == "even: 4"
                ```

            :param condition: Boolean value or function returning boolean
            :type condition: [bool][bool] | [Callable][typing.Callable][[[_T][chainedpy.chain._T]], [bool][bool] | [Awaitable][typing.Awaitable][[bool][bool]]]
            :param then: Value or function to execute if condition is true
            :type then: [_O][chainedpy.chain._O] | [Callable][typing.Callable][[[_T][chainedpy.chain._T]], [_O][chainedpy.chain._O] | [Awaitable][typing.Awaitable][[_O][chainedpy.chain._O]] | [Chain][chainedpy.chain.Chain][[_O][chainedpy.chain._O]]]
            :param otherwise: Value or function to execute if condition is false
            :type otherwise: [_O][chainedpy.chain._O] | [Callable][typing.Callable][[[_T][chainedpy.chain._T]], [_O][chainedpy.chain._O] | [Awaitable][typing.Awaitable][[_O][chainedpy.chain._O]] | [Chain][chainedpy.chain.Chain][[_O][chainedpy.chain._O]]]
            :return [Chain][chainedpy.chain.Chain][[_O][chainedpy.chain._O]]: New chain with result from the executed branch
            """
            ...

        def then_filter(
            self,
            predicate: Callable[
                [_T], bool | Awaitable[bool]
            ],
        ) -> "Chain[_T]":
            """Filter the chain value based on a predicate function.

            Example:
                ```python
                from chainedpy import Chain
                from chainedpy.exceptions import ValidationError

                # Filter with simple predicate
                result = await (
                    Chain(10)
                    .then_filter(lambda x: x > 5)
                )
                assert result == 10

                # Filter that fails
                try:
                    await (
                        Chain(3)
                        .then_filter(lambda x: x > 5)
                    )
                except ValidationError:
                    print("Filter failed as expected")

                # Async predicate
                async def async_predicate(x):
                    return x % 2 == 0

                result = await (
                    Chain(4)
                    .then_filter(async_predicate)
                )
                assert result == 4
                ```

            :param predicate: Function that returns True to keep the value
            :type predicate: [Callable][typing.Callable][[[_T][chainedpy.chain._T]], [bool][bool] | [Awaitable][typing.Awaitable][[bool][bool]]]
            :return [Chain][chainedpy.chain.Chain][[_T][chainedpy.chain._T]]: Chain with the same value if predicate passes
            :raises ValidationError: If predicate returns False
            """
            ...

        def then_flat_map(
            self,
            fn: Callable[[_T], "Chain[_O]"],
        ) -> "Chain[_O]":
            """Transform the chain value using a function that returns another Chain.

            Example:
                ```python
                from chainedpy import Chain

                # Flat map with chain creation
                result = await (
                    Chain(5)
                    .then_flat_map(lambda x: Chain(x * 2))
                )
                assert result == 10

                # Flat map with complex chain
                def create_processing_chain(value):
                    return (
                        Chain(value)
                        .then_map(str)
                        .then_map(lambda s: s.upper())
                    )

                result = await (
                    Chain(42)
                    .then_flat_map(create_processing_chain)
                )
                assert result == "42"

                # Nested flat mapping
                result = await (
                    Chain([1, 2, 3])
                    .then_flat_map(lambda lst: Chain(sum(lst)))
                    .then_flat_map(lambda total: Chain(f"Total: {total}"))
                )
                assert result == "Total: 6"
                ```

            :param fn: Function that transforms the value into a new Chain
            :type fn: [Callable][typing.Callable][[[_T][chainedpy.chain._T]], [Chain][chainedpy.chain.Chain][[_O][chainedpy.chain._O]]]
            :return [Chain][chainedpy.chain.Chain][[_O][chainedpy.chain._O]]: Flattened chain with the result from the inner chain
            """
            ...

        def then_switch(
            self,
            *,
            key: Callable[[_T], _I],
            cases: dict[
                _I,
                _O
                | Callable[
                    [_T],
                    _O | Awaitable[_O] | "Chain[_O]",
                ],
            ],
            default: _O
            | Callable[
                [_T],
                _O | Awaitable[_O] | "Chain[_O]",
            ]
            | None = None,
        ) -> "Chain[_O]":
            """Execute different branches based on a key function result.

            Example:
                ```python
                from chainedpy import Chain
                from chainedpy.exceptions import ValidationError

                # Switch based on string value
                result = await (
                    Chain("apple")
                    .then_switch(
                        key=lambda x: x[0],  # First letter
                        cases={
                            'a': "fruit",
                            'b': "vegetable",
                            'c': "grain"
                        },
                        default="unknown"
                    )
                )
                assert result == "fruit"

                # Switch with function cases
                result = await (
                    Chain(5)
                    .then_switch(
                        key=lambda x: x % 3,
                        cases={
                            0: lambda x: f"{x} divisible by 3",
                            1: lambda x: f"{x} remainder 1",
                            2: lambda x: f"{x} remainder 2"
                        }
                    )
                )
                assert result == "5 remainder 2"

                # Switch without default (error case)
                try:
                    await (
                        Chain("xyz")
                        .then_switch(
                            key=lambda x: x[0],
                            cases={'a': "vowel", 'e': "vowel"}
                        )
                    )
                except ValidationError:
                    print("No matching case and no default")
                ```

            :param key: Function to extract the switch key from the value
            :type key: [Callable][typing.Callable][[[_T][chainedpy.chain._T]], [_I][chainedpy.chain._I]]
            :param cases: Dictionary mapping keys to values or functions
            :type cases: [dict][dict][[_I][chainedpy.chain._I], [_O][chainedpy.chain._O] | [Callable][typing.Callable][[[_T][chainedpy.chain._T]], [_O][chainedpy.chain._O] | [Awaitable][typing.Awaitable][[_O][chainedpy.chain._O]] | [Chain][chainedpy.chain.Chain][[_O][chainedpy.chain._O]]]]
            :param default: Default value or function if key not found, defaults to None
            :type default: [_O][chainedpy.chain._O] | [Callable][typing.Callable][[[_T][chainedpy.chain._T]], [_O][chainedpy.chain._O] | [Awaitable][typing.Awaitable][[_O][chainedpy.chain._O]] | [Chain][chainedpy.chain.Chain][[_O][chainedpy.chain._O]]] | [None][None], optional
            :return [Chain][chainedpy.chain.Chain][[_O][chainedpy.chain._O]]: New chain with result from the matched case or default
            :raises ValidationError: If key not found and no default provided
            """
            ...

        def then_foreach(
            self: "Chain[Iterable[_E]]",
            *,
            transform: Callable[
                [_E], _V | Awaitable[_V] | "Chain[_V]"
            ],
        ) -> "Chain[list[_V]]":
            """Transform each element in an iterable sequentially.

            Example:
                ```python
                from chainedpy import Chain

                # Transform list of numbers
                result = await (
                    Chain([1, 2, 3, 4])
                    .then_foreach(transform=lambda x: x * 2)
                )
                assert result == [2, 4, 6, 8]

                # Transform with async function
                async def async_transform(x):
                    return f"item_{x}"

                result = await (
                    Chain(["a", "b", "c"])
                    .then_foreach(transform=async_transform)
                )
                assert result == ["item_a", "item_b", "item_c"]

                # Transform with chain creation
                def chain_transform(x):
                    return (
                        Chain(x)
                        .then_map(str.upper)
                        .then_map(lambda s: f"[{s}]")
                    )

                result = await (
                    Chain(["hello", "world"])
                    .then_foreach(transform=chain_transform)
                )
                assert result == ["[HELLO]", "[WORLD]"]
                ```

            :param transform: Function to transform each element
            :type transform: [Callable][typing.Callable][[[_E][chainedpy.chain._E]], [_V][chainedpy.chain._V] | [Awaitable][typing.Awaitable][[_V][chainedpy.chain._V]] | [Chain][chainedpy.chain.Chain][[_V][chainedpy.chain._V]]]
            :return [Chain][chainedpy.chain.Chain][[list][list][[_V][chainedpy.chain._V]]]: Chain containing list of transformed elements
            """
            ...

        def then_parallel_foreach(
            self: "Chain[Iterable[_E]]",
            *,
            transform: Callable[
                [_E], _V | Awaitable[_V] | "Chain[_V]"
            ],
            limit: int | None = None,
        ) -> "Chain[list[_V]]":
            """Transform each element in an iterable in parallel.

            Example:
                ```python
                from chainedpy import Chain
                import asyncio

                # Parallel transformation
                async def slow_transform(x):
                    await asyncio.sleep(0.1)  # Simulate slow operation
                    return x * 2

                result = await (
                    Chain([1, 2, 3, 4, 5])
                    .then_parallel_foreach(transform=slow_transform)
                )
                assert result == [2, 4, 6, 8, 10]

                # With concurrency limit
                result = await (
                    Chain([1, 2, 3, 4, 5, 6, 7, 8])
                    .then_parallel_foreach(
                        transform=slow_transform,
                        limit=3  # Max 3 concurrent operations
                    )
                )
                assert result == [2, 4, 6, 8, 10, 12, 14, 16]

                # Parallel with chain creation
                def chain_transform(x):
                    return (
                        Chain(x)
                        .then_map(lambda n: n ** 2)
                        .then_map(str)
                    )

                result = await (
                    Chain([2, 3, 4])
                    .then_parallel_foreach(transform=chain_transform)
                )
                assert result == ["4", "9", "16"]
                ```

            :param transform: Function to transform each element
            :type transform: [Callable][typing.Callable][[[_E][chainedpy.chain._E]], [_V][chainedpy.chain._V] | [Awaitable][typing.Awaitable][[_V][chainedpy.chain._V]] | [Chain][chainedpy.chain.Chain][[_V][chainedpy.chain._V]]]
            :param limit: Maximum number of concurrent operations, defaults to None
            :type limit: [int][int] | [None][None], optional
            :return [Chain][chainedpy.chain.Chain][[list][list][[_V][chainedpy.chain._V]]]: Chain containing list of transformed elements
            """
            ...

        def then_reduce(
            self: "Chain[Iterable[_E]]",
            *,
            initial: _O,
            accumulator: Callable[
                [_O, _E], _O | Awaitable[_O]
            ],
        ) -> "Chain[_O]":
            """Reduce an iterable to a single value using an accumulator function.

            Example:
                ```python
                from chainedpy import Chain

                # Sum numbers
                result = await (
                    Chain([1, 2, 3, 4, 5])
                    .then_reduce(
                        initial=0,
                        accumulator=lambda acc, x: acc + x
                    )
                )
                assert result == 15

                # Concatenate strings
                result = await (
                    Chain(["hello", " ", "world", "!"])
                    .then_reduce(
                        initial="",
                        accumulator=lambda acc, x: acc + x
                    )
                )
                assert result == "hello world!"

                # Async accumulator
                async def async_accumulator(acc, x):
                    return acc * 10 + x

                result = await (
                    Chain([1, 2, 3])
                    .then_reduce(
                        initial=0,
                        accumulator=async_accumulator
                    )
                )
                assert result == 123

                # Complex reduction
                result = await (
                    Chain([{"value": 10}, {"value": 20}, {"value": 30}])
                    .then_reduce(
                        initial={"total": 0, "count": 0},
                        accumulator=lambda acc, item: {
                            "total": acc["total"] + item["value"],
                            "count": acc["count"] + 1
                        }
                    )
                )
                assert result == {"total": 60, "count": 3}
                ```

            :param initial: Initial value for the reduction
            :type initial: [_O][chainedpy.chain._O]
            :param accumulator: Function to combine accumulator and element
            :type accumulator: [Callable][typing.Callable][[[_O][chainedpy.chain._O], [_E][chainedpy.chain._E]], [_O][chainedpy.chain._O] | [Awaitable][typing.Awaitable][[_O][chainedpy.chain._O]]]
            :return [Chain][chainedpy.chain.Chain][[_O][chainedpy.chain._O]]: Chain containing the reduced value
            """
            ...

        def then_parallel(
            self,
            *chains: "Chain[object]",
        ) -> "Chain[list[object]]":
            """Execute multiple chains in parallel and collect results.

            Example:
                ```python
                from chainedpy import Chain
                import asyncio

                # Execute multiple chains in parallel
                async def slow_operation(x, delay):
                    await asyncio.sleep(delay)
                    return x * 2

                chain1 = Chain(5).then_map(lambda x: slow_operation(x, 0.1))
                chain2 = Chain(10).then_map(lambda x: slow_operation(x, 0.1))
                chain3 = Chain(15).then_map(lambda x: slow_operation(x, 0.1))

                result = await (
                    Chain("start")
                    .then_map(lambda _: 1)
                    .then_parallel(chain1, chain2, chain3)
                )
                assert result == [2, 10, 20, 30]  # First result + parallel results

                # Parallel with different types
                str_chain = Chain("hello").then_map(str.upper)
                num_chain = Chain(42).then_map(lambda x: x * 2)
                bool_chain = Chain(True).then_map(lambda x: not x)

                result = await (
                    Chain([1, 2, 3])
                    .then_map(len)
                    .then_parallel(str_chain, num_chain, bool_chain)
                )
                assert result == [3, "HELLO", 84, False]
                ```

            :param chains: Additional chains to execute in parallel
            :type chains: [Chain][chainedpy.chain.Chain][[object][object]]
            :return [Chain][chainedpy.chain.Chain][[list][list][[object][object]]]: Chain containing list of all results
            """
            ...

        def as_retry(
            self, *, attempts: int = 3, delay: float = 1.0
        ) -> "Chain[_T]":
            """Add retry behavior to the chain.

            Example:
                ```python
                from chainedpy import Chain
                from chainedpy.exceptions import RetryExhausted
                import random

                # Retry a flaky operation
                def flaky_operation(x):
                    if random.random() < 0.7:  # 70% chance of failure
                        raise ValueError("Random failure")
                    return x * 2

                try:
                    result = await (
                        Chain(5)
                        .then_map(flaky_operation)
                        .as_retry(attempts=5, delay=0.1)
                    )
                    print(f"Success: {result}")
                except RetryExhausted as e:
                    print(f"All retries failed: {e}")

                # Retry with exponential backoff
                result = await (
                    Chain("https://api.example.com/data")
                    .then_map(lambda url: fetch_data(url))  # Might fail
                    .as_retry(attempts=3, delay=2.0)
                )
                ```

            :param attempts: Number of retry attempts, defaults to 3
            :type attempts: [int][int], optional
            :param delay: Delay between retries in seconds, defaults to 1.0
            :type delay: [float][float], optional
            :return [Chain][chainedpy.chain.Chain][[_T][chainedpy.chain._T]]: Chain with retry behavior applied
            """
            ...

        def as_timeout(self, seconds: float) -> "Chain[_T]":
            """Add timeout behavior to the chain.

            Example:
                ```python
                from chainedpy import Chain
                from chainedpy.exceptions import TimeoutExpired
                import asyncio

                # Timeout a slow operation
                async def slow_operation(x):
                    await asyncio.sleep(2.0)  # Takes 2 seconds
                    return x * 2

                try:
                    result = await (
                        Chain(5)
                        .then_map(slow_operation)
                        .as_timeout(1.0)  # Timeout after 1 second
                    )
                except TimeoutExpired as e:
                    print(f"Operation timed out: {e}")

                # Successful timeout (operation completes in time)
                async def fast_operation(x):
                    await asyncio.sleep(0.1)  # Takes 0.1 seconds
                    return x * 3

                result = await (
                    Chain(10)
                    .then_map(fast_operation)
                    .as_timeout(1.0)  # Plenty of time
                )
                assert result == 30
                ```

            :param seconds: Timeout duration in seconds
            :type seconds: [float][float]
            :return [Chain][chainedpy.chain.Chain][[_T][chainedpy.chain._T]]: Chain with timeout behavior applied
            :raises TimeoutExpired: If execution exceeds timeout
            """
            ...

        def as_log(
            self, label: str = "", *, level: int = 20
        ) -> "Chain[_T]":
            """Add logging behavior to the chain.

            :param label: Label for log messages, defaults to ""
            :type label: str, optional
            :param level: Logging level, defaults to 20 (INFO)
            :type level: int, optional
            :return Chain[_T]: Chain with logging behavior applied
            """
            ...

        def as_cache(self, *, ttl: float = 60.0) -> "Chain[_T]":
            """Add caching behavior to the chain.

            Example:
                ```python
                from chainedpy import Chain
                import time

                # Cache expensive computation
                def expensive_computation(x):
                    time.sleep(1)  # Simulate expensive operation
                    return x * x

                # First call takes time, subsequent calls are cached
                result1 = await (
                    Chain(5)
                    .then_map(expensive_computation)
                    .as_cache(ttl=30.0)  # Cache for 30 seconds
                )

                # This should be much faster (cached)
                result2 = await (
                    Chain(5)
                    .then_map(expensive_computation)
                    .as_cache(ttl=30.0)
                )

                assert result1 == result2 == 25

                # Cache with short TTL
                result = await (
                    Chain("hello")
                    .then_map(str.upper)
                    .as_cache(ttl=1.0)  # Cache for 1 second
                )
                assert result == "HELLO"
                ```

            :param ttl: Time-to-live for cache entries in seconds, defaults to 60.0
            :type ttl: [float][float], optional
            :return [Chain][chainedpy.chain.Chain][[_T][chainedpy.chain._T]]: Chain with caching behavior applied
            """
            ...

        def as_on_error(
            self,
            handler: Callable[[Exception], _T | Awaitable[_T]],
        ) -> "Chain[_T]":
            """Add error handling behavior to the chain.

            Example:
                ```python
                from chainedpy import Chain

                # Handle errors with fallback value
                def error_handler(error):
                    print(f"Error occurred: {error}")
                    return "fallback_value"

                result = await (
                    Chain("input")
                    .then_map(lambda x: 1 / 0)  # Will raise ZeroDivisionError
                    .as_on_error(error_handler)
                )
                assert result == "fallback_value"

                # Handle errors with async handler
                async def async_error_handler(error):
                    return f"Handled: {type(error).__name__}"

                result = await (
                    Chain(42)
                    .then_map(lambda x: x.invalid_method())  # AttributeError
                    .as_on_error(async_error_handler)
                )
                assert result == "Handled: AttributeError"

                # No error case
                result = await (
                    Chain(10)
                    .then_map(lambda x: x * 2)
                    .as_on_error(error_handler)
                )
                assert result == 20
                ```

            :param handler: Function to handle exceptions
            :type handler: [Callable][typing.Callable][[Exception], [_T][chainedpy.chain._T] | [Awaitable][typing.Awaitable][[_T][chainedpy.chain._T]]]
            :return [Chain][chainedpy.chain.Chain][[_T][chainedpy.chain._T]]: Chain with error handling behavior applied
            """
            ...

        # -------------------- processors (built-ins overloads) --------
        @overload
        def then_process(
            self: "Chain[_T]",
            proc: Literal[
                Proc.STRIP,
                Proc.UPPER,
                Proc.LOWER,
                Proc.B64_ENCODE,
                Proc.JSON_DUMPS,
            ],
            *,
            param: str | None = None,
        ) -> "Chain[str]":
            """Process the chain value using string-returning built-in processors.

            Example:
                ```python
                from chainedpy import Chain
                from chainedpy.plugins.processors import Proc

                # String processing
                result = await (
                    Chain("  Hello World  ")
                    .then_process(Proc.STRIP)
                )
                assert result == "Hello World"

                result = await (
                    Chain("hello")
                    .then_process(Proc.UPPER)
                )
                assert result == "HELLO"

                # Base64 encoding
                result = await (
                    Chain("hello world")
                    .then_process(Proc.B64_ENCODE)
                )
                assert isinstance(result, str)

                # JSON dumps
                result = await (
                    Chain({"name": "John", "age": 30})
                    .then_process(Proc.JSON_DUMPS)
                )
                assert '"name": "John"' in result
                ```

            :param proc: Built-in processor that returns string
            :type proc: [Literal][typing.Literal][[Proc.STRIP][chainedpy.plugins.processors.Proc.STRIP], [Proc.UPPER][chainedpy.plugins.processors.Proc.UPPER], [Proc.LOWER][chainedpy.plugins.processors.Proc.LOWER], [Proc.B64_ENCODE][chainedpy.plugins.processors.Proc.B64_ENCODE], [Proc.JSON_DUMPS][chainedpy.plugins.processors.Proc.JSON_DUMPS]]
            :param param: Optional parameter for the processor, defaults to None
            :type param: [str][str] | [None][None], optional
            :return [Chain][chainedpy.chain.Chain][[str][str]]: Chain containing processed string value
            """
            ...

        @overload
        def then_process(
            self: "Chain[_T]",
            proc: Literal[Proc.B64_DECODE],
            *,
            param: str | None = None,
        ) -> "Chain[bytes]":
            """Process the chain value using base64 decode processor.

            Example:
                ```python
                from chainedpy import Chain
                from chainedpy.plugins.processors import Proc
                import base64

                # Base64 decode
                encoded_data = base64.b64encode(b"hello world").decode()
                result = await (
                    Chain(encoded_data)
                    .then_process(Proc.B64_DECODE)
                )
                assert result == b"hello world"

                # Chain with encoding then decoding
                original = "test data"
                result = await (
                    Chain(original)
                    .then_process(Proc.B64_ENCODE)
                    .then_process(Proc.B64_DECODE)
                    .then_map(lambda b: b.decode())
                )
                assert result == original
                ```
            
            :param proc: Base64 decode processor
            :type proc: [Literal][typing.Literal][[Proc.B64_DECODE][chainedpy.plugins.processors.Proc.B64_DECODE]]
            :param param: Optional parameter for the processor, defaults to None
            :type param: [str][str] | [None][None], optional
            :return [Chain][chainedpy.chain.Chain][[bytes][bytes]]: Chain containing decoded bytes value

            """
            ...

        @overload
        def then_process(
            self: "Chain[_T]",
            proc: Literal[Proc.TO_INT],
            *,
            param: str | None = None,
        ) -> "Chain[int]":
            """Process the chain value using integer conversion processor.

            :param proc: Integer conversion processor
            :type proc: Literal[Proc.TO_INT]
            :param param: Optional parameter for the processor, defaults to None
            :type param: str | None, optional
            :return Chain[int]: Chain containing integer value
            """
            ...

        @overload
        def then_process(
            self: "Chain[_T]",
            proc: Literal[Proc.TO_FLOAT],
            *,
            param: str | None = None,
        ) -> "Chain[float]":
            """Process the chain value using float conversion processor.

            :param proc: Float conversion processor
            :type proc: Literal[Proc.TO_FLOAT]
            :param param: Optional parameter for the processor, defaults to None
            :type param: str | None, optional
            :return Chain[float]: Chain containing float value
            """
            ...

        @overload
        def then_process(
            self: "Chain[_T]",
            proc: Literal[Proc.JSON_LOADS],
            *,
            param: str | None = None,
        ) -> "Chain[object]":
            """Process the chain value using JSON loads processor.

            :param proc: JSON loads processor
            :type proc: Literal[Proc.JSON_LOADS]
            :param param: Optional parameter for the processor, defaults to None
            :type param: str | None, optional
            :return Chain[object]: Chain containing parsed JSON object
            """
            ...

        @overload
        def then_process(
            self: "Chain[_T]",
            proc: Literal[Proc.REGEX_EXTRACT],
            *,
            param: str | None = None,
        ) -> "Chain[str | None]":
            r"""Process the chain value using regex extract processor.

            Example:
                ```python
                from chainedpy import Chain
                from chainedpy.plugins.processors import Proc

                # Extract email from text
                result = await (
                    Chain("Contact us at support@example.com for help")
                    .then_process(Proc.REGEX_EXTRACT, param=r"[\w\.-]+@[\w\.-]+\.\w+")
                )
                assert result == "support@example.com"

                # Extract first number
                result = await (
                    Chain("The price is $29.99 and tax is $2.50")
                    .then_process(Proc.REGEX_EXTRACT, param=r"\d+\.\d+")
                )
                assert result == "29.99"

                # No match returns None
                result = await (
                    Chain("No numbers here")
                    .then_process(Proc.REGEX_EXTRACT, param=r"\d+")
                )
                assert result is None
                ```

            :param proc: Regex extract processor
            :type proc: [Literal][typing.Literal][[Proc.REGEX_EXTRACT][chainedpy.plugins.processors.Proc.REGEX_EXTRACT]]
            :param param: Optional parameter for the processor, defaults to None
            :type param: [str][str] | [None][None], optional
            :return [Chain][chainedpy.chain.Chain][[str][str] | [None][None]]: Chain containing extracted string or None
            """
            ...

        @overload
        def then_process(
            self: "Chain[_T]",
            proc: Literal[Proc.REGEX_MATCH],
            *,
            param: str | None = None,
        ) -> "Chain[bool]":
            r"""Process the chain value using regex match processor.

            Example:
                ```python
                from chainedpy import Chain
                from chainedpy.plugins.processors import Proc

                # Check if email exists
                result = await (
                    Chain("Contact us at support@example.com")
                    .then_process(Proc.REGEX_MATCH, param=r"[\w\.-]+@[\w\.-]+\.\w+")
                )
                assert result == True

                # Check if string contains numbers
                result = await (
                    Chain("The price is $29.99")
                    .then_process(Proc.REGEX_MATCH, param=r"\d+")
                )
                assert result == True

                # No match returns False
                result = await (
                    Chain("No numbers here")
                    .then_process(Proc.REGEX_MATCH, param=r"\d+")
                )
                assert result == False

                # Phone number validation
                result = await (
                    Chain("Call me at (555) 123-4567")
                    .then_process(Proc.REGEX_MATCH, param=r"\(\d{3}\) \d{3}-\d{4}")
                )
                assert result == True
                ```

            :param proc: Regex match processor
            :type proc: [Literal][typing.Literal][[Proc.REGEX_MATCH][chainedpy.plugins.processors.Proc.REGEX_MATCH]]
            :param param: Optional parameter for the processor, defaults to None
            :type param: [str][str] | [None][None], optional
            :return [Chain][chainedpy.chain.Chain][[bool][bool]]: Chain containing boolean match result
            """
            ...

        # fallback - custom or future processors
        def then_process(
            self: "Chain[_T]",
            proc: Processor[_T, _O],
            *,
            param: str | None = None,
        ) -> "Chain[_O]":
            """Process the chain value using a custom processor.

            Example:
                ```python
                from chainedpy import Chain
                from chainedpy.link import Processor

                # Create custom processor
                class DoubleProcessor(Processor[int, int]):
                    def apply(self, value: int, *, param: str | None = None) -> int:
                        multiplier = int(param) if param else 2
                        return value * multiplier

                # Use custom processor
                result = await (
                    Chain(5)
                    .then_process(DoubleProcessor())
                )
                assert result == 10

                # Use with parameter
                result = await (
                    Chain(3)
                    .then_process(DoubleProcessor(), param="4")
                )
                assert result == 12

                # String processor
                class PrefixProcessor(Processor[str, str]):
                    def apply(self, value: str, *, param: str | None = None) -> str:
                        prefix = param or "PREFIX"
                        return f"{prefix}: {value}"

                result = await (
                    Chain("hello")
                    .then_process(PrefixProcessor(), param="CUSTOM")
                )
                assert result == "CUSTOM: hello"
                ```

            :param proc: Custom processor instance
            :type proc: [Processor][chainedpy.link.Processor][[_T][chainedpy.typing._T], [_O][chainedpy.typing._O]]
            :param param: Optional parameter for the processor, defaults to None
            :type param: [str][str] | [None][None], optional
            :return [Chain][chainedpy.chain.Chain][[_O][chainedpy.typing._O]]: Chain containing processed value
            """
            ...


    class Chain(_ChainMethods[_T], Generic[_T]):  # shadow class for type hints
        """Shadow Chain class for enhanced type checking.

        This shadow class combines the runtime Chain implementation with the
        _ChainMethods protocol to provide complete type hints during static
        analysis. It exists only during TYPE_CHECKING and does not affect
        runtime behavior.

        Note:
           This is a shadow class used only for type checking purposes.
           The actual runtime implementation is defined above.
        """

        def __init__(self, value: _T | None = None, **kw):
            """Initialize the Chain with a value or kwargs.

            :param value: Initial value for the chain, defaults to None
            :type value: _T | None, optional
            :param kw: Keyword arguments as initial value
            :type kw: Any
            """
            ...

        def __await__(self) -> Awaitable[_T]:
            """Make Chain awaitable for async execution.

            :return Awaitable[_T]: Awaitable object for chain execution
            """
            ...
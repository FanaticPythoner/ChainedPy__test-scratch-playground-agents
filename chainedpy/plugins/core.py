"""Core transformation operations for ChainedPy.

This module implements the fundamental then_* methods with proper auto-chaining support.
It provides essential transformation operations like [then_map][chainedpy.plugins.core.then_map], [then_filter][chainedpy.plugins.core.then_filter],
[then_flat_map][chainedpy.plugins.core.then_flat_map], and conditional operations that form the core of the ChainedPy
transformation pipeline.

All methods in this module are registered using the [then][chainedpy.register.then] decorator, making them
automatically available on [Chain][chainedpy.chain.Chain] instances when this module is imported. The implementations
support both synchronous and asynchronous transformations seamlessly.

Note:
    This module is automatically imported by the main ChainedPy package, so all
    methods defined here are immediately available on Chain instances without
    explicit imports.

Example:
    ```python
    from chainedpy import Chain

    # Core transformation methods are automatically available
    result = await (
        Chain([1, 2, 3, 4, 5])
        .then_map(lambda x: x * 2)        # Transform each element
        .then_filter(lambda x: x > 5)     # Filter elements
        .then_flat_map(lambda x: [x, x])  # Flatten and duplicate
    )

    # Conditional transformations
    result = await (
        Chain(10)
        .then_if(
            lambda x: x > 5,
            lambda x: x * 2,    # if true
            lambda x: x + 1     # if false
        )
    )
    ```

See Also:
    - [then_map][chainedpy.plugins.core.then_map]: Transform values with a function
    - [then_filter][chainedpy.plugins.core.then_filter]: Filter values with a predicate
    - [then_if][chainedpy.plugins.core.then_if]: Conditional transformation
    - [chainedpy.register.then][chainedpy.register.then]: Registration decorator used by this module
"""
from __future__ import annotations

import asyncio
from typing import Awaitable, Callable, Iterable, TypeVar

from ..register import then # pylint: disable=relative-beyond-top-level
from ..link import Link, maybe_await  # pylint: disable=relative-beyond-top-level
from ..exceptions import ValidationError, ChainError # pylint: disable=relative-beyond-top-level
from ..chain import Chain # pylint: disable=relative-beyond-top-level

# @@ STEP 1: Define type variables. @@
_T = TypeVar("_T")
_O = TypeVar("_O")
_E = TypeVar("_E")
_V = TypeVar("_V")
_I = TypeVar("_I")


# @@ STEP 2: Define core transformation operations. @@
@then("map")
def then_map(fn: Callable[[_T], _O | Awaitable[_O]]) -> Link[_T, _O]:
    """Transform the stream value using a function.

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

        # Chain multiple transformations
        result = await (
            Chain(3)
            .then_map(lambda x: x * 2)
            .then_map(str)
            .then_map(lambda s: f"Result: {s}")
        )
        assert result == "Result: 6"
        ```

    :param fn: Function to transform the value.
    :type fn: [Callable][typing.Callable][[[_T][chainedpy.typing._T]], [_O][chainedpy.typing._O] | [Awaitable][typing.Awaitable][[_O][chainedpy.typing._O]]]
    :return [Link][chainedpy.link.Link][[_T][chainedpy.typing._T], [_O][chainedpy.typing._O]]: Link that applies the transformation.
    """
    class MapLink(Link[_T, _O]):
        """Link implementation for map transformation."""
        name = "map"

        async def __call__(self, arg: _T) -> _O:
            """Apply the map transformation.

            Example:
                ```python
                # This method is called internally by the chain
                link = MapLink()
                result = await link("hello")
                # Result depends on the fn provided to then_map
                ```

            :param arg: Input value to transform.
            :type arg: [_T][chainedpy.typing._T]
            :return [_O][chainedpy.typing._O]: Transformed value.
            """
            # Apply function and await if necessary.
            result = fn(arg)
            return await maybe_await(result)

    return MapLink()


@then("flat_map")
def then_flat_map(fn: Callable[[_T], "Chain[_O]"]) -> Link[_T, _O]:
    """Transform and flatten using a function that returns a Chain.

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

    :param fn: Function that transforms value to a Chain.
    :type fn: [Callable][typing.Callable][[[_T][chainedpy.typing._T]], [Chain][chainedpy.chain.Chain][[_O][chainedpy.typing._O]]]
    :return [Link][chainedpy.link.Link][[_T][chainedpy.typing._T], [_O][chainedpy.typing._O]]: Link that applies the flat map transformation.
    """
    class FlatMapLink(Link[_T, _O]):
        """Link implementation for flat map transformation."""
        name = "flat_map"

        async def __call__(self, arg: _T) -> _O:
            """Apply the flat map transformation.

            Example:
                ```python
                # This method is called internally by the chain
                link = FlatMapLink()
                result = await link(5)
                # Result depends on the fn provided to then_flat_map
                ```

            :param arg: Input value to transform.
            :type arg: [_T][chainedpy.typing._T]
            :return [_O][chainedpy.typing._O]: Flattened result from the Chain.
            :raises ValidationError: If function doesn't return a Chain.
            """
            # Apply function and validate result is a Chain.
            result = fn(arg)
            if not isinstance(result, Chain):
                raise ValidationError("then_flat_map function must return a Chain")
            return await result

    return FlatMapLink()


@then("filter")
def then_filter(predicate: Callable[[_T], bool | Awaitable[bool]]) -> Link[_T, _T]:
    """Filter the stream value using a predicate.

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

        # String filtering
        result = await (
            Chain("hello")
            .then_filter(lambda s: len(s) > 3)
        )
        assert result == "hello"
        ```

    :param predicate: Function to test the value.
    :type predicate: [Callable][typing.Callable][[[_T][chainedpy.typing._T]], [bool][bool] | [Awaitable][typing.Awaitable][[bool][bool]]]
    :return [Link][chainedpy.link.Link][[_T][chainedpy.typing._T], [_T][chainedpy.typing._T]]: Link that applies the filter.
    """
    class FilterLink(Link[_T, _T]):
        """Link implementation for filter transformation."""
        name = "filter"

        async def __call__(self, arg: _T) -> _T:
            """Apply the filter predicate.

            Example:
                ```python
                # This method is called internally by the chain
                link = FilterLink()
                result = await link(10)
                # Result depends on the predicate provided to then_filter
                ```

            :param arg: Input value to test.
            :type arg: [_T][chainedpy.typing._T]
            :return [_T][chainedpy.typing._T]: The original value if predicate passes.
            :raises ChainError: If predicate fails.
            """
            # Apply predicate and check result.
            result = await maybe_await(predicate(arg))  # Pass raw value directly.
            if not result:
                raise ChainError("Value filtered out by predicate")
            return arg

    return FilterLink()


@then("if")
def then_if(
    *,
    condition: bool | Callable[[_T], bool | Awaitable[bool]],
    then: _O | Callable[[_T], _O | Awaitable[_O] | "Chain[_O]"],
    otherwise: _O | Callable[[_T], _O | Awaitable[_O] | "Chain[_O]"],
) -> Link[_T, _O]:
    """Conditional transformation.

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

    :param condition: Boolean value or function that evaluates to boolean.
    :type condition: [bool][bool] | [Callable][typing.Callable][[[_T][chainedpy.typing._T]], [bool][bool] | [Awaitable][typing.Awaitable][[bool][bool]]]
    :param then: Value or function to use if condition is true.
    :type then: [_O][chainedpy.typing._O] | [Callable][typing.Callable][[[_T][chainedpy.typing._T]], [_O][chainedpy.typing._O] | [Awaitable][typing.Awaitable][[_O][chainedpy.typing._O]] | [Chain][chainedpy.chain.Chain][[_O][chainedpy.typing._O]]]
    :param otherwise: Value or function to use if condition is false.
    :type otherwise: [_O][chainedpy.typing._O] | [Callable][typing.Callable][[[_T][chainedpy.typing._T]], [_O][chainedpy.typing._O] | [Awaitable][typing.Awaitable][[_O][chainedpy.typing._O]] | [Chain][chainedpy.chain.Chain][[_O][chainedpy.typing._O]]]
    :return [Link][chainedpy.link.Link][[_T][chainedpy.typing._T], [_O][chainedpy.typing._O]]: Link that applies conditional logic.
    """
    class IfLink(Link[_T, _O]):
        """Link implementation for conditional transformation."""
        name = "if"

        async def __call__(self, arg: _T) -> _O:
            """Apply conditional transformation.

            :param arg: Input value to process.
            :type arg: _T
            :return [_O][chainedpy.typing._O]: Result from chosen branch.
            """
            # @@ STEP 1: Evaluate condition. @@
            if callable(condition):
                cond_result = await maybe_await(condition(arg))
            else:
                cond_result = condition

            # @@ STEP 2: Choose branch based on condition. @@
            branch = then if cond_result else otherwise

            # @@ STEP 3: Execute chosen branch. @@
            if callable(branch):
                result = branch(arg)
                if isinstance(result, Chain):
                    return await result
                return await maybe_await(result)
            else:
                return branch

    return IfLink()


@then("switch")
def then_switch(
    *,
    key: Callable[[_T], _I],
    cases: dict[_I, _O | Callable[[_T], _O | Awaitable[_O] | "Chain[_O]"]],
    default: _O | Callable[[_T], _O | Awaitable[_O] | "Chain[_O]"] | None = None,
) -> Link[_T, _O]:
    """Switch-case transformation.

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

    :param key: Function to extract key from input value.
    :type key: [Callable][typing.Callable][[[_T][chainedpy.typing._T]], [_I][chainedpy.typing._I]]
    :param cases: Dictionary mapping keys to values or functions.
    :type cases: [dict][dict][[_I][chainedpy.typing._I], [_O][chainedpy.typing._O] | [Callable][typing.Callable][[[_T][chainedpy.typing._T]], [_O][chainedpy.typing._O] | [Awaitable][typing.Awaitable][[_O][chainedpy.typing._O]] | [Chain][chainedpy.chain.Chain][[_O][chainedpy.typing._O]]]]
    :param default: Default value or function if no case matches, defaults to None.
    :type default: [_O][chainedpy.typing._O] | [Callable][typing.Callable][[[_T][chainedpy.typing._T]], [_O][chainedpy.typing._O] | [Awaitable][typing.Awaitable][[_O][chainedpy.typing._O]] | [Chain][chainedpy.chain.Chain][[_O][chainedpy.typing._O]]] | [None][None], optional
    :return [Link][chainedpy.link.Link][[_T][chainedpy.typing._T], [_O][chainedpy.typing._O]]: Link that applies switch-case logic.
    """
    class SwitchLink(Link[_T, _O]):
        """Link implementation for switch-case transformation."""
        name = "switch"

        async def __call__(self, arg: _T) -> _O:
            """Apply switch-case transformation.

            Example:
                ```python
                # This method is called internally by the chain
                link = SwitchLink()
                result = await link("apple")
                # Result depends on the cases and key function provided to then_switch
                ```

            :param arg: Input value to process.
            :type arg: [_T][chainedpy.typing._T]
            :return [_O][chainedpy.typing._O]: Result from matching case or default.
            :raises ChainError: If no case matches and no default provided.
            """
            # Extract key from input value.
            key_result = key(arg)

            # @@ STEP 1: Find matching case. @@
            if key_result in cases:
                branch = cases[key_result]
            elif default is not None:
                branch = default
            else:
                raise ChainError(f"No case found for key '{key_result}' and no default provided")

            # @@ STEP 2: Execute chosen branch. @@
            if callable(branch):
                result = branch(arg)
                if isinstance(result, Chain):
                    return await result
                return await maybe_await(result)
            else:
                return branch

    return SwitchLink()


@then("foreach")
def then_foreach(
    *,
    transform: Callable[[_E], _V | Awaitable[_V] | "Chain[_V]"],  # _E will be passed as raw value
) -> Link[Iterable[_E], list[_V]]:
    """Transform each element in an iterable sequentially.

    :param transform: Function to transform each element.
    :type transform: Callable[[_E], _V | Awaitable[_V] | "Chain[_V]"]
    :return Link[Iterable[_E], list[_V]]: Link that processes each element sequentially.
    """
    class ForeachLink(Link[Iterable[_E], list[_V]]):
        """Link implementation for sequential foreach transformation."""
        name = "foreach"

        async def __call__(self, arg: Iterable[_E]) -> list[_V]:
            """Process each element sequentially.

            :param arg: Iterable to process.
            :type arg: Iterable[_E]
            :return list[_V]: List of transformed results.
            :raises ValidationError: If input is not iterable.
            """
            # @@ STEP 1: Validate input is iterable. @@
            try:
                iter(arg)
            except TypeError as e:
                raise ValidationError(f"foreach requires iterable input, got {type(arg).__name__}") from e

            # @@ STEP 2: Process each item sequentially. @@
            results = []
            for item in arg:
                result = transform(item)

                if isinstance(result, Chain):
                    results.append(await result)
                else:
                    results.append(await maybe_await(result))

            return results

    return ForeachLink()


@then("parallel_foreach")
def then_parallel_foreach(
    *,
    transform: Callable[[_E], _V | Awaitable[_V] | "Chain[_V]"],  # _E will be passed as raw value
    limit: int | None = None,
) -> Link[Iterable[_E], list[_V]]:
    """Transform each element in an iterable in parallel.

    Example:
        ```python
        from chainedpy import Chain
        import asyncio

        # Parallel processing of numbers
        async def square(x):
            await asyncio.sleep(0.1)  # Simulate async work
            return x * x

        result = await (
            Chain([1, 2, 3, 4, 5])
            .then_parallel_foreach(transform=square)
        )
        assert result == [1, 4, 9, 16, 25]

        # With concurrency limit
        result = await (
            Chain([1, 2, 3, 4, 5])
            .then_parallel_foreach(transform=square, limit=2)
        )
        assert result == [1, 4, 9, 16, 25]

        # Sync transformation
        result = await (
            Chain(["a", "b", "c"])
            .then_parallel_foreach(transform=str.upper)
        )
        assert result == ["A", "B", "C"]
        ```

    :param transform: Function to transform each element.
    :type transform: [Callable][typing.Callable][[[_E][chainedpy.typing._E]], [_V][chainedpy.typing._V] | [Awaitable][typing.Awaitable][[_V][chainedpy.typing._V]] | [Chain][chainedpy.chain.Chain][[_V][chainedpy.typing._V]]]
    :param limit: Maximum number of concurrent operations, defaults to None.
    :type limit: [int][int] | [None][None], optional
    :return [Link][chainedpy.link.Link][[Iterable][typing.Iterable][[_E][chainedpy.typing._E]], [list][list][[_V][chainedpy.typing._V]]]: Link that processes each element in parallel.
    """
    class ParallelForeachLink(Link[Iterable[_E], list[_V]]):
        """Link implementation for parallel foreach transformation."""
        name = "parallel_foreach"

        async def __call__(self, arg: Iterable[_E]) -> list[_V]:
            """Process each element in parallel.

            :param arg: Iterable to process.
            :type arg: Iterable[_E]
            :return list[_V]: List of transformed results.
            """
            async def process_item(item: _E) -> _V:
                """Process a single item.

                :param item: Item to process.
                :type item: _E
                :return _V: Transformed result.
                """
                result = transform(item)

                if isinstance(result, Chain):
                    return await result
                else:
                    return await maybe_await(result)

            # @@ STEP 1: Create tasks for all items. @@
            tasks = [process_item(item) for item in arg]

            # @@ STEP 2: Execute with or without concurrency limit. @@
            if limit is None:
                # No limit - run all in parallel.
                return await asyncio.gather(*tasks)
            else:
                # Limited concurrency.
                semaphore = asyncio.Semaphore(limit)

                async def limited_process(task):
                    """Process task with semaphore limit.

                    Example:
                        ```python
                        # This is an internal helper function
                        # Used to limit concurrent operations
                        ```

                    :param task: Task to process.
                    :type task: [Any][typing.Any]
                    :return [Any][typing.Any]: Task result.
                    """
                    async with semaphore:
                        return await task

                limited_tasks = [limited_process(task) for task in tasks]
                return await asyncio.gather(*limited_tasks)

    return ParallelForeachLink()


@then("reduce")
def then_reduce(
    *,
    initial: _O,
    accumulator: Callable[[_O, _E], _O | Awaitable[_O]],
) -> Link[Iterable[_E], _O]:
    """Reduce an iterable to a single value.

    Example:
        ```python
        from chainedpy import Chain

        # Sum numbers
        result = await (
            Chain([1, 2, 3, 4, 5])
            .then_reduce(initial=0, accumulator=lambda acc, x: acc + x)
        )
        assert result == 15

        # Concatenate strings
        result = await (
            Chain(["hello", " ", "world"])
            .then_reduce(initial="", accumulator=lambda acc, x: acc + x)
        )
        assert result == "hello world"

        # Find maximum
        result = await (
            Chain([3, 1, 4, 1, 5, 9])
            .then_reduce(initial=0, accumulator=lambda acc, x: max(acc, x))
        )
        assert result == 9

        # Async accumulator
        async def async_sum(acc, x):
            return acc + x

        result = await (
            Chain([1, 2, 3])
            .then_reduce(initial=0, accumulator=async_sum)
        )
        assert result == 6
        ```

    :param initial: Initial value for the reduction.
    :type initial: [_O][chainedpy.typing._O]
    :param accumulator: Function to combine accumulator and current item.
    :type accumulator: [Callable][typing.Callable][[[_O][chainedpy.typing._O], [_E][chainedpy.typing._E]], [_O][chainedpy.typing._O] | [Awaitable][typing.Awaitable][[_O][chainedpy.typing._O]]]
    :return [Link][chainedpy.link.Link][[Iterable][typing.Iterable][[_E][chainedpy.typing._E]], [_O][chainedpy.typing._O]]: Link that reduces the iterable.
    """
    class ReduceLink(Link[Iterable[_E], _O]):
        """Link implementation for reduce transformation."""
        name = "reduce"

        async def __call__(self, arg: Iterable[_E]) -> _O:
            """Reduce the iterable to a single value.

            :param arg: Iterable to reduce.
            :type arg: Iterable[_E]
            :return [_O][chainedpy.typing._O]: Reduced result.
            """
            # @@ STEP 1: Initialize result with initial value. @@
            result = initial

            # @@ STEP 2: Apply accumulator to each item. @@
            for item in arg:
                result = await maybe_await(accumulator(result, item))  # Pass raw values directly.
            return result

    return ReduceLink()


@then("parallel")
def then_parallel(*chains: "Chain[object]") -> Link[_T, list[object]]:
    """Execute multiple chains in parallel.

    :param chains: Chains to execute in parallel.
    :type chains: "Chain[object]"
    :return Link[_T, list[object]]: Link that executes chains in parallel.
    """
    class ParallelLink(Link[_T, list[object]]):
        """Link implementation for parallel execution."""
        name = "parallel"

        async def __call__(self, arg: _T) -> list[object]:
            """Execute all chains in parallel.

            :param arg: Input value (unused in parallel execution).
            :type arg: _T
            :return list[object]: List of results from all chains.
            """
            # Execute all chains in parallel.
            tasks = [chain for chain in chains]
            return await asyncio.gather(*tasks)

    return ParallelLink()
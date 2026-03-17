#!/usr/bin/env python3
"""
ChainedPy Example: Using Remote Chain with then_print Method

This example demonstrates how to use a ChainedPy project that extends
a remote base chain (myprivatechain1) and call its then_print method.

The project 'your_project_name' extends myprivatechain1 which provides
the then_print method for printing chain data.
"""

import asyncio
import sys
from pathlib import Path

from chainedpy.plugins.processors import Proc

# Add the PROJECTS directory to Python path so we can import our project
projects_dir = Path(__file__).parent.parent / "PROJECTS"
sys.path.insert(0, str(projects_dir))

# Import the Chain from our project (which extends myprivatechain1)
from PROJECTS.your_project_name4.your_project_name4_chain import Chain


async def basic_then_print_example():
    """Basic example of using then_print method from myprivatechain1.

    :return None: None
    """
    # @@ STEP 1: Print example header. @@
    print("🔗 Basic then_print Example")
    print("=" * 40)

    # @@ STEP 2: Create a chain with some data and execute operations. @@
    result = await (
        Chain([1, 2, 3, 4, 5])
        # (method) def then_print(transform_fn: (list[int]) -> (_O@then_print | Awaitable[_O@then_print])) -> Chain[_O@then_print]
        .then_print( # Instance of 'Chain' has no 'then_print' memberPylintE1101:no-member <<<< THIS IS WRONG. IT IS PRESENT. IT EVEN HAVE THE TYPE HINTS FOR THE "DATA" PARAMETER.
            lambda data: f"Numbers: {data}" # (parameter) data: list[int]
        )
        .then_process(Proc.JSON_DUMPS)
        .then_map(lambda x: x)
        .then_print(lambda data: f"dumped: {data}") # (method) def then_print(transform_fn: (str) -> (_O@then_print | Awaitable[_O@then_print])) -> Chain[_O@then_print]
        .then_parallel(
            Chain(1).then_map(lambda x: x * 2),
            Chain(2).then_map(lambda x: x * 3),
            Chain(3).then_map(lambda x: x * 4),
        )
        .then_print(lambda data: f"Parallel results: {data}")
    )

    # @@ STEP 3: Print final result. @@
    print(f"Result: {result}")
    print()


async def string_processing_example():
    """Example processing strings with then_print.

    :return None: None
    """
    # @@ STEP 1: Print example header. @@
    print("🔗 String Processing Example")
    print("=" * 40)

    # @@ STEP 2: Process a list of names. @@
    names = ["Alice", "Bob", "Charlie", "Diana"]

    result = await Chain(names).then_print(
        lambda names: f"Team members: {', '.join(names)}"
    )

    # @@ STEP 3: Print final result. @@
    print(f"Result: {result}")
    print()


async def data_transformation_example():
    """Example showing data transformation with then_print.
    
    :return None: None
    """
    # @@ STEP 1: Print example header. @@
    print("🔗 Data Transformation Example")
    print("=" * 40)

    # @@ STEP 2: Start with raw data. @@
    raw_data = [
        {"name": "Product A", "price": 29.99, "stock": 15},
        {"name": "Product B", "price": 49.99, "stock": 8},
        {"name": "Product C", "price": 19.99, "stock": 23}
    ]

    # @@ STEP 3: Transform and print inventory summary. @@
    result = await Chain(raw_data).then_print(
        lambda products: f"Inventory: {len(products)} products, "
                        f"Total value: ${sum(p['price'] * p['stock'] for p in products):.2f}"
    )

    # @@ STEP 4: Print final result. @@
    print(f"Result: {result}")
    print()


async def chained_operations_example():
    """Example showing chained operations with then_print.

    :return None: None
    """
    # @@ STEP 1: Print example header. @@
    print("🔗 Chained Operations Example")
    print("=" * 40)

    # @@ STEP 2: Chain multiple operations together. @@
    numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

    result = await (Chain(numbers)
                   .then_map(lambda n: n * 2)                                 # Double them
                   .then_map(lambda nums: [n for n in nums if n % 2 == 0])  # Filter even numbers
                   .then_map(lambda nums: [n * n for n in nums])            # Square them
                   .then_print(lambda squares: f"Even squares: {squares}")      # Print with description
                   )

    # @@ STEP 3: Print final result. @@
    print(f"Final result: {result}")
    print()


async def async_processing_example():
    """Example with async processing and then_print."""
    print("🔗 Async Processing Example")
    print("=" * 40)
    
    async def async_formatter(data):
        """Simulate async processing (e.g., API call, database query)."""
        await asyncio.sleep(0.1)  # Simulate async work
        return f"Processed {len(data)} items asynchronously: {data}"
    
    # Use async function with then_print
    result = await Chain(["apple", "banana", "cherry"]).then_print(async_formatter)
    
    print(f"Result: {result}")
    print()


async def error_handling_example():
    """Example showing error handling with then_print."""
    print("🔗 Error Handling Example")
    print("=" * 40)
    
    try:
        # This will work fine
        result = await Chain([1, 2, 3]).then_print(
            lambda data: f"Sum: {sum(data)}"
        )
        print(f"Success: {result}")
        
        # This might cause an error if the lambda fails
        result = await Chain(["a", "b", "c"]).then_print(
            lambda data: f"Sum: {sum(data)}"  # This will fail - can't sum strings
        )
        print(f"This shouldn't print: {result}")
        
    except Exception as e:
        print(f"Caught expected error: {e}")
    
    print()


async def main():
    """Run all examples.

    :return None: None
    """
    # @@ STEP 1: Print main header. @@
    print("🎯 ChainedPy Remote Chain Examples")
    print("Using project: your_project_name")
    print("Base chain: myprivatechain1")
    print("Method: then_print")
    print("=" * 60)
    print()

    # @@ STEP 2: Run all examples. @@
    await basic_then_print_example()
    await string_processing_example()
    await data_transformation_example()
    await chained_operations_example()
    await async_processing_example()
    await error_handling_example()

    # @@ STEP 3: Print completion message and key points. @@
    print("✅ All examples completed!")
    print()
    print("💡 Key Points:")
    print("   - The Chain class comes from your_project_name")
    print("   - then_print method comes from myprivatechain1 (remote base chain)")
    print("   - Supports both sync and async lambda functions")
    print("   - Can be chained with other operations")
    print("   - Handles data transformation and printing in one step")


if __name__ == "__main__":
    # Run the examples
    asyncio.run(main())

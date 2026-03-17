"""ChainedPy type variables and parameter specifications.

This module defines the core type variables used throughout ChainedPy for generic type
annotations and covariance relationships. These type variables enable proper type inference
and safety across the entire chain transformation pipeline.

The module provides covariant type variables for input and output types, as well as
parameter specifications for callable signatures. These types are fundamental to
ChainedPy's type system and are used extensively in [Link][chainedpy.link.Link], [Chain][chainedpy.chain.Chain], and other
core abstractions.

Note:
    All type variables are covariant to support proper type inheritance and
    transformation in the chain pipeline. This enables type-safe composition
    of transformations with compatible input/output types.

Example:
    ```python
    from chainedpy.typing import I_co, O_co, P
    from typing import Generic, Callable

    # Using covariant type variables
    class Transform(Generic[I_co, O_co]):
        def apply(self, value: I_co) -> O_co:
            ...

    # Using parameter specifications
    def with_params(func: Callable[P, O_co]) -> Callable[P, O_co]:
        return func
    ```

See Also:
    - [I_co][chainedpy.typing.I_co]: Input covariant type variable
    - [O_co][chainedpy.typing.O_co]: Output covariant type variable
    - [P][chainedpy.typing.P]: Parameter specification for callables
"""
from typing import TypeVar, ParamSpec

# @@ STEP 1: Define covariant type variables. @@
I_co = TypeVar("I_co", covariant=True)
"""[TypeVar][typing.TypeVar]: Input covariant type variable for transformations.

This covariant type variable represents input types in transformation pipelines.
Covariance allows for proper type inheritance where a transformation accepting
a base type can also accept derived types.

:type: [TypeVar][typing.TypeVar] (covariant=True)
"""

O_co = TypeVar("O_co", covariant=True)
"""[TypeVar][typing.TypeVar]: Output covariant type variable for transformations.

This covariant type variable represents output types in transformation pipelines.
Covariance enables type-safe composition where transformations producing derived
types can be used where base types are expected.

:type: [TypeVar][typing.TypeVar] (covariant=True)
"""

# @@ STEP 2: Define parameter specifications. @@
P = ParamSpec("P")
"""[ParamSpec][typing.ParamSpec]: Parameter specification for callable signatures.

This parameter specification captures the parameter signature of callable objects,
enabling type-safe wrapping and decoration of functions while preserving their
exact parameter types and signatures.

:type: [ParamSpec][typing.ParamSpec]
"""

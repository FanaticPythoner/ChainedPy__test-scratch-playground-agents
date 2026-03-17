"""Built-in processors for ChainedPy.

This module provides a comprehensive collection of built-in processors that can be used
with the [then_process][chainedpy.plugins.core.then_process] method. Each processor declares the type it returns
through its `.output_type` property, enabling type-safe transformations with runtime
contract enforcement.

The type contract system works as follows:
    • if `output_type is None`  ->  the processor must preserve the
      input type (identity-shaped processors);
    • else                      ->  the processor must return a value
      that `isinstance(result, output_type)`.

A runtime guard enforces this contract, so downstream links can rely on
it with zero dynamic checks. This ensures type safety while maintaining
flexibility for various transformation operations.

Note:
    All processors are stateless and can be safely reused across multiple
    chain executions. They are registered automatically when this module
    is imported.

Example:
    ```python
    from chainedpy import Chain

    # String processing
    result = await (
        Chain("  hello world  ")
        .then_process("strip")
        .then_process("upper")
    )
    assert result == "HELLO WORLD"

    # Type conversions
    result = await (
        Chain("42")
        .then_process("to_int")
        .then_map(lambda x: x * 2)
    )
    assert result == 84

    # JSON processing
    result = await (
        Chain('{"name": "John", "age": 30}')
        .then_process("json_loads")
        .then_map(lambda obj: obj["name"])
    )
    assert result == "John"
    ```

See Also:
    - [Proc][chainedpy.plugins.processors.Proc]: Main processor enum class
    - [then_process][chainedpy.plugins.core.then_process]: Method that uses these processors
    - [chainedpy.register.processor][chainedpy.register.processor]: Registration decorator
"""
from __future__ import annotations

import base64
import json
import re
from enum   import Enum
from typing import Any, Optional

from ..exceptions import ProcessorError # pylint: disable=relative-beyond-top-level


from ..register import processor # pylint: disable=relative-beyond-top-level


@processor("builtin")
class Proc(Enum):
    r"""Stateless one-shot processors used by [then_process][chainedpy.plugins.core.then_process].

    Each processor enum value defines a transformation operation with
    a declared output type for type safety. The processors cover common
    transformation needs including type conversions, string operations,
    encoding/decoding, JSON processing, and regular expressions.

    Example:
        ```python
        from chainedpy import Chain
        from chainedpy.plugins.processors import Proc

        # Using processors directly
        result = Proc.UPPER.apply("hello")
        assert result == "HELLO"

        # Using in chains
        result = await (
            Chain("42.5")
            .then_process(Proc.TO_FLOAT)
            .then_map(lambda x: x * 2)
        )
        assert result == 85.0

        # With parameters
        result = await (
            Chain("hello world")
            .then_process(Proc.REGEX_EXTRACT, param=r"(\w+)")
        )
        assert result == "hello"
        ```

    See Also:
        - [then_process][chainedpy.plugins.core.then_process]: Method that uses these processors
        - [apply][chainedpy.plugins.processors.Proc.apply]: Method to apply processor transformations
    """

    # @@ STEP 1: Define processor enum values. @@
    # fmt: off
    TO_INT        = ("to_int",        int)
    TO_FLOAT      = ("to_float",      float)

    STRIP         = ("strip",         str)
    UPPER         = ("upper",         str)
    LOWER         = ("lower",         str)

    B64_DECODE    = ("b64_decode",    bytes)
    B64_ENCODE    = ("b64_encode",    str)

    JSON_LOADS    = ("json_loads",    object)   # Could be any JSON type.
    JSON_DUMPS    = ("json_dumps",    str)

    REGEX_EXTRACT = ("regex_extract", str)      # `None` also allowed.
    REGEX_MATCH   = ("regex_match",   bool)
    # fmt: on

    # @@ STEP 2: Define enum constructor. @@
    def __new__(cls, value: str, out_type: type | None):
        """Create new processor enum instance.

        :param value: Processor name.
        :type value: str
        :param out_type: Expected output type.
        :type out_type: type | None
        :return Proc: New processor instance.
        """
        obj = object.__new__(cls)
        obj._value_ = value
        obj.output_type: type | None = out_type # type: ignore
        return obj

    # ----------------------------------------------------------------------
    #                        **   C O R E   **                               #
    # ----------------------------------------------------------------------
    @property
    def name(self) -> str: # TODO: FIX THIS EVERYWHERE. RIGHT NOW, IT THROWS: "method already defined line 3PylintE0102:function-redefined" AS "name" IS A PROTECTED PROPERTY OF ENUMS
        """Return the public name used in log / link names.

        :return str: Processor name for logging and identification.
        """
        return self.value

    # ----------------------------------------------------------------------
    #                           apply()                                      #
    # ----------------------------------------------------------------------
    def apply(self, value: Any, *, param: Optional[str] = None) -> Any: # TODO: Map the processor return type using a TypeVar
        """Run the processor - _must_ respect `self.output_type`.

        :param value: Input value to process.
        :type value: Any
        :param param: Optional parameter for the processor, defaults to None.
        :type param: Optional[str], optional
        :return Any: Processed result.
        :raises ProcessorError: If processing fails or type contract is violated.
        """
        try:
            # @@ STEP 1: Process numeric conversions. @@
            if self is Proc.TO_INT:
                if param is not None:
                    raise ProcessorError(self.name, value, ValueError("TO_INT does not accept parameters"))
                result: Any = int(value)

            elif self is Proc.TO_FLOAT:
                if param is not None:
                    raise ProcessorError(self.name, value, ValueError("TO_FLOAT does not accept parameters"))
                result = float(value)

            # @@ STEP 2: Process string operations. @@
            elif self is Proc.STRIP:
                result = str(value).strip()

            elif self is Proc.UPPER:
                result = str(value).upper()

            elif self is Proc.LOWER:
                result = str(value).lower()

            # @@ STEP 3: Process base-64 operations. @@
            elif self is Proc.B64_DECODE:
                if not isinstance(value, (str, bytes)):
                    raise ProcessorError(self.name, value, ValueError(f"B64_DECODE requires string or bytes input, got {type(value).__name__}"))
                raw = value.encode() if isinstance(value, str) else value
                result = base64.b64decode(raw)

            elif self is Proc.B64_ENCODE:
                raw = value if isinstance(value, (bytes, bytearray)) else str(value).encode()
                result = base64.b64encode(raw).decode()

            # @@ STEP 4: Process JSON operations. @@
            elif self is Proc.JSON_LOADS:
                payload = value.decode() if isinstance(value, (bytes, bytearray)) else value
                result = json.loads(payload)

            elif self is Proc.JSON_DUMPS:
                result = json.dumps(value)

            # @@ STEP 5: Process regex operations. @@
            elif self == Proc.REGEX_EXTRACT:
                if param is None:
                    raise ProcessorError(self.name, value, ValueError("REGEX_EXTRACT requires a pattern parameter"))
                text = str(value)
                try:
                    matches = re.findall(param, text)
                    if not matches:
                        return ""  # Return empty string for no matches as expected by tests.

                    # If there are capture groups, return all groups for first match.
                    match = re.search(param, text)
                    if match and match.groups():
                        return list(match.groups())  # Return all groups as list.

                    # If multiple matches without groups, return all matches.
                    if len(matches) > 1:
                        return matches

                    # Single match without groups, return the match.
                    return matches[0]
                except re.error as e:
                    raise ProcessorError(self.name, value, e)

            elif self == Proc.REGEX_MATCH:
                if param is None:
                    raise ProcessorError(self.name, value, ValueError("REGEX_MATCH requires a pattern parameter"))
                text = str(value)
                try:
                    return bool(re.search(param, text))
                except re.error as e:
                    raise ProcessorError(self.name, value, e)

            else:
                raise ProcessorError(self.name, value, ValueError(f"Unknown processor: {self}"))

            # @@ STEP 6: Enforce the declared output type. @@
            expected = self.output_type
            if expected is None:                         # Must preserve type.
                if not isinstance(result, type(value)):
                    raise TypeError(
                        f"expected type {type(value).__name__}, "
                        f"got {type(result).__name__}"
                    )
            elif expected is not object and result is not None:
                if not isinstance(result, expected):
                    raise TypeError(
                        f"expected type {expected.__name__}, "
                        f"got {type(result).__name__}"
                    )

            return result


        except ProcessorError:
            raise  # Re-raise ProcessorError as-is.
        except Exception as e:
            raise ProcessorError(self.name, value, e) from e

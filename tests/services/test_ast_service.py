"""
Test ChainedPy AST service functionality.

This module tests all AST parsing, decorator extraction, function signature building,
and TypeVar handling functionality in the AST service. NO exception swallowing.
"""

import ast
import pytest

from chainedpy.services.ast_service import (
    ASTServiceError,
    parse_source_code,
    find_function_definitions,
    find_overloaded_functions,
    has_overload_decorator,
    extract_function_parameters,
    extract_return_type,
    convert_link_wrapper_to_chain,
    extract_typevar_names,
    find_typevar_definitions,
    build_method_signature,
    build_overloaded_method_signatures_from_ast,
    parse_file_for_functions,
    parse_remote_source_for_functions
)


class TestBasicASTOperations:
    """Test basic AST parsing and source code operations.

    :raises Exception: If basic AST operations testing fails.
    """

    def test_parse_source_code_valid_python(self):
        """Test parsing valid Python source code.

        :raises AssertionError: If valid Python source code parsing fails.
        :return None: None
        """
        # @@ STEP 1: Define valid Python source code. @@
        source = """
def test_function():
    return "hello"

class TestClass:
    def method(self):
        pass
"""
        # @@ STEP 2: Parse source code and verify result. @@
        tree = parse_source_code(source)
        assert isinstance(tree, ast.Module)
        assert len(tree.body) == 2  # function and class

    def test_parse_source_code_invalid_syntax(self):
        """Test parsing invalid Python source code raises ASTServiceError.

        :raises AssertionError: If invalid Python source code error handling fails.
        :return None: None
        """
        # @@ STEP 1: Define invalid Python source code. @@
        invalid_source = """
def invalid_function(
    # Missing closing parenthesis and colon
"""
        # @@ STEP 2: Verify parsing raises ASTServiceError. @@
        with pytest.raises(ASTServiceError, match="Failed to parse source code"):
            parse_source_code(invalid_source)

    def test_parse_source_code_empty_string(self):
        """Test parsing empty source code.

        :raises AssertionError: If empty source code parsing fails.
        :return None: None
        """
        # @@ STEP 1: Parse empty source code. @@
        tree = parse_source_code("")

        # @@ STEP 2: Verify empty AST module is created. @@
        assert isinstance(tree, ast.Module)
        assert len(tree.body) == 0


class TestFunctionDefinitionFinding:
    """Test finding function definitions in AST.

    :raises Exception: If function definition finding testing fails.
    """

    def test_find_function_definitions_no_prefix(self):
        """Test finding all function definitions without prefix filter.

        :raises AssertionError: If function definition finding without prefix fails.
        :return None: None
        """
        # @@ STEP 1: Define source code with various functions. @@
        source = """
def regular_function():
    pass

def then_process():
    pass

def as_cached():
    pass

class TestClass:
    def method(self):
        pass
"""
        # @@ STEP 2: Parse source and find all functions. @@
        tree = parse_source_code(source)
        functions = find_function_definitions(tree)

        # @@ STEP 3: Verify all functions are found. @@
        function_names = [f.name for f in functions]
        assert "regular_function" in function_names
        assert "then_process" in function_names
        assert "as_cached" in function_names
        assert "method" in function_names
        assert len(functions) == 4

    def test_find_function_definitions_with_prefix(self):
        """Test finding function definitions with prefix filter.

        :raises AssertionError: If function definition finding with prefix fails.
        :return None: None
        """
        # @@ STEP 1: Define source code with various functions. @@
        source = """
def regular_function():
    pass

def then_process():
    pass

def then_validate():
    pass

def as_cached():
    pass
"""
        # @@ STEP 2: Parse source code. @@
        tree = parse_source_code(source)

        # @@ STEP 3: Test then_ prefix filtering. @@
        then_functions = find_function_definitions(tree, "then_")
        then_names = [f.name for f in then_functions]
        assert then_names == ["then_process", "then_validate"]

        # @@ STEP 4: Test as_ prefix filtering. @@
        as_functions = find_function_definitions(tree, "as_")
        as_names = [f.name for f in as_functions]
        assert as_names == ["as_cached"]

    def test_find_function_definitions_empty_tree(self):
        """Test finding functions in empty AST tree.

        :raises AssertionError: If empty tree function finding fails.
        :return None: None
        """
        # @@ STEP 1: Parse empty source code. @@
        tree = parse_source_code("")

        # @@ STEP 2: Find functions in empty tree. @@
        functions = find_function_definitions(tree)

        # @@ STEP 3: Verify no functions found. @@
        assert functions == []


class TestOverloadedFunctionFinding:
    """Test finding overloaded function definitions.

    :raises Exception: If overloaded function finding testing fails.
    """

    def test_find_overloaded_functions_single_function(self):
        """Test finding single function (no overloads).

        :raises AssertionError: If single function finding fails.
        :return None: None
        """
        # @@ STEP 1: Define source with single function. @@
        source = """
def process_data(data: str) -> str:
    return data.upper()
"""
        # @@ STEP 2: Parse and find overloaded functions. @@
        tree = parse_source_code(source)
        functions = find_overloaded_functions(tree, "process_data")

        # @@ STEP 3: Verify single function found. @@
        assert len(functions) == 1
        assert functions[0].name == "process_data"

    def test_find_overloaded_functions_multiple_overloads(self):
        """Test finding multiple overloaded functions.

        :raises AssertionError: If multiple overloaded function finding fails.
        :return None: None
        """
        # @@ STEP 1: Define source with multiple overloads. @@
        source = """
from typing import overload

@overload
def process_data(data: str) -> str: ...

@overload
def process_data(data: int) -> int: ...

def process_data(data):
    if isinstance(data, str):
        return data.upper()
    return data * 2
"""
        # @@ STEP 2: Parse and find overloaded functions. @@
        tree = parse_source_code(source)
        functions = find_overloaded_functions(tree, "process_data")

        # @@ STEP 3: Verify all overloads found. @@
        assert len(functions) == 3
        for func in functions:
            assert func.name == "process_data"

    def test_find_overloaded_functions_nonexistent(self):
        """Test finding nonexistent function returns empty list.

        :raises AssertionError: If nonexistent function handling fails.
        :return None: None
        """
        # @@ STEP 1: Define source without target function. @@
        source = """
def other_function():
    pass
"""
        # @@ STEP 2: Parse and search for nonexistent function. @@
        tree = parse_source_code(source)
        functions = find_overloaded_functions(tree, "nonexistent_function")

        # @@ STEP 3: Verify empty list returned. @@
        assert functions == []


class TestDecoratorDetection:
    """Test decorator detection functionality.

    :raises Exception: If decorator detection testing fails.
    """

    def test_has_overload_decorator_simple_name(self):
        """Test detecting @overload decorator as simple name.

        :raises AssertionError: If @overload decorator detection fails.
        :return None: None
        """
        # @@ STEP 1: Define source with @overload decorator. @@
        source = """
from typing import overload

@overload
def test_function(x: int) -> int: ...
"""
        # @@ STEP 2: Parse and find function. @@
        tree = parse_source_code(source)
        functions = find_function_definitions(tree, "test_function")

        # @@ STEP 3: Verify @overload decorator detected. @@
        assert len(functions) == 1
        assert has_overload_decorator(functions[0]) is True

    def test_has_overload_decorator_attribute_access(self):
        """Test detecting @typing.overload decorator as attribute access.

        :raises AssertionError: If @typing.overload decorator detection fails.
        :return None: None
        """
        # @@ STEP 1: Define source with @typing.overload decorator. @@
        source = """
import typing

@typing.overload
def test_function(x: int) -> int: ...
"""
        # @@ STEP 2: Parse and find function. @@
        tree = parse_source_code(source)
        functions = find_function_definitions(tree, "test_function")

        # @@ STEP 3: Verify @typing.overload decorator detected. @@
        assert len(functions) == 1
        assert has_overload_decorator(functions[0]) is True

    def test_has_overload_decorator_no_decorator(self):
        """Test function without @overload decorator.

        :raises AssertionError: If non-overload function detection fails.
        :return None: None
        """
        # @@ STEP 1: Define source without @overload decorator. @@
        source = """
def test_function(x: int) -> int:
    return x * 2
"""
        # @@ STEP 2: Parse and find function. @@
        tree = parse_source_code(source)
        functions = find_function_definitions(tree, "test_function")

        # @@ STEP 3: Verify no @overload decorator detected. @@
        assert len(functions) == 1
        assert has_overload_decorator(functions[0]) is False

    def test_has_overload_decorator_other_decorators(self):
        """Test function with other decorators but not @overload.

        :raises AssertionError: If other decorator handling fails.
        :return None: None
        """
        # @@ STEP 1: Define source with other decorators. @@
        source = """
@staticmethod
@property
def test_function(x: int) -> int:
    return x * 2
"""
        # @@ STEP 2: Parse and find function. @@
        tree = parse_source_code(source)
        functions = find_function_definitions(tree, "test_function")

        # @@ STEP 3: Verify no @overload decorator detected. @@
        assert len(functions) == 1
        assert has_overload_decorator(functions[0]) is False

    def test_has_overload_decorator_mixed_decorators(self):
        """Test function with @overload and other decorators.

        :raises AssertionError: If mixed decorator handling fails.
        :return None: None
        """
        # @@ STEP 1: Define source with mixed decorators. @@
        source = """
from typing import overload

@staticmethod
@overload
def test_function(x: int) -> int: ...
"""
        # @@ STEP 2: Parse and find function. @@
        tree = parse_source_code(source)
        functions = find_function_definitions(tree, "test_function")

        # @@ STEP 3: Verify @overload decorator detected among others. @@
        assert len(functions) == 1
        assert has_overload_decorator(functions[0]) is True


class TestParameterExtraction:
    """Test function parameter extraction from AST.

    :raises Exception: If parameter extraction testing fails.
    """

    def test_extract_function_parameters_simple(self):
        """Test extracting simple function parameters.

        :raises AssertionError: If simple parameter extraction fails.
        :return None: None
        """
        # @@ STEP 1: Define source with simple parameters. @@
        source = """
def test_function(a: int, b: str, c: float) -> None:
    pass
"""
        # @@ STEP 2: Parse and extract parameters. @@
        tree = parse_source_code(source)
        functions = find_function_definitions(tree, "test_function")

        params = extract_function_parameters(functions[0], skip_self=False)
        expected = ["a: int", "b: str", "c: float"]
        assert params == expected

    def test_extract_function_parameters_skip_self(self):
        """Test extracting parameters while skipping self.

        :raises AssertionError: If self parameter skipping fails.
        :return None: None
        """
        # @@ STEP 1: Define source with self parameter. @@
        source = """
class TestClass:
    def method(self, a: int, b: str) -> None:
        pass
"""
        # @@ STEP 2: Parse and extract parameters. @@
        tree = parse_source_code(source)
        functions = find_function_definitions(tree, "method")

        # @@ STEP 3: Skip self (default behavior). @@
        params = extract_function_parameters(functions[0], skip_self=True)
        expected = ["a: int", "b: str"]
        assert params == expected

        # @@ STEP 4: Include self. @@
        params_with_self = extract_function_parameters(functions[0], skip_self=False)
        expected_with_self = ["self: Any", "a: int", "b: str"]
        assert params_with_self == expected_with_self

    def test_extract_function_parameters_keyword_only(self):
        """Test extracting keyword-only parameters with defaults.

        :raises AssertionError: If keyword-only parameter extraction fails.
        :return None: None
        """
        # @@ STEP 1: Define source with keyword-only parameters. @@
        source = """
def test_function(a: int, *, b: str = "default", c: float) -> None:
    pass
"""
        # @@ STEP 2: Parse and extract parameters. @@
        tree = parse_source_code(source)
        functions = find_function_definitions(tree, "test_function")

        params = extract_function_parameters(functions[0], skip_self=False)
        expected = ["a: int", "*", "b: str = 'default'", "c: float"]
        assert params == expected

    def test_extract_function_parameters_varargs_kwargs(self):
        """Test extracting *args and **kwargs parameters.

        :raises AssertionError: If varargs/kwargs parameter extraction fails.
        :return None: None
        """
        # @@ STEP 1: Define source with varargs and kwargs. @@
        source = """
def test_function(a: int, *args: str, **kwargs: float) -> None:
    pass
"""
        # @@ STEP 2: Parse and extract parameters. @@
        tree = parse_source_code(source)
        functions = find_function_definitions(tree, "test_function")

        params = extract_function_parameters(functions[0], skip_self=False)
        expected = ["a: int", "*args: str", "**kwargs: float"]
        assert params == expected

    def test_extract_function_parameters_no_annotations(self):
        """Test extracting parameters without type annotations.

        :raises AssertionError: If parameter extraction without annotations fails.
        :return None: None
        """
        # @@ STEP 1: Define source without type annotations. @@
        source = """
def test_function(a, b, c):
    pass
"""
        # @@ STEP 2: Parse and extract parameters. @@
        tree = parse_source_code(source)
        functions = find_function_definitions(tree, "test_function")

        params = extract_function_parameters(functions[0], skip_self=False)
        expected = ["a: Any", "b: Any", "c: Any"]
        assert params == expected

    def test_extract_function_parameters_complex_annotations(self):
        """Test extracting parameters with complex type annotations.

        :raises AssertionError: If complex parameter extraction fails.
        :return None: None
        """
        # @@ STEP 1: Define source with complex type annotations. @@
        source = """
from typing import List, Dict, Optional, Union

def test_function(
    a: List[str],
    b: Dict[str, int],
    c: Optional[Union[str, int]]
) -> None:
    pass
"""
        # @@ STEP 2: Parse and extract parameters. @@
        tree = parse_source_code(source)
        functions = find_function_definitions(tree, "test_function")

        params = extract_function_parameters(functions[0], skip_self=False)
        expected = [
            "a: List[str]",
            "b: Dict[str, int]",
            "c: Optional[Union[str, int]]"
        ]
        assert params == expected


class TestReturnTypeExtraction:
    """Test return type extraction from function definitions.

    :raises Exception: If return type extraction testing fails.
    """

    def test_extract_return_type_simple(self):
        """Test extracting simple return type.

        :raises AssertionError: If simple return type extraction fails.
        :return None: None
        """
        # @@ STEP 1: Define source with simple return type. @@
        source = """
def test_function() -> str:
    return "hello"
"""
        # @@ STEP 2: Parse and extract return type. @@
        tree = parse_source_code(source)
        functions = find_function_definitions(tree, "test_function")

        return_type = extract_return_type(functions[0])
        assert return_type == "str"

    def test_extract_return_type_complex(self):
        """Test extracting complex return type.

        :raises AssertionError: If complex return type extraction fails.
        :return None: None
        """
        # @@ STEP 1: Define source with complex return type. @@
        source = """
from typing import List, Dict

def test_function() -> Dict[str, List[int]]:
    return {}
"""
        # @@ STEP 2: Parse and extract return type. @@
        tree = parse_source_code(source)
        functions = find_function_definitions(tree, "test_function")

        return_type = extract_return_type(functions[0])
        assert return_type == "Dict[str, List[int]]"

    def test_extract_return_type_none_annotation(self):
        """Test extracting return type when no annotation present.

        :raises AssertionError: If return type extraction without annotation fails.
        :return None: None
        """
        # @@ STEP 1: Define source without return type annotation. @@
        source = """
def test_function():
    return "hello"
"""
        # @@ STEP 2: Parse and extract return type. @@
        tree = parse_source_code(source)
        functions = find_function_definitions(tree, "test_function")

        return_type = extract_return_type(functions[0])
        assert return_type == "Any"


class TestLinkWrapperConversion:
    """Test conversion of Link/Wrapper return types to Chain.

    :raises Exception: If Link/Wrapper conversion testing fails.
    """

    def test_convert_link_to_chain_then_method(self):
        """Test converting Link return type to Chain for then_ methods.

        :raises AssertionError: If Link to Chain conversion fails.
        :return None: None
        """
        # @@ STEP 1: Define source with Link return type. @@
        source = """
from chainedpy.base.link import Link
from typing import TypeVar

_T = TypeVar('_T')
_O = TypeVar('_O')

def then_process(self, func) -> Link[_T, _O]:
    pass
"""
        # @@ STEP 2: Parse and convert Link to Chain. @@
        tree = parse_source_code(source)
        functions = find_function_definitions(tree, "then_process")

        converted = convert_link_wrapper_to_chain(functions[0].returns, "then_process")
        assert converted == '"Chain[_O]"'

    def test_convert_wrapper_to_chain_as_method(self):
        """Test converting Wrapper return type to Chain for as_ methods.

        :raises AssertionError: If Wrapper to Chain conversion fails.
        :return None: None
        """
        # @@ STEP 1: Define source with Wrapper return type. @@
        source = """
from chainedpy.base.wrapper import Wrapper
from typing import TypeVar

_T = TypeVar('_T')

def as_cached(self, ttl) -> Wrapper[_T, _T]:
    pass
"""
        # @@ STEP 2: Parse and convert Wrapper to Chain. @@
        tree = parse_source_code(source)
        functions = find_function_definitions(tree, "as_cached")

        converted = convert_link_wrapper_to_chain(functions[0].returns, "as_cached")
        assert converted == '"Chain[_T]"'

    def test_convert_link_single_type_param(self):
        """Test converting Link with single type parameter.

        :raises AssertionError: If Link single type parameter conversion fails.
        :return None: None
        """
        # @@ STEP 1: Define source with single type parameter Link. @@
        source = """
from chainedpy.base.link import Link
from typing import TypeVar

_T = TypeVar('_T')

def then_process(self, func) -> Link[_T]:
    pass
"""
        # @@ STEP 2: Parse and convert Link to Chain. @@
        tree = parse_source_code(source)
        functions = find_function_definitions(tree, "then_process")

        converted = convert_link_wrapper_to_chain(functions[0].returns, "then_process")
        assert converted == '"Chain[_T]"'

    def test_convert_no_conversion_needed(self):
        """Test return type that doesn't need conversion.

        :raises AssertionError: If no conversion handling fails.
        :return None: None
        """
        # @@ STEP 1: Define source with regular return type. @@
        source = """
def regular_function() -> str:
    pass
"""
        # @@ STEP 2: Parse and verify no conversion needed. @@
        tree = parse_source_code(source)
        functions = find_function_definitions(tree, "regular_function")

        converted = convert_link_wrapper_to_chain(functions[0].returns, "regular_function")
        assert converted == "str"


class TestTypeVarExtraction:
    """Test TypeVar name extraction from type annotations.

    :raises Exception: If TypeVar extraction testing fails.
    """

    def test_extract_typevar_names_simple(self):
        """Test extracting simple TypeVar names.

        :raises AssertionError: If simple TypeVar extraction fails.
        :return None: None
        """
        # @@ STEP 1: Extract TypeVars from simple annotation. @@
        annotation = "_T"
        typevars = extract_typevar_names(annotation)
        assert typevars == {"_T"}

    def test_extract_typevar_names_multiple(self):
        """Test extracting multiple TypeVar names.

        :raises AssertionError: If multiple TypeVar extraction fails.
        :return None: None
        """
        # @@ STEP 1: Extract TypeVars from multiple annotation. @@
        annotation = "Dict[_T, _O]"
        typevars = extract_typevar_names(annotation)
        assert typevars == {"Dict", "_T", "_O"}

    def test_extract_typevar_names_complex(self):
        """Test extracting TypeVars from complex annotations.

        :raises AssertionError: If complex TypeVar extraction fails.
        :return None: None
        """
        # @@ STEP 1: Extract TypeVars from complex annotation. @@
        annotation = "Union[List[_T], Dict[_K, _V]]"
        typevars = extract_typevar_names(annotation)
        assert typevars == {"Union", "List", "_T", "Dict", "_K", "_V"}

    def test_extract_typevar_names_invalid_syntax(self):
        """Test extracting TypeVars from invalid syntax returns empty set.

        :raises AssertionError: If invalid syntax handling fails.
        :return None: None
        """
        # @@ STEP 1: Extract TypeVars from invalid syntax. @@
        annotation = "invalid[syntax"
        typevars = extract_typevar_names(annotation)
        assert typevars == set()

    def test_extract_typevar_names_empty_string(self):
        """Test extracting TypeVars from empty string.

        :raises AssertionError: If empty string handling fails.
        :return None: None
        """
        # @@ STEP 1: Extract TypeVars from empty string. @@
        annotation = ""
        typevars = extract_typevar_names(annotation)
        assert typevars == set()


class TestTypeVarDefinitionFinding:
    """Test finding TypeVar definitions in AST.

    :raises Exception: If TypeVar definition finding testing fails.
    """

    def test_find_typevar_definitions_simple(self):
        """Test finding simple TypeVar definitions.

        :raises AssertionError: If simple TypeVar definition finding fails.
        :return None: None
        """
        # @@ STEP 1: Define source with simple TypeVar definitions. @@
        source = """
from typing import TypeVar

_T = TypeVar('_T')
_O = TypeVar('_O')
"""
        # @@ STEP 2: Parse and find TypeVar definitions. @@
        tree = parse_source_code(source)
        typevars = find_typevar_definitions(tree, "test_module")

        expected = {
            "_T": "from test_module import _T",
            "_O": "from test_module import _O"
        }
        assert typevars == expected

    def test_find_typevar_definitions_with_constraints(self):
        """Test finding TypeVar definitions with constraints.

        :raises AssertionError: If constrained TypeVar definition finding fails.
        :return None: None
        """
        # @@ STEP 1: Define source with constrained TypeVar definitions. @@
        source = """
from typing import TypeVar

_T = TypeVar('_T', str, int)
_Numeric = TypeVar('_Numeric', bound=float)
"""
        # @@ STEP 2: Parse and find TypeVar definitions. @@
        tree = parse_source_code(source)
        typevars = find_typevar_definitions(tree, "test_module")

        expected = {
            "_T": "from test_module import _T",
            "_Numeric": "from test_module import _Numeric"
        }
        assert typevars == expected

    def test_find_typevar_definitions_none_found(self):
        """Test finding TypeVar definitions when none exist.

        :raises AssertionError: If no TypeVar definition handling fails.
        :return None: None
        """
        # @@ STEP 1: Define source without TypeVar definitions. @@
        source = """
def regular_function():
    pass

class RegularClass:
    pass
"""
        # @@ STEP 2: Parse and find TypeVar definitions. @@
        tree = parse_source_code(source)
        typevars = find_typevar_definitions(tree, "test_module")
        assert typevars == {}

    def test_find_typevar_definitions_mixed_assignments(self):
        """Test finding TypeVars among other variable assignments.

        :raises AssertionError: If mixed assignment TypeVar finding fails.
        :return None: None
        """
        # @@ STEP 1: Define source with mixed assignments. @@
        source = """
from typing import TypeVar

_T = TypeVar('_T')
regular_var = "not a typevar"
another_var = 42
_O = TypeVar('_O')
"""
        # @@ STEP 2: Parse and find TypeVar definitions. @@
        tree = parse_source_code(source)
        typevars = find_typevar_definitions(tree, "test_module")

        expected = {
            "_T": "from test_module import _T",
            "_O": "from test_module import _O"
        }
        assert typevars == expected


class TestMethodSignatureBuilding:
    """Test building complete method signatures from AST.

    :raises Exception: If method signature building testing fails.
    """

    def test_build_method_signature_simple(self):
        """Test building simple method signature.

        :raises AssertionError: If simple method signature building fails.
        :return None: None
        """
        # @@ STEP 1: Define source with simple method. @@
        source = """
def test_method(self, data: str) -> str:
    return data.upper()
"""
        # @@ STEP 2: Parse and build method signature. @@
        tree = parse_source_code(source)
        functions = find_function_definitions(tree, "test_method")

        signature, typevars = build_method_signature(functions[0], "test_method", add_self=True)
        expected_signature = "def test_method(self, data: str) -> str: ..."
        assert signature == expected_signature
        assert typevars == {"str"}

    def test_build_method_signature_with_typevars(self):
        """Test building method signature with TypeVars.

        :raises AssertionError: If TypeVar method signature building fails.
        :return None: None
        """
        # @@ STEP 1: Define source with TypeVars. @@
        source = """
from typing import TypeVar

_T = TypeVar('_T')
_O = TypeVar('_O')

def then_process(self, func: Callable[[_T], _O]) -> Link[_T, _O]:
    pass
"""
        # @@ STEP 2: Parse and build method signature. @@
        tree = parse_source_code(source)
        functions = find_function_definitions(tree, "then_process")

        signature, typevars = build_method_signature(functions[0], "then_process", add_self=True)
        expected_signature = 'def then_process(self, func: Callable[[_T], _O]) -> "Chain[_O]": ...'
        assert signature == expected_signature
        assert "_T" in typevars
        assert "_O" in typevars

    def test_build_method_signature_no_return_annotation_then(self):
        """Test building then_ method signature without return annotation.

        :raises AssertionError: If then method signature without return annotation fails.
        :return None: None
        """
        # @@ STEP 1: Define source without return annotation. @@
        source = """
def then_process(self, func):
    pass
"""
        # @@ STEP 2: Parse and build method signature. @@
        tree = parse_source_code(source)
        functions = find_function_definitions(tree, "then_process")

        signature, typevars = build_method_signature(functions[0], "then_process", add_self=True)
        expected_signature = 'def then_process(self, func: Any) -> "Chain[Any]": ...'
        assert signature == expected_signature
        assert typevars == {"Any"}

    def test_build_method_signature_no_return_annotation_as(self):
        """Test building as_ method signature without return annotation.

        :raises AssertionError: If as method signature without return annotation fails.
        :return None: None
        """
        # @@ STEP 1: Define source without return annotation. @@
        source = """
def as_cached(self, ttl):
    pass
"""
        # @@ STEP 2: Parse and build method signature. @@
        tree = parse_source_code(source)
        functions = find_function_definitions(tree, "as_cached")

        signature, typevars = build_method_signature(functions[0], "as_cached", add_self=True)
        expected_signature = 'def as_cached(self, ttl: Any) -> "Chain[_T]": ...'
        assert signature == expected_signature
        assert typevars == {"Any", "_T"}

    def test_build_method_signature_no_self(self):
        """Test building method signature without self parameter.

        :raises AssertionError: If method signature without self fails.
        :return None: None
        """
        # @@ STEP 1: Define source without self parameter. @@
        source = """
def standalone_function(data: str) -> str:
    return data
"""
        # @@ STEP 2: Parse and build method signature. @@
        tree = parse_source_code(source)
        functions = find_function_definitions(tree, "standalone_function")

        signature, typevars = build_method_signature(functions[0], "standalone_function", add_self=False)
        expected_signature = "def standalone_function(data: str) -> str: ..."
        assert signature == expected_signature
        assert typevars == {"str"}


class TestOverloadedMethodSignatures:
    """Test building overloaded method signatures from AST.

    :raises Exception: If overloaded method signature testing fails.
    """

    def test_build_overloaded_signatures_single_function(self):
        """Test building signatures for single function (no overloads).

        :raises AssertionError: If single function signature building fails.
        :return None: None
        """
        # @@ STEP 1: Define source with single function. @@
        source = """
def process_data(self, data: str) -> str:
    return data.upper()
"""
        # @@ STEP 2: Parse and build overloaded signatures. @@
        tree = parse_source_code(source)
        signature, typevars = build_overloaded_method_signatures_from_ast(tree, "process_data", add_self=True)

        expected_signature = "def process_data(self, data: str) -> str: ..."
        assert signature == expected_signature
        assert typevars == {"str"}

    def test_build_overloaded_signatures_multiple_overloads(self):
        """Test building signatures for multiple overloaded functions.

        :raises AssertionError: If multiple overloaded function signature building fails.
        :return None: None
        """
        # @@ STEP 1: Define source with multiple overloaded functions. @@
        source = """
from typing import overload

@overload
def process_data(self, data: str) -> str: ...

@overload
def process_data(self, data: int) -> int: ...

def process_data(self, data):
    if isinstance(data, str):
        return data.upper()
    return data * 2
"""
        # @@ STEP 2: Parse and build overloaded signatures. @@
        tree = parse_source_code(source)
        signature, typevars = build_overloaded_method_signatures_from_ast(tree, "process_data", add_self=True)

        # @@ STEP 3: Should contain @overload decorators for first two, regular signature for last. @@
        assert "@overload" in signature
        assert "def process_data(self, data: str) -> str: ..." in signature
        assert "def process_data(self, data: int) -> int: ..." in signature
        assert 'def process_data(self, data: Any) -> "Chain[_T]": ...' in signature
        assert typevars == {"str", "int", "Any", "_T"}

    def test_build_overloaded_signatures_nonexistent_function(self):
        """Test building signatures for nonexistent function.

        :raises AssertionError: If nonexistent function signature building fails.
        :return None: None
        """
        # @@ STEP 1: Define source without target function. @@
        source = """
def other_function():
    pass
"""
        # @@ STEP 2: Parse and build signatures for nonexistent function. @@
        tree = parse_source_code(source)
        signature, typevars = build_overloaded_method_signatures_from_ast(tree, "nonexistent", add_self=True)

        expected_signature = 'def nonexistent(self) -> "Chain[Any]": ...'
        assert signature == expected_signature
        assert typevars == set()

    def test_build_overloaded_signatures_mixed_decorators(self):
        """Test building signatures with mixed decorators.

        :raises AssertionError: If mixed decorator signature building fails.
        :return None: None
        """
        # @@ STEP 1: Define source with mixed decorators. @@
        source = """
from typing import overload

@staticmethod
@overload
def process_data(data: str) -> str: ...

@overload
@classmethod
def process_data(cls, data: int) -> int: ...

def process_data(data):
    return data
"""
        # @@ STEP 2: Parse and build signatures with mixed decorators. @@
        tree = parse_source_code(source)
        signature, typevars = build_overloaded_method_signatures_from_ast(tree, "process_data", add_self=True)

        # @@ STEP 3: Should detect @overload decorators regardless of other decorators. @@
        assert "@overload" in signature
        assert signature.count("@overload") == 2  # Two overload decorators
        assert typevars == {"str", "int", "Any", "_T"}


class TestFileParsing:
    """Test parsing Python files for function extraction.

    :raises Exception: If file parsing testing fails.
    """

    def test_parse_file_for_functions_valid_file(self, tmp_path):
        """Test parsing valid Python file for functions.

        :param tmp_path: Temporary path fixture.
        :type tmp_path: Path
        :raises AssertionError: If valid file parsing fails.
        :return None: None
        """
        # @@ STEP 1: Create temporary Python file. @@
        test_file = tmp_path / "test_plugin.py"
        test_content = """
def then_process(self, func):
    '''Process data with function.'''
    return func(self.value)

def then_validate(self, validator):
    '''Validate data.'''
    if validator(self.value):
        return self
    raise ValueError("Validation failed")

def regular_function():
    pass
"""
        test_file.write_text(test_content, encoding='utf-8')

        # @@ STEP 2: Parse file for then_ functions. @@
        functions = parse_file_for_functions(test_file, "then_")
        function_names = [f.name for f in functions]

        # @@ STEP 3: Verify correct functions were found. @@
        assert "then_process" in function_names
        assert "then_validate" in function_names
        assert "regular_function" not in function_names
        assert len(functions) == 2

    def test_parse_file_for_functions_nonexistent_file(self, tmp_path):
        """Test parsing nonexistent file raises ASTServiceError.

        :param tmp_path: Temporary path fixture.
        :type tmp_path: Path
        :raises AssertionError: If nonexistent file error handling fails.
        :return None: None
        """
        # @@ STEP 1: Define nonexistent file path. @@
        nonexistent_file = tmp_path / "nonexistent.py"

        # @@ STEP 2: Verify exception is raised. @@
        with pytest.raises(ASTServiceError, match="Failed to parse file"):
            parse_file_for_functions(nonexistent_file, "then_")

    def test_parse_file_for_functions_invalid_syntax(self, tmp_path):
        """Test parsing file with invalid syntax raises ASTServiceError.

        :param tmp_path: Temporary path fixture.
        :type tmp_path: Path
        :raises AssertionError: If invalid syntax error handling fails.
        :return None: None
        """
        # @@ STEP 1: Create file with invalid syntax. @@
        invalid_file = tmp_path / "invalid.py"
        invalid_content = """
def invalid_function(
    # Missing closing parenthesis and colon
"""
        invalid_file.write_text(invalid_content, encoding='utf-8')

        # @@ STEP 2: Verify exception is raised. @@
        with pytest.raises(ASTServiceError, match="Failed to parse file"):
            parse_file_for_functions(invalid_file, "then_")

    def test_parse_remote_source_for_functions_valid_source(self):
        """Test parsing valid remote source code for functions.

        :raises AssertionError: If valid remote source parsing fails.
        :return None: None
        """
        # @@ STEP 1: Define valid remote source. @@
        source = """
def as_cached(self, ttl=300):
    '''Cache result with TTL.'''
    return self

def as_retried(self, attempts=3):
    '''Retry on failure.'''
    return self

def helper_function():
    pass
"""
        # @@ STEP 2: Parse remote source for as_ functions. @@
        functions = parse_remote_source_for_functions(source, "as_")
        function_names = [f.name for f in functions]

        # @@ STEP 3: Verify correct functions were found. @@
        assert "as_cached" in function_names
        assert "as_retried" in function_names
        assert "helper_function" not in function_names
        assert len(functions) == 2

    def test_parse_remote_source_for_functions_invalid_syntax(self):
        """Test parsing invalid remote source raises ASTServiceError.

        :raises AssertionError: If invalid remote source error handling fails.
        :return None: None
        """
        # @@ STEP 1: Define invalid remote source. @@
        invalid_source = """
def invalid_function(
    # Missing closing parenthesis and colon
"""
        # @@ STEP 2: Verify exception is raised. @@
        with pytest.raises(ASTServiceError, match="Failed to parse source code"):
            parse_remote_source_for_functions(invalid_source, "as_")


class TestComplexDecoratorScenarios:
    """Test complex decorator extraction scenarios.

    :raises Exception: If complex decorator scenario testing fails.
    """

    def test_multiple_overload_decorators_complex_types(self):
        """Test multiple @overload decorators with complex type annotations.

        :raises AssertionError: If complex overload decorator handling fails.
        :return None: None
        """
        # @@ STEP 1: Define source with complex overload decorators. @@
        source = """
from typing import overload, Union, List, Dict, Optional

@overload
def complex_method(self, data: str, *, format: str = "json") -> Dict[str, str]: ...

@overload
def complex_method(self, data: List[int], *, format: str = "csv") -> str: ...

@overload
def complex_method(self, data: Union[str, int], *, format: Optional[str] = None) -> Union[Dict[str, str], str]: ...

def complex_method(self, data, *, format=None):
    # Implementation
    pass
"""
        # @@ STEP 2: Parse source and test overload detection. @@
        tree = parse_source_code(source)

        functions = find_overloaded_functions(tree, "complex_method")
        assert len(functions) == 4

        overload_count = sum(1 for func in functions if has_overload_decorator(func))
        assert overload_count == 3

        # @@ STEP 3: Test signature building. @@
        signature, typevars = build_overloaded_method_signatures_from_ast(tree, "complex_method", add_self=True)

        assert "@overload" in signature
        assert signature.count("@overload") == 3
        assert "format: str = 'json'" in signature
        assert "format: str = 'csv'" in signature
        assert "format: Optional[str] = None" in signature

        # @@ STEP 4: Check TypeVars extracted - Optional is not extracted from parameters with defaults. @@
        expected_typevars = {"Dict", "str", "List", "int", "Union", "Any", "_T"}
        assert expected_typevars.issubset(typevars)

    def test_nested_class_method_decorators(self):
        """Test decorator detection in nested class methods.

        :raises AssertionError: If nested class method decorator detection fails.
        :return None: None
        """
        # @@ STEP 1: Define source with nested class methods. @@
        source = """
from typing import overload

class OuterClass:
    class InnerClass:
        @overload
        def nested_method(self, x: int) -> int: ...

        @overload
        def nested_method(self, x: str) -> str: ...

        def nested_method(self, x):
            return x

    @overload
    def outer_method(self, data: str) -> str: ...

    def outer_method(self, data):
        return data
"""
        # @@ STEP 2: Parse source and find all methods. @@
        tree = parse_source_code(source)

        all_functions = find_function_definitions(tree)
        method_names = [f.name for f in all_functions]

        assert "nested_method" in method_names
        assert "outer_method" in method_names

        # @@ STEP 3: Test overload detection for nested method. @@
        nested_functions = find_overloaded_functions(tree, "nested_method")
        assert len(nested_functions) == 3

        nested_overload_count = sum(1 for func in nested_functions if has_overload_decorator(func))
        assert nested_overload_count == 2

        # @@ STEP 4: Test overload detection for outer method. @@
        outer_functions = find_overloaded_functions(tree, "outer_method")
        assert len(outer_functions) == 2

        outer_overload_count = sum(1 for func in outer_functions if has_overload_decorator(func))
        assert outer_overload_count == 1

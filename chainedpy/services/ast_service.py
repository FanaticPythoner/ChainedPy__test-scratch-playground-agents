"""AST analysis service for ChainedPy.

This service centralizes ALL AST operations to avoid code duplication and ensure consistency
across the ChainedPy codebase. It provides comprehensive functionality for parsing Python
source code, analyzing chain methods, extracting function signatures, and generating
type-safe stub files.

The service handles complex AST operations including method discovery, signature extraction,
type annotation processing, and stub generation. All AST-related functionality should
be implemented in this service to maintain consistency and avoid scattered AST code
throughout the codebase.

Note:
    No AST operations should exist outside this service. All modules requiring AST
    functionality should import and use the functions provided here.

Example:
    ```python
    from chainedpy.services import ast_service
    from pathlib import Path

    # Parse source code
    source = "def hello(): return 'world'"
    tree = ast_service.parse_source_code(source)

    # Discover chain methods in a file
    methods = ast_service.discover_chain_methods(Path("my_chain.py"))

    # Extract function signature
    signature = ast_service.extract_function_signature(tree, "hello")

    # Generate stub content
    stub_content = ast_service.generate_stub_content(
        methods, "MyChain", Path("my_project")
    )
    ```

See Also:
    - [parse_source_code][chainedpy.services.ast_service.parse_source_code]: Parse Python source into AST
    - [discover_chain_methods][chainedpy.services.ast_service.discover_chain_methods]: Find chain methods in files
    - [generate_stub_content][chainedpy.services.ast_service.generate_stub_content]: Generate type stub files
    - [chainedpy.exceptions.ASTServiceError][chainedpy.exceptions.ASTServiceError]: AST-specific exceptions
"""
from __future__ import annotations

# @@ STEP 1: Import standard library modules. @@
import ast
from pathlib import Path
from typing import Dict, List, Set, Tuple

# @@ STEP 2: Import third-party modules. @@
# (none)

# @@ STEP 3: Import internal constants. @@
from chainedpy.constants import (
    AST_TYPE_ANY, AST_TYPE_CHAIN, AST_TYPE_WRAPPER, AST_TYPE_LINK,
    PLUGIN_PREFIX_THEN, PLUGIN_PREFIX_AS, TEMPLATE_METHOD_SIGNATURE, TEMPLATE_OVERLOAD_SIGNATURE,
    TEMPLATE_TYPEVAR_IMPORT
)

# @@ STEP 4: Import ChainedPy services. @@
from chainedpy.services import filesystem_service as fs_utils
from chainedpy.services.template_service import render_template

# @@ STEP 5: Import ChainedPy internal modules. @@
from chainedpy.exceptions import ASTServiceError

# @@ STEP 6: Import TYPE_CHECKING modules. @@
# (none)


# No logging needed in this service.


def parse_source_code(source: str) -> ast.AST:
    """Parse Python source code into AST.

    Example:
        ```python
        from chainedpy.services.ast_service import parse_source_code
        from chainedpy.exceptions import ASTServiceError
        import ast

        # Parse simple function
        source = '''
        def hello_world():
            return "Hello, World!"
        '''

        tree = parse_source_code(source)
        assert isinstance(tree, ast.AST)
        assert isinstance(tree, ast.Module)

        # Parse class definition
        class_source = '''
        class MyClass:
            def method(self, x: int) -> str:
                return str(x)
        '''

        class_tree = parse_source_code(class_source)
        assert isinstance(class_tree, ast.Module)

        # Parse complex code with imports
        complex_source = '''
        from typing import List, Dict
        import asyncio

        async def process_data(data: List[Dict[str, int]]) -> Dict[str, int]:
            result = {}
            for item in data:
                result.update(item)
            return result
        '''

        complex_tree = parse_source_code(complex_source)
        assert isinstance(complex_tree, ast.Module)

        # Error handling for invalid syntax
        try:
            parse_source_code("def invalid syntax:")
        except ASTServiceError as e:
            print(f"Syntax error: {e}")
            assert "Failed to parse" in str(e)
        ```

    :param source: Python source code string.
    :type source: [str][str]
    :return [ast.AST][ast.AST]: AST tree.
    :raises ASTServiceError: If parsing fails.
    """
    try:
        return ast.parse(source)
    except SyntaxError as e:
        raise ASTServiceError(f"Failed to parse source code: {e}") from e


def find_function_definitions(tree: ast.AST, name_prefix: str = "") -> List[ast.FunctionDef]:
    """Find all function definitions in AST that match the given prefix.

    Example:
        ```python
        from chainedpy.services.ast_service import parse_source_code, find_function_definitions
        import ast

        # Source with multiple functions
        source = '''
        def then_map(self, fn):
            return self._add_link(fn)

        def then_filter(self, predicate):
            return self._add_link(predicate)

        def as_retry(self, attempts=3):
            return self._wrap(attempts)

        def regular_function():
            pass
        '''

        tree = parse_source_code(source)

        # Find all functions
        all_functions = find_function_definitions(tree)
        assert len(all_functions) == 4
        function_names = [f.name for f in all_functions]
        assert "then_map" in function_names
        assert "then_filter" in function_names
        assert "as_retry" in function_names
        assert "regular_function" in function_names

        # Find functions with "then_" prefix
        then_functions = find_function_definitions(tree, "then_")
        assert len(then_functions) == 2
        then_names = [f.name for f in then_functions]
        assert "then_map" in then_names
        assert "then_filter" in then_names
        assert "as_retry" not in then_names

        # Find functions with "as_" prefix
        as_functions = find_function_definitions(tree, "as_")
        assert len(as_functions) == 1
        assert as_functions[0].name == "as_retry"

        # No matches for non-existent prefix
        no_matches = find_function_definitions(tree, "nonexistent_")
        assert len(no_matches) == 0
        ```

    :param tree: AST tree to search.
    :type tree: [ast.AST][ast.AST]
    :param name_prefix: Optional prefix to filter function names, defaults to "".
    :type name_prefix: [str][str], optional
    :return [List][list][[ast.FunctionDef][ast.FunctionDef]]: List of AST FunctionDef nodes matching the criteria.
    """
    # @@ STEP 1: Initialize function list. @@
    functions = []

    # @@ STEP 2: Walk AST and find matching functions. @@
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            if not name_prefix or node.name.startswith(name_prefix):
                functions.append(node)

    return functions


def find_overloaded_functions(tree: ast.AST, function_name: str) -> List[ast.FunctionDef]:
    """Find all overloaded function definitions for a specific function name.

    Example:
        ```python
        from chainedpy.services.ast_service import parse_source_code, find_overloaded_functions
        import ast

        # Source with overloaded functions
        source = '''
        from typing import overload

        @overload
        def then_if(self, condition: bool, then: str, otherwise: str) -> Chain[str]: ...

        @overload
        def then_if(self, condition: Callable, then: Callable, otherwise: Callable) -> Chain[Any]: ...

        def then_if(self, condition, then, otherwise):
            # Implementation
            pass

        def other_function():
            pass
        '''

        tree = parse_source_code(source)

        # Find all overloads of then_if
        then_if_overloads = find_overloaded_functions(tree, "then_if")
        assert len(then_if_overloads) == 3  # 2 overloads + 1 implementation

        # All should have the same name
        for func in then_if_overloads:
            assert func.name == "then_if"
            assert isinstance(func, ast.FunctionDef)

        # Find function with no overloads
        other_funcs = find_overloaded_functions(tree, "other_function")
        assert len(other_funcs) == 1
        assert other_funcs[0].name == "other_function"

        # Find non-existent function
        no_funcs = find_overloaded_functions(tree, "nonexistent")
        assert len(no_funcs) == 0
        ```

    :param tree: AST tree to search.
    :type tree: [ast.AST][ast.AST]
    :param function_name: Exact function name to find.
    :type function_name: [str][str]
    :return [List][list][[ast.FunctionDef][ast.FunctionDef]]: List of AST FunctionDef nodes for the same function name (including overloads).
    """
    # @@ STEP 1: Initialize function list. @@
    functions = []

    # @@ STEP 2: Walk AST and find functions with exact name match. @@
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == function_name:
            functions.append(node)

    return functions


def has_overload_decorator(func_node: ast.FunctionDef) -> bool:
    """Check if a function has @overload decorator.

    Example:
        ```python
        from chainedpy.services.ast_service import parse_source_code, find_function_definitions, has_overload_decorator
        import ast

        # Source with overloaded and regular functions
        source = '''
        from typing import overload

        @overload
        def then_if(self, condition: bool) -> Chain[str]: ...

        @typing.overload
        def then_map(self, fn: Callable) -> Chain[Any]: ...

        def regular_function(self):
            pass

        @some_other_decorator
        def decorated_function(self):
            pass
        '''

        tree = parse_source_code(source)
        functions = find_function_definitions(tree)

        # Check each function for overload decorator
        for func in functions:
            if func.name == "then_if":
                assert has_overload_decorator(func) == True
            elif func.name == "then_map":
                assert has_overload_decorator(func) == True
            elif func.name == "regular_function":
                assert has_overload_decorator(func) == False
            elif func.name == "decorated_function":
                assert has_overload_decorator(func) == False

        # Test with function that has no decorators
        simple_source = "def simple(): pass"
        simple_tree = parse_source_code(simple_source)
        simple_funcs = find_function_definitions(simple_tree)
        assert has_overload_decorator(simple_funcs[0]) == False
        ```

    :param func_node: AST FunctionDef node.
    :type func_node: [ast.FunctionDef][ast.FunctionDef]
    :return [bool][bool]: True if function has @overload decorator.
    """
    for decorator in func_node.decorator_list:
        if isinstance(decorator, ast.Name) and decorator.id == 'overload':
            return True
        if isinstance(decorator, ast.Attribute) and decorator.attr == 'overload':
            return True

    return False


def extract_function_parameters(func_node: ast.FunctionDef, skip_self: bool = True) -> List[str]:
    """Extract function parameters from AST FunctionDef node.

    Example:
        ```python
        from chainedpy.services.ast_service import parse_source_code, find_function_definitions, extract_function_parameters
        import ast

        # Source with various function signatures
        source = '''
        def method_with_types(self, name: str, age: int, active: bool = True) -> None:
            pass

        def function_no_types(x, y, z=None):
            pass

        def function_mixed(self, typed_param: str, untyped_param, default_param: int = 42):
            pass
        '''

        tree = parse_source_code(source)
        functions = find_function_definitions(tree)

        # Extract parameters from typed method (skip self)
        typed_method = next(f for f in functions if f.name == "method_with_types")
        params = extract_function_parameters(typed_method, skip_self=True)
        assert "name: str" in params
        assert "age: int" in params
        assert "active: bool = True" in params
        assert len(params) == 3  # self is skipped

        # Extract parameters including self
        params_with_self = extract_function_parameters(typed_method, skip_self=False)
        assert "self: Any" in params_with_self
        assert len(params_with_self) == 4

        # Extract from untyped function
        untyped_func = next(f for f in functions if f.name == "function_no_types")
        untyped_params = extract_function_parameters(untyped_func, skip_self=False)
        assert "x: Any" in untyped_params
        assert "y: Any" in untyped_params
        assert "z: Any = None" in untyped_params

        # Extract from mixed function
        mixed_func = next(f for f in functions if f.name == "function_mixed")
        mixed_params = extract_function_parameters(mixed_func, skip_self=True)
        assert "typed_param: str" in mixed_params
        assert "untyped_param: Any" in mixed_params
        assert "default_param: int = 42" in mixed_params
        ```

    :param func_node: AST FunctionDef node.
    :type func_node: [ast.FunctionDef][ast.FunctionDef]
    :param skip_self: Whether to skip 'self' parameter if present, defaults to True.
    :type skip_self: [bool][bool], optional
    :return [List][list][[str][str]]: List of parameter strings with type annotations.
    """
    params = []

    # Process regular arguments
    args_to_process = func_node.args.args
    if skip_self and args_to_process and args_to_process[0].arg == 'self':
        args_to_process = args_to_process[1:]

    for arg in args_to_process:
        param_name = arg.arg
        if arg.annotation:
            type_annotation = ast.unparse(arg.annotation)
            params.append(f"{param_name}: {type_annotation}")
        else:
            params.append(f"{param_name}: Any")

    if func_node.args.kwonlyargs:
        # Add * separator for keyword-only arguments
        params.append("*")

        # Process keyword-only arguments with their defaults
        kw_defaults = func_node.args.kw_defaults or []
        for i, arg in enumerate(func_node.args.kwonlyargs):
            param_name = arg.arg
            if arg.annotation:
                type_annotation = ast.unparse(arg.annotation)
                param_str = f"{param_name}: {type_annotation}"
            else:
                param_str = f"{param_name}: Any"

            # Add default value if present
            if i < len(kw_defaults) and kw_defaults[i] is not None:
                default_value = ast.unparse(kw_defaults[i])
                param_str += f" = {default_value}"

            params.append(param_str)

    # Process *args if present
    if func_node.args.vararg:
        vararg_name = func_node.args.vararg.arg
        if func_node.args.vararg.annotation:
            vararg_annotation = ast.unparse(func_node.args.vararg.annotation)
            params.append(f"*{vararg_name}: {vararg_annotation}")
        else:
            params.append(f"*{vararg_name}: Any")

    # Process **kwargs if present
    if func_node.args.kwarg:
        kwarg_name = func_node.args.kwarg.arg
        if func_node.args.kwarg.annotation:
            kwarg_annotation = ast.unparse(func_node.args.kwarg.annotation)
            params.append(f"**{kwarg_name}: {kwarg_annotation}")
        else:
            params.append(f"**{kwarg_name}: Any")

    return params


def extract_return_type(func_node: ast.FunctionDef) -> str:
    """Extract return type annotation from AST FunctionDef node.

    Example:
        ```python
        from chainedpy.services.ast_service import parse_source_code, find_function_definitions, extract_return_type

        source = '''
        def typed_function(x: int) -> str:
            return str(x)

        def untyped_function(x):
            return x

        def complex_return() -> List[Dict[str, int]]:
            return []
        '''

        tree = parse_source_code(source)
        functions = find_function_definitions(tree)

        typed_func = next(f for f in functions if f.name == "typed_function")
        assert extract_return_type(typed_func) == "str"

        untyped_func = next(f for f in functions if f.name == "untyped_function")
        assert extract_return_type(untyped_func) == "Any"

        complex_func = next(f for f in functions if f.name == "complex_return")
        assert extract_return_type(complex_func) == "List[Dict[str, int]]"
        ```

    :param func_node: AST FunctionDef node.
    :type func_node: [ast.FunctionDef][ast.FunctionDef]
    :return [str][str]: Return type string.
    """
    if func_node.returns:
        return ast.unparse(func_node.returns)
    return AST_TYPE_ANY


def convert_link_wrapper_to_chain(return_node: ast.AST, function_name: str) -> str:
    """Convert Link/Wrapper return types to Chain for stub generation.

    Example:
        ```python
        from chainedpy.services.ast_service import parse_source_code, convert_link_wrapper_to_chain
        import ast

        source = '''
        def then_map(self) -> Link[str, int]:
            pass

        def as_retry(self) -> Wrapper[str]:
            pass

        def regular_func(self) -> Chain[str]:
            pass
        '''

        tree = parse_source_code(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if node.returns:
                    converted = convert_link_wrapper_to_chain(node.returns, node.name)
                    if node.name == "then_map":
                        assert "Chain[int]" in converted
                    elif node.name == "as_retry":
                        assert "Chain[str]" in converted
                    elif node.name == "regular_func":
                        assert "Chain[str]" in converted
        ```

    :param return_node: AST node representing the return type.
    :type return_node: [ast.AST][ast.AST]
    :param function_name: Name of the function.
    :type function_name: [str][str]
    :return [str][str]: Converted return type string.
    """
    if isinstance(return_node, ast.Subscript) and isinstance(return_node.value, ast.Name):
        base_type = return_node.value.id

        if base_type == AST_TYPE_LINK and function_name.startswith(PLUGIN_PREFIX_THEN):
            # Link[_T, _O] -> "Chain[_O]"" (second type parameter)
            if isinstance(return_node.slice, ast.Tuple) and len(return_node.slice.elts) >= 2:
                output_type = ast.unparse(return_node.slice.elts[1])
                return f'"{AST_TYPE_CHAIN}[{output_type}]"'
            elif isinstance(return_node.slice, ast.Name):
                output_type = ast.unparse(return_node.slice)
                return f'"{AST_TYPE_CHAIN}[{output_type}]"'

        elif base_type == AST_TYPE_WRAPPER and function_name.startswith(PLUGIN_PREFIX_AS):
            # Wrapper[_T, _T] -> "Chain[_T]"" (first type parameter)
            if isinstance(return_node.slice, ast.Tuple) and len(return_node.slice.elts) >= 1:
                input_type = ast.unparse(ast_obj=return_node.slice.elts[0])
                return f'"{AST_TYPE_CHAIN}[{input_type}]"'
            elif isinstance(return_node.slice, ast.Name):
                input_type = ast.unparse(return_node.slice)
                return f'"{AST_TYPE_CHAIN}[{input_type}]"'

    # Return original if no conversion needed
    return ast.unparse(return_node)


def extract_typevar_names(annotation_str: str) -> Set[str]:
    """Extract TypeVar names from a type annotation string.

    Example:
        ```python
        from chainedpy.services.ast_service import extract_typevar_names

        # Simple TypeVar
        typevars = extract_typevar_names("_T")
        assert "_T" in typevars

        # Multiple TypeVars
        typevars = extract_typevar_names("Callable[[_T], _O]")
        assert "_T" in typevars
        assert "_O" in typevars

        # Complex annotation
        typevars = extract_typevar_names("Union[_T, Chain[_O]]")
        assert "_T" in typevars
        assert "_O" in typevars
        assert "Union" in typevars
        assert "Chain" in typevars

        # No TypeVars
        typevars = extract_typevar_names("str")
        assert "str" in typevars

        # Invalid annotation
        typevars = extract_typevar_names("invalid syntax")
        assert isinstance(typevars, set)
        ```

    :param annotation_str: Type annotation string.
    :type annotation_str: [str][str]
    :return [Set][set][[str][str]]: Set of TypeVar names found.
    """
    # @@ STEP 1: Initialize TypeVar set. @@
    typevars = set()

    # @@ STEP 2: Parse annotation and extract TypeVar names. @@
    try:
        tree = ast.parse(annotation_str, mode='eval')
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                typevars.add(node.id)
    except (SyntaxError, ValueError):
        pass

    return typevars


def find_typevar_definitions(tree: ast.AST, module_name: str) -> Dict[str, str]:
    """Find TypeVar definitions in AST and generate import statements.

    Example:
        ```python
        from chainedpy.services.ast_service import parse_source_code, find_typevar_definitions

        source = '''
        from typing import TypeVar

        _T = TypeVar("_T")
        _O = TypeVar("_O", covariant=True)
        P = ParamSpec("P")
        '''

        tree = parse_source_code(source)
        typevars = find_typevar_definitions(tree, "mymodule")

        assert "_T" in typevars
        assert "_O" in typevars
        assert "P" in typevars

        assert "from mymodule import _T" in typevars["_T"]
        assert "from mymodule import _O" in typevars["_O"]
        assert "from mymodule import P" in typevars["P"]
        ```

    :param tree: AST tree to search.
    :type tree: [ast.AST][ast.AST]
    :param module_name: Module name for import statements.
    :type module_name: [str][str]
    :return [Dict][dict][[str][str], [str][str]]: Dictionary mapping TypeVar names to import statements.
    """
    typevar_imports = {}

    for node in ast.walk(tree):
        if (isinstance(node, ast.Assign) and
            len(node.targets) == 1 and
            isinstance(node.targets[0], ast.Name) and
            isinstance(node.value, ast.Call) and
            isinstance(node.value.func, ast.Name) and
            node.value.func.id == 'TypeVar'):

            typevar_name = node.targets[0].id
            import_stmt = render_template(TEMPLATE_TYPEVAR_IMPORT,
                                        module_name=module_name,
                                        typevar_name=typevar_name).strip()
            typevar_imports[typevar_name] = import_stmt

    return typevar_imports


def build_method_signature(func_node: ast.FunctionDef, method_name: str, add_self: bool = True) -> Tuple[str, Set[str]]:
    """Build complete method signature from AST FunctionDef node.

    Example:
        ```python
        from chainedpy.services.ast_service import parse_source_code, find_function_definitions, build_method_signature

        source = '''
        def then_map(self, fn: Callable[[_T], _O]) -> Chain[_O]:
            pass

        def simple_method(self, x: int) -> str:
            pass
        '''

        tree = parse_source_code(source)
        functions = find_function_definitions(tree)

        then_map_func = next(f for f in functions if f.name == "then_map")
        signature, typevars = build_method_signature(then_map_func, "then_map")

        assert "def then_map(self, fn: Callable[[_T], _O]) -> Chain[_O]:" in signature
        assert "_T" in typevars
        assert "_O" in typevars

        simple_func = next(f for f in functions if f.name == "simple_method")
        signature, typevars = build_method_signature(simple_func, "simple_method")

        assert "def simple_method(self, x: int) -> str:" in signature
        assert len(typevars) == 0
        ```

    :param func_node: AST FunctionDef node.
    :type func_node: [ast.FunctionDef][ast.FunctionDef]
    :param method_name: Name of the method.
    :type method_name: [str][str]
    :param add_self: Whether to add 'self' parameter, defaults to True.
    :type add_self: [bool][bool], optional
    :return [Tuple][tuple][[str][str], [Set][set][[str][str]]]: Tuple of (complete signature, set of TypeVars used).
    """
    params = []
    typevars = set()

    # Add self parameter if requested
    if add_self:
        params.append("self")

    # Extract parameters
    param_list = extract_function_parameters(func_node, skip_self=True)
    params.extend(param_list)

    # Extract TypeVars from parameters
    for param in param_list:
        if ": " in param:
            type_part = param.split(": ", 1)[1]
            typevars.update(extract_typevar_names(type_part))

    # Extract return type
    return_type = extract_return_type(func_node)
    if func_node.returns:
        # Convert Link/Wrapper to Chain
        converted_return = convert_link_wrapper_to_chain(func_node.returns, method_name)
        return_type = converted_return
        typevars.update(extract_typevar_names(return_type))
    else:
        # Default return types
        if method_name.startswith(PLUGIN_PREFIX_THEN):
            return_type = '"Chain[Any]"'
        else:
            return_type = '"Chain[_T]"'
            typevars.add('_T')

    # Build complete signature using template
    params_str = ", ".join(params)
    signature = render_template(TEMPLATE_METHOD_SIGNATURE,
                              method_name=method_name,
                              add_self=False,  # self already included in params if needed
                              parameters=params_str,
                              return_annotation=return_type).strip()

    return signature, typevars


def build_overloaded_method_signatures_from_ast(tree: ast.AST, method_name: str, add_self: bool = True) -> Tuple[str, Set[str]]:
    """Build complete overloaded method signatures from AST for methods with @overload decorators.

    Example:
        ```python
        from chainedpy.services.ast_service import parse_source_code, build_overloaded_method_signatures_from_ast

        source = '''
        from typing import overload

        @overload
        def then_if(self, condition: bool, then: str, otherwise: str) -> Chain[str]: ...

        @overload
        def then_if(self, condition: Callable, then: Callable, otherwise: Callable) -> Chain[Any]: ...

        def then_if(self, condition, then, otherwise):
            pass
        '''

        tree = parse_source_code(source)
        signatures, typevars = build_overloaded_method_signatures_from_ast(tree, "then_if")

        assert "@overload" in signatures
        assert "def then_if(self, condition: bool" in signatures
        assert "def then_if(self, condition: Callable" in signatures
        assert "Chain[str]" in signatures
        assert "Chain[Any]" in signatures
        ```

    :param tree: AST tree to search.
    :type tree: [ast.AST][ast.AST]
    :param method_name: Name of the method.
    :type method_name: [str][str]
    :param add_self: Whether to add 'self' parameter, defaults to True.
    :type add_self: [bool][bool], optional
    :return [Tuple][tuple][[str][str], [Set][set][[str][str]]]: Tuple of (complete overloaded signatures, set of TypeVars used).
    """
    # Find all function definitions with this name
    overloaded_functions = find_overloaded_functions(tree, method_name)

    if len(overloaded_functions) <= 1:
        # No overloads, use regular signature building
        if overloaded_functions:
            return build_method_signature(overloaded_functions[0], method_name, add_self)

        # Function not found - create fallback signature using template
        fallback_signature = render_template(TEMPLATE_METHOD_SIGNATURE,
                                           method_name=method_name,
                                           add_self=True,
                                           parameters="",
                                           return_annotation='"Chain[Any]"').strip()
        return fallback_signature, set()

    # Build signatures for all overloads
    signatures = []
    all_typevars = set()

    for func_node in overloaded_functions:
        signature, typevars = build_method_signature(func_node, method_name, add_self)

        # Add @overload decorator for overloaded functions (except the last one which is the fallback)
        if has_overload_decorator(func_node):
            # Format as single line with @overload prefix using template
            signature = render_template(TEMPLATE_OVERLOAD_SIGNATURE, signature=signature).strip()

        signatures.append(signature)
        all_typevars.update(typevars)

    # Join all signatures with proper spacing
    complete_signature = "\n\n    ".join(signatures)

    return complete_signature, all_typevars


def parse_file_for_functions(file_path: Path, name_prefix: str = "") -> List[ast.FunctionDef]:
    """Parse a Python file and extract function definitions.

    Example:
        ```python
        from chainedpy.services.ast_service import parse_file_for_functions
        from chainedpy.exceptions import ASTServiceError
        from pathlib import Path

        # Create test file
        test_file = Path("test_functions.py")
        test_file.write_text('''
def then_map(self, fn):
    return self._add_link(fn)

def then_filter(self, predicate):
    return self._add_link(predicate)

def as_retry(self, attempts=3):
    return self._wrap(attempts)

def regular_function():
    pass
        ''')

        # Parse all functions
        all_functions = parse_file_for_functions(test_file)
        assert len(all_functions) == 4

        function_names = [f.name for f in all_functions]
        assert "then_map" in function_names
        assert "then_filter" in function_names
        assert "as_retry" in function_names
        assert "regular_function" in function_names

        # Parse only 'then_' functions
        then_functions = parse_file_for_functions(test_file, "then_")
        assert len(then_functions) == 2
        then_names = [f.name for f in then_functions]
        assert "then_map" in then_names
        assert "then_filter" in then_names
        assert "as_retry" not in then_names

        # Error handling for non-existent file
        try:
            parse_file_for_functions(Path("nonexistent.py"))
        except ASTServiceError as e:
            print(f"File error: {e}")

        # Cleanup
        test_file.unlink(missing_ok=True)
        ```

    :param file_path: Path to Python file.
    :type file_path: [Path][pathlib.Path]
    :param name_prefix: Optional prefix to filter function names, defaults to "".
    :type name_prefix: [str][str], optional
    :return [List][list][[ast.FunctionDef][ast.FunctionDef]]: List of AST FunctionDef nodes.
    :raises ASTServiceError: If file parsing fails.
    """
    try:
        source = fs_utils.read_text(str(file_path))

        tree = parse_source_code(source)
        return find_function_definitions(tree, name_prefix)

    except Exception as e:
        raise ASTServiceError(f"Failed to parse file {file_path}: {e}") from e


def parse_remote_source_for_functions(source: str, name_prefix: str = "") -> List[ast.FunctionDef]:
    """Parse remote source code and extract function definitions.

    Example:
        ```python
        from chainedpy.services.ast_service import parse_remote_source_for_functions
        from chainedpy.exceptions import ASTServiceError

        # Remote source with chain methods
        remote_source = '''
        def then_send_email(self, to: str, subject: str) -> Chain[bool]:
            pass

        def then_process_data(self, data: dict) -> Chain[dict]:
            pass

        def as_retry(self, attempts: int = 3) -> Chain[Any]:
            pass
        '''

        # Parse all functions
        all_functions = parse_remote_source_for_functions(remote_source)
        assert len(all_functions) == 3

        function_names = [f.name for f in all_functions]
        assert "then_send_email" in function_names
        assert "then_process_data" in function_names
        assert "as_retry" in function_names

        # Parse only 'then_' functions
        then_functions = parse_remote_source_for_functions(remote_source, "then_")
        assert len(then_functions) == 2
        then_names = [f.name for f in then_functions]
        assert "then_send_email" in then_names
        assert "then_process_data" in then_names
        assert "as_retry" not in then_names

        # Error handling for invalid source
        try:
            parse_remote_source_for_functions("def invalid syntax:")
        except ASTServiceError as e:
            print(f"Parse error: {e}")
        ```

    :param source: Python source code string.
    :type source: [str][str]
    :param name_prefix: Optional prefix to filter function names, defaults to "".
    :type name_prefix: [str][str], optional
    :return [List][list][[ast.FunctionDef][ast.FunctionDef]]: List of AST FunctionDef nodes.
    :raises ASTServiceError: If parsing fails.
    """
    tree = parse_source_code(source)
    return find_function_definitions(tree, name_prefix)

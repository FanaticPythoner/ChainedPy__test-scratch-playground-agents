"""
Test ChainedPy stub generation service functionality.

This module tests stub generation with decorator handling, overloaded method signatures,
and integration with AST service decorator functions. NO exception swallowing.
"""

import pytest
from unittest.mock import Mock # TODO: Strictly use Pytest.

from chainedpy.services.stub_generation_service import (
    StubGenerationError,
    generate_stub_content,
    _discover_base_chainedpy_methods,
    _discover_project_methods_with_ast,
    _extract_plugin_signature,
    _extract_remote_plugin_signature
)

# Use centralized test infrastructure
from tests.services.project_test_service import create_test_project
# from .project_test_service import create_test_project


class TestDecoratorHandlingInStubGeneration:
    """Test decorator handling in stub generation functionality.

    :raises Exception: If decorator handling in stub generation testing fails.
    """

    def test_discover_base_chainedpy_methods_with_overloads(self):
        """Test discovering base chainedpy methods that have @overload decorators.

        :raises AssertionError: If base chainedpy method discovery fails.
        :return None: None
        """
        # @@ STEP 1: Discover base chainedpy methods using AST service integration. @@
        then_methods, as_methods, typevar_imports = _discover_base_chainedpy_methods()

        # @@ STEP 2: Verify we found methods from chainedpy.chain. @@
        assert len(then_methods) > 0
        assert len(as_methods) > 0

        # @@ STEP 3: Check that method discovery works (specific methods may vary). @@
        then_method_names = [method.name for method in then_methods]
        as_method_names = [method.name for method in as_methods]

        # @@ STEP 4: Verify common chain methods are included. @@
        expected_then_methods = ['then_if', 'then_map', 'then_foreach']
        # @@ STEP 5: Verify expected as_ methods are included. @@
        expected_as_methods = ['as_retry', 'as_on_error']

        # || S.S. 4.1: Check each expected then method is present. ||
        for expected in expected_then_methods:
            assert any(expected in name for name in then_method_names), f"Expected then method {expected} not found"

        # || S.S. 5.1: Check each expected as method is present. ||
        for expected in expected_as_methods:
            assert any(expected in name for name in as_method_names), f"Expected as method {expected} not found"

    def test_discover_current_project_methods_with_overloaded_plugins(self, temp_workspace):
        """Test discovering project methods with overloaded plugin signatures.

        :param temp_workspace: Temporary workspace fixture.
        :type temp_workspace: Path
        :raises AssertionError: If project method discovery with overloads fails.
        :return None: None
        """
        # @@ STEP 1: Create project with plugin that has overloaded signatures. @@
        project = create_test_project(temp_workspace, "test_project")

        # @@ STEP 2: Create plugin with overloaded signatures. @@
        plugin_dir = project / "plugins" / "then"
        plugin_dir.mkdir(parents=True, exist_ok=True)

        # || S.S. 2.1: Define plugin content with overloaded signatures. ||
        overloaded_plugin_content = '''
from typing import overload, Union, List, Callable, Awaitable
from chainedpy.link import Link
from chainedpy.register import then
from typing import TypeVar

_T = TypeVar('_T')
_O = TypeVar('_O')

@overload
def then_process(func: Callable[[str], str | Awaitable[str]]) -> Link[str, str]: ...

@overload
def then_process(func: Callable[[int], int | Awaitable[int]]) -> Link[int, int]: ...

@then("process")
def then_process(func: Callable[[_T], _O | Awaitable[_O]]) -> Link[_T, _O]:
    """Process data with overloaded function signatures."""
    class ProcessLink(Link[_T, _O]):
        name = "process"
        async def __call__(self, arg: _T) -> _O:
            result = func(arg)
            return await result if hasattr(result, '__await__') else result
    return ProcessLink()
'''

        # @@ STEP 3: Write plugin file. @@
        plugin_file = plugin_dir / "then_process.py"
        plugin_file.write_text(overloaded_plugin_content, encoding='utf-8')

        # @@ STEP 4: Discover methods - should handle overloaded signatures. @@
        then_methods, as_methods, typevars = _discover_project_methods_with_ast(project, "test_project")

        # @@ STEP 5: Should find the overloaded method. @@
        # || S.S. 5.1: Filter methods by name to find the specific method. ||
        process_methods = [m for m in then_methods if m.name == 'then_process']
        assert len(process_methods) > 0

        # @@ STEP 6: Should contain signature information. @@
        # || S.S. 6.1: Verify the method has signature data. ||
        process_method = process_methods[0]
        assert process_method.signature is not None

    def test_extract_plugin_signature_with_overload_decorators(self, temp_workspace):
        """Test extracting plugin signatures that have @overload decorators.

        :param temp_workspace: Temporary workspace fixture.
        :type temp_workspace: Path
        :raises AssertionError: If plugin signature extraction with overloads fails.
        :return None: None
        """
        # @@ STEP 1: Create temporary plugin file with overloaded signatures. @@
        # || S.S. 1.1: Define plugin content with overloaded method signatures. ||
        plugin_content = '''
from typing import overload, Callable, Awaitable
from chainedpy.link import Link
from chainedpy.register import then
from typing import TypeVar

_T = TypeVar('_T')
_O = TypeVar('_O')

@overload
def then_transform(func: Callable[[str], str | Awaitable[str]]) -> Link[str, str]: ...

@overload
def then_transform(func: Callable[[int], int | Awaitable[int]]) -> Link[int, int]: ...

@then("transform")
def then_transform(func: Callable[[_T], _O | Awaitable[_O]]) -> Link[_T, _O]:
    """Transform data with type-specific functions."""
    class TransformLink(Link[_T, _O]):
        name = "transform"
        async def __call__(self, arg: _T) -> _O:
            result = func(arg)
            return await result if hasattr(result, '__await__') else result
    return TransformLink()
'''

        # || S.S. 1.2: Write plugin content to temporary file. ||
        plugin_file = temp_workspace / "then_transform.py"
        plugin_file.write_text(plugin_content, encoding='utf-8')

        # @@ STEP 2: Extract signature - should handle overloaded methods. @@
        signature = _extract_plugin_signature(plugin_file, "then_transform")

        # @@ STEP 3: Verify signature extraction was successful. @@
        assert signature is not None
        # || S.S. 3.1: Should contain parameter information from one of the overloads. ||
        assert "func:" in signature or "self:" in signature
    def test_extract_remote_plugin_signature_with_decorators(self):
        """Test extracting remote plugin signatures with decorators.

        :raises AssertionError: If remote plugin signature extraction fails.
        :return None: None
        """
        # @@ STEP 1: Mock remote source with overloaded signatures. @@
        # || S.S. 1.1: Define remote plugin content with overloaded method signatures. ||
        remote_source = '''
from typing import overload, Union, Any
from chainedpy.link import Wrapper
from chainedpy.register import as_
from typing import TypeVar

_T = TypeVar('_T')

@overload
def as_cached(ttl: int) -> Wrapper[_T, _T]: ...

@overload
def as_cached(ttl: str) -> Wrapper[_T, _T]: ...

@as_("cached")
def as_cached(ttl: Union[int, str]) -> Wrapper[Any, Any]:
    """Cache with flexible TTL types."""
    class CachedWrapper(Wrapper[Any, Any]):
        def wrap(self, inner):
            return inner  # Simplified implementation
    return CachedWrapper()
'''

        # @@ STEP 2: Mock filesystem for remote access. @@
        # || S.S. 2.1: Create mock filesystem with encoded content. ||
        mock_fs = Mock()
        mock_fs.cat_file.return_value = remote_source.encode('utf-8')

        # @@ STEP 3: Extract signature. @@
        signature = _extract_remote_plugin_signature(
            mock_fs, "remote/path/as_cached.py", "as_cached"
        )

        # @@ STEP 4: Verify signature extraction was successful. @@
        assert signature is not None
        # || S.S. 4.1: Should contain parameter information. ||
        assert "ttl:" in signature or "self:" in signature
    def test_stub_generation_with_overloaded_methods(self, temp_workspace):
        """Test complete stub generation with overloaded method signatures.

        :param temp_workspace: Temporary workspace fixture.
        :type temp_workspace: Path
        :raises AssertionError: If stub generation with overloaded methods fails.
        :return None: None
        """
        # @@ STEP 1: Create project with overloaded plugin. @@
        project = create_test_project(temp_workspace, "test_project")

        # @@ STEP 2: Create plugin with overloaded signatures. @@
        plugin_dir = project / "plugins" / "as_"
        plugin_dir.mkdir(parents=True, exist_ok=True)

        # || S.S. 2.1: Define plugin content with overloaded method signatures. ||
        overloaded_plugin_content = '''
from typing import overload, Union, Any
from chainedpy.link import Wrapper
from chainedpy.register import as_
from typing import TypeVar

_T = TypeVar('_T')

@overload
def as_timeout(seconds: int) -> Wrapper[_T, _T]: ...

@overload
def as_timeout(seconds: float) -> Wrapper[_T, _T]: ...

@as_("timeout")
def as_timeout(seconds: Union[int, float]) -> Wrapper[Any, Any]:
    """Timeout with numeric flexibility."""
    class TimeoutWrapper(Wrapper[Any, Any]):
        def wrap(self, inner):
            return inner  # Simplified implementation
    return TimeoutWrapper()
'''

        # || S.S. 2.2: Write plugin content to file. ||
        plugin_file = plugin_dir / "as_timeout.py"
        plugin_file.write_text(overloaded_plugin_content, encoding='utf-8')

        # @@ STEP 3: Generate stub content. @@
        stub_content = generate_stub_content(project)

        # @@ STEP 4: Verify stub generation was successful. @@
        # || S.S. 4.1: Should contain the method signature. ||
        assert "def as_timeout(" in stub_content
        # || S.S. 4.2: Should handle the overloaded signatures properly. ||
        assert stub_content is not None
        assert len(stub_content) > 0
    
    def test_stub_generation_error_handling_with_broken_decorators(self, temp_workspace):
        """Test error handling when plugin files have broken decorator syntax.

        :param temp_workspace: Temporary workspace fixture.
        :type temp_workspace: Path
        :raises StubGenerationError: If plugin files have broken decorator syntax.
        :return None: None
        """
        # @@ STEP 1: Create project with broken plugin. @@
        project = create_test_project(temp_workspace, "test_project")

        # @@ STEP 2: Create plugin with broken decorator syntax. @@
        plugin_dir = project / "plugins" / "then"
        plugin_dir.mkdir(parents=True, exist_ok=True)

        # || S.S. 2.1: Define broken plugin content with syntax error. ||
        broken_plugin_content = '''
from typing import overload

@overload
def then_broken(self, data: str) -> str: ...

def then_broken(self, data
    # Missing closing parenthesis and colon - this will cause syntax error
'''

        # || S.S. 2.2: Write broken plugin content to file. ||
        plugin_file = plugin_dir / "then_broken.py"
        plugin_file.write_text(broken_plugin_content, encoding='utf-8')

        # @@ STEP 3: Should raise StubGenerationError instead of swallowing exception. @@
        with pytest.raises(StubGenerationError, match="Failed to parse plugin file"):
            generate_stub_content(project)


class TestStubGenerationIntegrationWithASTService:
    """Test integration between stub generation and AST service decorator functions.

    :raises Exception: If integration between stub generation and AST service fails.
    """

    def test_ast_service_decorator_detection_integration(self, temp_workspace):
        """Test that stub generation properly uses AST service decorator detection.

        :param temp_workspace: Temporary workspace fixture.
        :type temp_workspace: Path
        :raises AssertionError: If AST service decorator detection integration fails.
        :return None: None
        """
        # @@ STEP 1: Create project with complex decorator scenarios. @@
        project = create_test_project(temp_workspace, "test_project")

        # @@ STEP 2: Create plugin with mixed decorators. @@
        plugin_dir = project / "plugins" / "then"
        plugin_dir.mkdir(parents=True, exist_ok=True)

        # || S.S. 2.1: Define complex plugin content with mixed decorator scenarios. ||
        complex_plugin_content = '''
from typing import overload, staticmethod, classmethod, Callable, Awaitable, Any
from chainedpy.link import Link
from chainedpy.register import then
from typing import TypeVar

_T = TypeVar('_T')
_O = TypeVar('_O')

@overload
def then_mixed_process(func: Callable[[str], str | Awaitable[str]]) -> Link[str, str]: ...

@overload
def then_mixed_process(func: Callable[[int], int | Awaitable[int]]) -> Link[int, int]: ...

@then("mixed_process")
def then_mixed_process(func: Callable[[_T], _O | Awaitable[_O]]) -> Link[_T, _O]:
    """Method with mixed decorator scenarios."""
    class MixedProcessLink(Link[_T, _O]):
        name = "mixed_process"
        async def __call__(self, arg: _T) -> _O:
            result = func(arg)
            return await result if hasattr(result, '__await__') else result
    return MixedProcessLink()
'''

        # || S.S. 2.2: Write complex plugin content to file. ||
        plugin_file = plugin_dir / "then_mixed_process.py"
        plugin_file.write_text(complex_plugin_content, encoding='utf-8')

        # @@ STEP 3: Generate stub - should handle complex decorator scenarios. @@
        stub_content = generate_stub_content(project)

        # @@ STEP 4: Verify stub generation was successful. @@
        # || S.S. 4.1: Should successfully generate stub without errors. ||
        assert stub_content is not None
        assert len(stub_content) > 0

        # || S.S. 4.2: Should contain method signatures. ||
        assert "def then_" in stub_content
    
    def test_typevar_extraction_with_decorated_methods(self, temp_workspace):
        """Test TypeVar extraction from decorated methods.

        :param temp_workspace: Temporary workspace fixture.
        :type temp_workspace: Path
        :raises AssertionError: If TypeVar extraction from decorated methods fails.
        :return None: None
        """
        # @@ STEP 1: Create project with decorated methods using TypeVars. @@
        project = create_test_project(temp_workspace, "test_project")

        # @@ STEP 2: Create plugin with TypeVars in decorated methods. @@
        plugin_dir = project / "plugins" / "as_"
        plugin_dir.mkdir(parents=True, exist_ok=True)

        # || S.S. 2.1: Define plugin content with complex TypeVar scenarios. ||
        typevar_plugin_content = '''
from typing import overload, TypeVar, Generic, List, Dict, Callable, Any
from chainedpy.link import Wrapper
from chainedpy.register import as_

_T = TypeVar('_T')
_K = TypeVar('_K')
_V = TypeVar('_V')

@overload
def as_mapped(func: Callable[[_T], _K]) -> Wrapper[List[_T], List[_K]]: ...

@overload
def as_mapped(func: Callable[[_V], _T]) -> Wrapper[Dict[_K, _V], Dict[_K, _T]]: ...

@as_("mapped")
def as_mapped(func: Callable[[Any], Any]) -> Wrapper[Any, Any]:
    """Map with complex TypeVar scenarios."""
    class MappedWrapper(Wrapper[Any, Any]):
        def wrap(self, inner):
            return inner  # Simplified implementation
    return MappedWrapper()
'''

        # || S.S. 2.2: Write plugin content to file. ||
        plugin_file = plugin_dir / "as_mapped.py"
        plugin_file.write_text(typevar_plugin_content, encoding='utf-8')

        # @@ STEP 3: Generate stub content. @@
        stub_content = generate_stub_content(project)

        # @@ STEP 4: Verify TypeVar extraction from decorated methods. @@
        # || S.S. 4.1: Should handle TypeVar extraction from decorated methods. ||
        assert stub_content is not None
        assert "def as_mapped(" in stub_content

        # || S.S. 4.2: Should include TypeVar imports. ||
        assert "_T" in stub_content or "_K" in stub_content or "_V" in stub_content


class TestStubGenerationEdgeCases:
    """Test edge cases in stub generation with decorators.

    :raises Exception: If edge case handling in stub generation fails.
    """

    def test_empty_overload_decorators(self, temp_workspace):
        """Test handling of empty @overload decorators.

        :param temp_workspace: Temporary workspace fixture.
        :type temp_workspace: Path
        :raises AssertionError: If empty overload decorator handling fails.
        :return None: None
        """
        # @@ STEP 1: Create test project. @@
        project = create_test_project(temp_workspace, "test_project")

        # @@ STEP 2: Create plugin directory. @@
        plugin_dir = project / "plugins" / "then"
        plugin_dir.mkdir(parents=True, exist_ok=True)

        # @@ STEP 3: Create plugin with empty overload decorators. @@
        # || S.S. 3.1: Define plugin content with empty overload. ||
        empty_overload_content = '''
from typing import overload

@overload
def then_empty(): ...

def then_empty():
    """Empty overload implementation."""
    pass
'''

        # || S.S. 3.2: Write plugin content to file. ||
        plugin_file = plugin_dir / "then_empty.py"
        plugin_file.write_text(empty_overload_content, encoding='utf-8')

        # @@ STEP 4: Should handle empty overloads without errors. @@
        stub_content = generate_stub_content(project)
        assert stub_content is not None
        assert "def then_empty(" in stub_content

    def test_malformed_decorator_syntax(self, temp_workspace):
        """Test handling of malformed decorator syntax.

        :param temp_workspace: Temporary workspace fixture.
        :type temp_workspace: Path
        :raises StubGenerationError: If malformed decorator syntax is encountered.
        :return None: None
        """
        # @@ STEP 1: Create test project. @@
        project = create_test_project(temp_workspace, "test_project")

        # @@ STEP 2: Create plugin directory. @@
        plugin_dir = project / "plugins" / "as_"
        plugin_dir.mkdir(parents=True, exist_ok=True)

        # @@ STEP 3: Create plugin with malformed decorator syntax. @@
        # || S.S. 3.1: Define plugin content with syntax error. ||
        malformed_content = '''
from typing import overload

@overload
def as_malformed(self, data: str) -> str: ...

def as_malformed(self, data
    # Missing closing parenthesis and colon - this will cause syntax error
'''

        # || S.S. 3.2: Write malformed plugin content to file. ||
        plugin_file = plugin_dir / "as_malformed.py"
        plugin_file.write_text(malformed_content, encoding='utf-8')

        # @@ STEP 4: Should raise StubGenerationError for malformed syntax. @@
        with pytest.raises(StubGenerationError):
            generate_stub_content(project)

    def test_nested_decorator_scenarios(self, temp_workspace):
        """Test nested decorator scenarios in class methods.

        :param temp_workspace: Temporary workspace fixture.
        :type temp_workspace: Path
        :raises AssertionError: If nested decorator scenario handling fails.
        :return None: None
        """
        # @@ STEP 1: Create test project. @@
        project = create_test_project(temp_workspace, "test_project")

        # @@ STEP 2: Create plugin directory. @@
        plugin_dir = project / "plugins" / "then"
        plugin_dir.mkdir(parents=True, exist_ok=True)

        # @@ STEP 3: Create plugin with nested decorator scenarios. @@
        # || S.S. 3.1: Define plugin content with nested class and module-level methods. ||
        nested_content = '''
from typing import overload

class NestedPlugin:
    @overload
    def then_nested(self, data: str) -> str: ...

    @overload
    def then_nested(self, data: int) -> int: ...

    def then_nested(self, data):
        return data

# Module-level function with same name
@overload
def then_nested(self, data: list) -> list: ...

def then_nested(self, data):
    return data
'''

        # || S.S. 3.2: Write nested plugin content to file. ||
        plugin_file = plugin_dir / "then_nested.py"
        plugin_file.write_text(nested_content, encoding='utf-8')

        # @@ STEP 4: Should handle nested scenarios properly. @@
        stub_content = generate_stub_content(project)
        assert stub_content is not None
        assert "def then_nested(" in stub_content

    def test_decorator_with_complex_imports(self, temp_workspace):
        """Test decorators with complex import scenarios.

        :param temp_workspace: Temporary workspace fixture.
        :type temp_workspace: Path
        :raises AssertionError: If complex import scenario handling fails.
        :return None: None
        """
        # @@ STEP 1: Create test project. @@
        project = create_test_project(temp_workspace, "test_project")

        # @@ STEP 2: Create plugin directory. @@
        plugin_dir = project / "plugins" / "as_"
        plugin_dir.mkdir(parents=True, exist_ok=True)

        # @@ STEP 3: Create plugin with complex import scenarios. @@
        # || S.S. 3.1: Define plugin content with import aliases. ||
        complex_import_content = '''
from typing import overload as ol, Union as U, List as L
import typing as t
from collections.abc import Callable as C

@ol
def as_complex(self, func: C[[str], str]) -> 'Wrapper[str, str]': ...

@t.overload
def as_complex(self, func: C[[int], int]) -> 'Wrapper[int, int]': ...

def as_complex(self, func):
    """Complex import scenario."""
    return func
'''

        # || S.S. 3.2: Write complex import plugin content to file. ||
        plugin_file = plugin_dir / "as_complex.py"
        plugin_file.write_text(complex_import_content, encoding='utf-8')

        # @@ STEP 4: Should handle complex import aliases. @@
        stub_content = generate_stub_content(project)
        assert stub_content is not None
        assert "def as_complex(" in stub_content

    def test_overload_with_default_parameters(self, temp_workspace):
        """Test @overload decorators with default parameters.

        :param temp_workspace: Temporary workspace fixture.
        :type temp_workspace: Path
        :raises AssertionError: If overload with default parameters handling fails.
        :return None: None
        """
        # @@ STEP 1: Create test project. @@
        project = create_test_project(temp_workspace, "test_project")

        # @@ STEP 2: Create plugin directory. @@
        plugin_dir = project / "plugins" / "then"
        plugin_dir.mkdir(parents=True, exist_ok=True)

        # @@ STEP 3: Create plugin with default parameters in overloads. @@
        # || S.S. 3.1: Define plugin content with default parameters. ||
        default_params_content = '''
from typing import overload, Optional

@overload
def then_with_defaults(self, data: str, *, format: str = "json") -> str: ...

@overload
def then_with_defaults(self, data: int, *, format: Optional[str] = None) -> int: ...

def then_with_defaults(self, data, *, format=None):
    """Method with default parameters in overloads."""
    return data
'''

        # || S.S. 3.2: Write default parameters plugin content to file. ||
        plugin_file = plugin_dir / "then_with_defaults.py"
        plugin_file.write_text(default_params_content, encoding='utf-8')

        # @@ STEP 4: Should handle default parameters in overloaded signatures. @@
        stub_content = generate_stub_content(project)
        assert stub_content is not None
        assert "def then_with_defaults(" in stub_content
        # || S.S. 4.1: Should preserve default parameter information. ||
        assert "format:" in stub_content or "=" in stub_content


class TestStubGenerationErrorRecovery:
    """Test error recovery in stub generation with decorator issues.

    :raises Exception: If error recovery in stub generation fails.
    """

    def test_partial_plugin_failure_recovery(self, temp_workspace):
        """Test recovery when some plugins fail but others succeed.

        :param temp_workspace: Temporary workspace fixture.
        :type temp_workspace: Path
        :raises StubGenerationError: If plugin failure recovery fails.
        :return None: None
        """
        # @@ STEP 1: Create test project. @@
        project = create_test_project(temp_workspace, "test_project")

        # @@ STEP 2: Create plugin directory. @@
        plugin_dir = project / "plugins" / "then"
        plugin_dir.mkdir(parents=True, exist_ok=True)

        # @@ STEP 3: Create valid plugin. @@
        # || S.S. 3.1: Define valid plugin content. ||
        valid_content = '''
def then_valid(self, data):
    """Valid plugin."""
    return data
'''
        # || S.S. 3.2: Write valid plugin to file. ||
        valid_file = plugin_dir / "then_valid.py"
        valid_file.write_text(valid_content, encoding='utf-8')

        # @@ STEP 4: Create invalid plugin. @@
        # || S.S. 4.1: Define invalid plugin content with syntax error. ||
        invalid_content = '''
from typing import overload

@overload
def then_invalid(self, data: str) -> str: ...

def then_invalid(self, data
    # Missing closing parenthesis and colon - this will cause syntax error
'''
        # || S.S. 4.2: Write invalid plugin to file. ||
        invalid_file = plugin_dir / "then_invalid.py"
        invalid_file.write_text(invalid_content, encoding='utf-8')

        # @@ STEP 5: Should fail completely rather than partial recovery. @@
        # No exception swallowing allowed.
        with pytest.raises(StubGenerationError):
            generate_stub_content(project)

    def test_circular_import_in_decorated_plugins(self, temp_workspace):
        """Test handling of circular imports in decorated plugins.

        :param temp_workspace: Temporary workspace fixture.
        :type temp_workspace: Path
        :raises StubGenerationError: If circular import handling fails.
        :return None: None
        """
        # @@ STEP 1: Create test project. @@
        project = create_test_project(temp_workspace, "test_project")

        # @@ STEP 2: Create plugin directory. @@
        plugin_dir = project / "plugins" / "as_"
        plugin_dir.mkdir(parents=True, exist_ok=True)

        # @@ STEP 3: Create plugin that might cause circular import issues. @@
        # || S.S. 3.1: Define plugin content with potential circular import. ||
        circular_content = '''
from typing import overload, Any
from chainedpy.link import Wrapper
from chainedpy.register import as_
# This could potentially cause circular import issues
from chainedpy.chain import Chain

@overload
def as_circular(data: str) -> Wrapper[Any, Any]: ...

@as_("circular")
def as_circular(data: Any) -> Wrapper[Any, Any]:
    """Plugin with potential circular import."""
    class CircularWrapper(Wrapper[Any, Any]):
        def wrap(self, inner):
            return inner  # Simplified implementation
    return CircularWrapper()
'''

        # || S.S. 3.2: Write circular import plugin content to file. ||
        plugin_file = plugin_dir / "as_circular.py"
        plugin_file.write_text(circular_content, encoding='utf-8')

        # @@ STEP 4: Should handle or fail gracefully (no silent failures). @@
        try:
            stub_content = generate_stub_content(project)
            # || S.S. 4.1: If successful, should contain the method. ||
            assert "def as_circular(" in stub_content
        except StubGenerationError:
            # || S.S. 4.2: If it fails, it should fail explicitly, not silently. ||
            pass  # This is acceptable - explicit failure is better than silent failure

    def test_unicode_in_decorated_plugin_docstrings(self, temp_workspace):
        """Test handling of Unicode characters in decorated plugin docstrings.

        :param temp_workspace: Temporary workspace fixture.
        :type temp_workspace: Path
        :raises AssertionError: If Unicode character handling fails.
        :return None: None
        """
        # @@ STEP 1: Create test project. @@
        project = create_test_project(temp_workspace, "test_project")

        # @@ STEP 2: Create plugin directory. @@
        plugin_dir = project / "plugins" / "then"
        plugin_dir.mkdir(parents=True, exist_ok=True)

        # @@ STEP 3: Create plugin with Unicode characters in docstrings. @@
        # || S.S. 3.1: Define plugin content with Unicode characters. ||
        unicode_content = '''
from typing import overload

@overload
def then_unicode(self, data: str) -> str: ...

def then_unicode(self, data):
    """Process with Unicode: 🚀 ñáéíóú αβγ 中文 русский."""
    return data
'''

        # || S.S. 3.2: Write Unicode plugin content to file. ||
        plugin_file = plugin_dir / "then_unicode.py"
        plugin_file.write_text(unicode_content, encoding='utf-8')

        # @@ STEP 4: Should handle Unicode characters properly. @@
        stub_content = generate_stub_content(project)
        assert stub_content is not None
        assert "def then_unicode(" in stub_content

"""Stub Generation Service.

This service handles .pyi stub file generation for ChainedPy projects. It provides
comprehensive functionality for analyzing chain methods, extracting type information,
and generating type-safe stub files that enable proper IDE support and static
type checking for ChainedPy projects.

The service analyzes both local and remote chain projects, discovers available
methods through AST parsing, extracts type signatures, and generates comprehensive
stub files with proper type annotations. It handles complex inheritance chains
and ensures all available methods are properly typed.

Note:
    This service was extracted from project.py to centralize stub generation
    functionality and maintain clean separation between project management
    and type stub generation concerns.

Example:
    ```python
    from chainedpy.services.stub_generation_service import (
        generate_project_stub, discover_chain_methods, update_project_stub
    )
    from pathlib import Path

    # Generate stub file for a project
    project_path = Path("./my_project")
    stub_content = generate_project_stub(project_path)

    # Discover available chain methods
    methods = discover_chain_methods(project_path)
    for method_name, signature in methods.items():
        print(f"{method_name}: {signature}")

    # Update existing stub file
    success = update_project_stub(project_path)
    if success:
        print("Stub file updated successfully")

    # Generate stub with custom configuration
    stub_content = generate_project_stub(
        project_path,
        include_base_methods=True,
        include_remote_methods=True
    )
    ```

See Also:
    - [generate_project_stub][chainedpy.services.stub_generation_service.generate_project_stub]: Generate complete stub files
    - [discover_chain_methods][chainedpy.services.stub_generation_service.discover_chain_methods]: Discover available methods
    - [chainedpy.services.ast_service][chainedpy.services.ast_service]: AST analysis for method discovery
    - [chainedpy.services.template_service][chainedpy.services.template_service]: Template rendering for stub files
"""
from __future__ import annotations

# 1. Standard library imports
import inspect
from pathlib import Path
from typing import Sequence, List, Dict, NamedTuple
from urllib.parse import urlparse

# 2. Third-party imports
import chainedpy.chain

# 3. Internal constants
from chainedpy.constants import (
    # File names and extensions
    CONFIG_FILE_NAME, PYI_FILE_SUFFIX, PYTHON_EXTENSION, CHAIN_FILE_SUFFIX,
    # Directory structure
    PLUGINS_THEN_PATH, PLUGINS_AS_PATH, PLUGINS_DIR, THEN_DIR, AS_DIR,
    # Default values
    DEFAULT_BASE_PROJECT, DEFAULT_SUMMARY_FORMAT, PLUGIN_PREFIX_THEN, PLUGIN_PREFIX_AS, PLUGIN_TYPE_THEN, PLUGIN_TYPE_AS, CONFIG_KEY_BASE_PROJECT, CONFIG_KEY_SUMMARY,
    # URL handling
    URL_SCHEME_SEPARATOR,
    # Template constants
    TEMPLATE_BASE_IMPORT_CHAINEDPY, TEMPLATE_BASE_IMPORT_REMOTE, TEMPLATE_BASE_IMPORT_CUSTOM,
    # Stub generation message constants
    MSG_STUB_DISCOVERED_BASE_METHODS, MSG_STUB_DISCOVERED_PROJECT_METHODS,
    MSG_STUB_DISCOVERED_PLUGINS, MSG_STUB_TOTAL_PLUGINS, MSG_STUB_ADDED_BASE_METHODS,
    MSG_STUB_ORGANIZED_METHODS, MSG_STUB_FAILED_DISCOVER_BASE, MSG_STUB_READ_CONFIG_DEFAULT,
    MSG_STUB_READ_CONFIG, MSG_STUB_USING_BASE_IMPORT
)

# 4. ChainedPy services
from chainedpy.services import filesystem_service as fs_utils
from chainedpy.services.ast_service import (
    parse_source_code, find_function_definitions, find_typevar_definitions, build_method_signature,
    parse_file_for_functions, parse_remote_source_for_functions, ASTServiceError
)
from chainedpy.services.chain_traversal_service import (
    traverse_project_chain, ChainTraversalError, _get_filesystem, _load_env_credentials
)
from chainedpy.services.logging_service import get_logger
from chainedpy.services.project_lifecycle import read_project_config
from chainedpy.services.template_service import render_stub_file, render_template, TemplateServiceError

# 5. ChainedPy internal modules
from chainedpy.exceptions import StubGenerationError
from chainedpy.models import ProjectConfig

# 6. TYPE_CHECKING imports (none)


class PluginInfo(NamedTuple):
    """Information about a plugin in the chain hierarchy."""
    name: str
    signature: str | None
    project_name: str
    project_path: str
    is_remote: bool


class HierarchicalPlugins(NamedTuple):
    """Hierarchical plugin information for stub generation."""
    then_plugins: List[PluginInfo]
    as_plugins: List[PluginInfo]
    all_then_names: List[str]
    all_as_names: List[str]
    then_methods: List[str]
    as_methods: List[str]
    # Organized method lists for better stub organization
    base_then_methods: List[str]
    base_as_methods: List[str]
    hierarchy_then_methods: List[str]
    hierarchy_as_methods: List[str]
    current_then_methods: List[str]
    current_as_methods: List[str]
    all_typevar_imports: dict[str, str]  # typevar_name -> import_statement


def _list_plugin_names(folder: Path, prefix: str) -> Sequence[str]:
    """List plugin names in a folder with given prefix.

    Example:
        ```python
        from chainedpy.services.stub_generation_service import _list_plugin_names
        from pathlib import Path
        import shutil

        # Create test plugin directory
        plugin_dir = Path("test_plugins")
        plugin_dir.mkdir(exist_ok=True)

        # Create test plugin files
        (plugin_dir / "then_send_email.py").write_text("def then_send_email(): pass")
        (plugin_dir / "then_process_data.py").write_text("def then_process_data(): pass")
        (plugin_dir / "as_retry.py").write_text("def as_retry(): pass")
        (plugin_dir / "other_file.py").write_text("def other(): pass")

        # List 'then_' plugins
        then_plugins = _list_plugin_names(plugin_dir, "then_")
        assert "send_email" in then_plugins
        assert "process_data" in then_plugins
        assert "retry" not in then_plugins

        # List 'as_' plugins
        as_plugins = _list_plugin_names(plugin_dir, "as_")
        assert "retry" in as_plugins
        assert "send_email" not in as_plugins

        # No matches for non-existent prefix
        no_plugins = _list_plugin_names(plugin_dir, "nonexistent_")
        assert len(no_plugins) == 0

        # Cleanup
        shutil.rmtree(plugin_dir, ignore_errors=True)
        ```

    :param folder: Folder path to search for plugins.
    :type folder: [Path][pathlib.Path]
    :param prefix: Prefix to filter plugin files.
    :type prefix: [str][str]
    :return [Sequence][typing.Sequence][[str][str]]: List of plugin names.
    """
    # @@ STEP 1: Create search pattern for plugin files. @@
    pattern = str(folder / f"{prefix}*.py")
    matching_files = fs_utils.glob(pattern)

    # @@ STEP 2: Extract plugin names from matching files. @@
    plugin_names = []
    for file_path in matching_files:
        file_name = Path(file_path).name
        if not file_name.startswith("_"):
            plugin_names.append(Path(file_path).stem)
    return sorted(plugin_names)


def _list_remote_plugin_names(fs, folder_path: str, prefix: str) -> List[str]:
    """List plugin names in a remote folder with given prefix.

    Example:
        ```python
        from chainedpy.services.stub_generation_service import _list_remote_plugin_names
        from chainedpy.services.filesystem_service import get_filesystem
        from chainedpy.exceptions import StubGenerationError

        # Get filesystem for remote access
        fs, _ = get_filesystem("https://raw.githubusercontent.com/user/repo/main/")

        # List remote 'then_' plugins
        try:
            then_plugins = _list_remote_plugin_names(
                fs,
                "https://raw.githubusercontent.com/user/repo/main/plugins/then/",
                "then_"
            )

            for plugin_name in then_plugins:
                assert isinstance(plugin_name, str)
                assert not plugin_name.startswith("then_")  # Prefix is stripped

        except StubGenerationError as e:
            print(f"Remote listing failed: {e}")

        # List remote 'as_' plugins
        try:
            as_plugins = _list_remote_plugin_names(
                fs,
                "https://raw.githubusercontent.com/user/repo/main/plugins/as_/",
                "as_"
            )

            assert isinstance(as_plugins, list)

        except StubGenerationError as e:
            print(f"Remote listing failed: {e}")
        ```

    :param fs: Filesystem object for remote access.
    :type fs: [Any][typing.Any]
    :param folder_path: Remote folder path to search.
    :type folder_path: [str][str]
    :param prefix: Prefix to filter plugin files.
    :type prefix: [str][str]
    :return [List][list][[str][str]]: List of plugin names.
    :raises StubGenerationError: If listing remote plugins fails.
    """
    try:
        # @@ STEP 1: Check if the remote folder exists. @@
        get_logger().debug(f"Checking if remote folder exists: {folder_path}")
        if not fs.exists(folder_path):
            get_logger().debug(f"Remote folder does not exist: {folder_path}")
            return []

        # @@ STEP 2: List files in the remote folder. @@
        get_logger().debug(f"Listing files in remote folder: {folder_path}")
        files = fs.ls(folder_path, detail=False)
        get_logger().debug(f"Found files in remote folder: {files}")
        plugin_names = []

        # @@ STEP 3: Extract plugin names from matching files. @@
        for file_path in files:
            file_name = Path(file_path).name
            get_logger().debug(f"Checking file: {file_name} with prefix: {prefix}")
            if (file_name.startswith(prefix) and
                file_name.endswith(".py") and
                not file_name.startswith("_")):
                # Extract plugin name (remove prefix and .py extension).
                plugin_name = file_name[:-3]  # Remove .py
                plugin_names.append(plugin_name)
                get_logger().debug(f"Added plugin: {plugin_name}")

        get_logger().debug(f"Final plugin names: {sorted(plugin_names)}")
        return sorted(plugin_names)
    except Exception as e:
        msg = f"Failed to list remote plugins from {folder_path}: {e}"
        raise StubGenerationError(msg) from e


def _extract_remote_plugin_signature(fs, plugin_file_path: str, function_name: str) -> str | None:
    """Extract the actual function signature from a remote plugin file using AST service.

    Example:
        ```python
        from chainedpy.services.stub_generation_service import _extract_remote_plugin_signature
        from chainedpy.services.filesystem_service import get_filesystem
        from chainedpy.exceptions import StubGenerationError

        # Get filesystem for remote access
        fs, _ = get_filesystem("https://raw.githubusercontent.com/user/repo/main/")

        # Extract signature from remote plugin
        try:
            signature = _extract_remote_plugin_signature(
                fs,
                "https://raw.githubusercontent.com/user/repo/main/plugins/then/then_send_email.py",
                "then_send_email"
            )

            if signature:
                assert "def then_send_email" in signature
                assert "Chain[" in signature
                print(f"Found signature: {signature}")
            else:
                print("Function not found in remote file")

        except StubGenerationError as e:
            print(f"Signature extraction failed: {e}")

        # Extract non-existent function
        try:
            signature = _extract_remote_plugin_signature(
                fs,
                "https://raw.githubusercontent.com/user/repo/main/plugins/then/then_send_email.py",
                "nonexistent_function"
            )
            assert signature is None

        except StubGenerationError as e:
            print(f"Expected failure: {e}")
        ```

    :param fs: Filesystem object for remote access.
    :type fs: [Any][typing.Any]
    :param plugin_file_path: Remote path to plugin file.
    :type plugin_file_path: [str][str]
    :param function_name: Name of function to extract signature for.
    :type function_name: [str][str]
    :return [str][str] | [None][None]: Function signature or None if not found.
    :raises StubGenerationError: If extraction fails.
    """
    try:
        # @@ STEP 1: Read remote plugin file. @@
        source = fs.cat_file(plugin_file_path).decode('utf-8')

        # @@ STEP 2: Find function definitions using AST service. @@
        functions = parse_remote_source_for_functions(source, function_name)

        # @@ STEP 3: Extract signature for matching function. @@
        for func_node in functions:
            if func_node.name == function_name:
                # Build method signature using AST service.
                signature, _ = build_method_signature(func_node, function_name, add_self=False)
                # Extract just the parameters and return type part.
                if signature.startswith("def ") and "(" in signature and ") ->" in signature:
                    start = signature.find("(")
                    end = signature.rfind(": ...")
                    if start != -1 and end != -1:
                        return signature[start:end]
                return signature

        msg = f"Function {function_name} not found in remote file {plugin_file_path}"
        raise StubGenerationError(msg)

    except ASTServiceError as e:
        msg = f"AST parsing failed for remote {plugin_file_path} function {function_name}: {e}"
        raise StubGenerationError(msg) from e
    except Exception as e:
        msg = f"Failed to extract signature from remote {plugin_file_path} for function {function_name}: {e}"
        raise StubGenerationError(msg) from e


def _discover_project_plugins(project_info, credentials: Dict[str, str] = None) -> tuple[List[PluginInfo], List[PluginInfo]]:
    """Discover plugins from a single project in the chain.

    :param project_info: ProjectInfo from chain traversal.
    :type project_info: Any
    :param credentials: Optional credentials for remote access, defaults to None.
    :type credentials: Dict[str, str], optional
    :return tuple[List[PluginInfo], List[PluginInfo]]: Tuple of (then_plugins, as_plugins) lists.
    """
    # @@ STEP 1: Initialize plugin lists. @@
    then_plugins = []
    as_plugins = []

    try:
        # @@ STEP 2: Handle remote or local project. @@
        if project_info.is_remote:
            # || S.S. 2.1: Handle remote project. ||
            fs, _ = _get_filesystem(project_info.path, credentials)

            # || S.S. 2.2: Discover then_ plugins. ||
            then_folder = f"{project_info.path.rstrip('/')}/{PLUGINS_THEN_PATH}"
            get_logger().debug(f"Looking for then_ plugins in remote folder: {then_folder}")
            then_names = _list_remote_plugin_names(fs, then_folder, PLUGIN_PREFIX_THEN)
            get_logger().debug(f"Found then_ plugin names: {then_names}")

            for name in then_names:
                plugin_file_path = f"{then_folder}/{name}{PYTHON_EXTENSION}"
                signature = _extract_remote_plugin_signature(fs, plugin_file_path, name)
                then_plugins.append(PluginInfo(
                    name=name,
                    signature=signature,
                    project_name=project_info.name,
                    project_path=project_info.path,
                    is_remote=True
                ))

            # || S.S. 2.3: Discover as_ plugins. ||
            as_folder = f"{project_info.path.rstrip('/')}/{PLUGINS_AS_PATH}"
            as_names = _list_remote_plugin_names(fs, as_folder, PLUGIN_PREFIX_AS)

            for name in as_names:
                plugin_file_path = f"{as_folder}/{name}{PYTHON_EXTENSION}"
                signature = _extract_remote_plugin_signature(fs, plugin_file_path, name)
                as_plugins.append(PluginInfo(
                    name=name,
                    signature=signature,
                    project_name=project_info.name,
                    project_path=project_info.path,
                    is_remote=True
                ))
        else:
            # || S.S. 2.4: Handle local project. ||
            project_path = Path(project_info.path)

            # || S.S. 2.5: Discover then_ plugins. ||
            then_folder = project_path / PLUGINS_THEN_PATH
            if then_folder.exists():
                then_names = _list_plugin_names(then_folder, PLUGIN_PREFIX_THEN)

                for name in then_names:
                    plugin_file = then_folder / f"{name}{PYTHON_EXTENSION}"
                    signature = _extract_plugin_signature(plugin_file, name)
                    then_plugins.append(PluginInfo(
                        name=name,
                        signature=signature,
                        project_name=project_info.name,
                        project_path=project_info.path,
                        is_remote=False
                    ))

            # || S.S. 2.6: Discover as_ plugins. ||
            as_folder = project_path / PLUGINS_AS_PATH
            if as_folder.exists():
                as_names = _list_plugin_names(as_folder, PLUGIN_PREFIX_AS)

                for name in as_names:
                    plugin_file = as_folder / f"{name}{PYTHON_EXTENSION}"
                    signature = _extract_plugin_signature(plugin_file, name)
                    as_plugins.append(PluginInfo(
                        name=name,
                        signature=signature,
                        project_name=project_info.name,
                        project_path=project_info.path,
                        is_remote=False
                    ))

    except Exception as e:
        raise StubGenerationError(f"Failed to discover plugins from project {project_info.name} at {project_info.path}: {e}") from e

    # @@ STEP 3: Return discovered plugins. @@
    return then_plugins, as_plugins


def _discover_base_chainedpy_methods() -> tuple[list[PluginInfo], list[PluginInfo], dict[str, str]]:
    """Discover base chainedpy methods using AST parsing of the chainedpy.chain module.

    :return tuple[list[PluginInfo], list[PluginInfo], dict[str, str]]: Tuple of (then_plugins, as_plugins, typevar_imports) containing base chainedpy methods and TypeVar imports.
    :raises StubGenerationError: If AST parsing fails.
    """
    try:
        # Get the path to chainedpy.chain module
        chain_module_path = Path(inspect.getfile(chainedpy.chain))

        # Read and parse the chain module using AST service
        chain_source = fs_utils.read_text(str(chain_module_path))

        tree = parse_source_code(chain_source)

        then_plugins = []
        as_plugins = []
        typevar_imports = {}  # typevar_name -> import_statement

        # Find TypeVar definitions in chainedpy.chain using AST service
        defined_typevars = find_typevar_definitions(tree, "chainedpy.chain")
        typevar_imports.update(defined_typevars)

        # Find all function definitions using AST service
        all_functions = find_function_definitions(tree)

        for func_node in all_functions:
            method_name = func_node.name

            # Check if it's a then_ or as_ method
            if method_name.startswith(PLUGIN_PREFIX_THEN) or method_name.startswith(PLUGIN_PREFIX_AS):
                # Extract method signature using AST service
                signature, method_typevars = build_method_signature(func_node, method_name, add_self=True)

                plugin_info = PluginInfo(
                    name=method_name,
                    signature=signature,
                    project_name=DEFAULT_BASE_PROJECT,
                    project_path=DEFAULT_BASE_PROJECT,
                    is_remote=False
                )

                if method_name.startswith(PLUGIN_PREFIX_THEN):
                    then_plugins.append(plugin_info)
                else:
                    as_plugins.append(plugin_info)

        get_logger().debug(MSG_STUB_DISCOVERED_BASE_METHODS.format(
            len(then_plugins), PLUGIN_TYPE_THEN, len(as_plugins), PLUGIN_TYPE_AS, DEFAULT_BASE_PROJECT
        ))
        get_logger().debug(f"Found TypeVar imports: {list(typevar_imports.keys())}")
        return then_plugins, as_plugins, typevar_imports

    except Exception as e:
        msg = MSG_STUB_FAILED_DISCOVER_BASE.format(DEFAULT_BASE_PROJECT, e)
        raise StubGenerationError(msg) from e


def _discover_project_methods_with_ast(project_path: Path | str, project_name: str, is_remote: bool = False) -> tuple[list[PluginInfo], list[PluginInfo], dict[str, str]]:
    """
    Discover project methods using AST parsing for maximum reusability.

    Args:
        project_path: Path to the project (URL for remote, local path for local)
        project_name: Name of the project
        is_remote: Whether the project is remote

    Returns:
        Tuple of (then_plugins, as_plugins, typevar_imports) containing discovered methods and TypeVar imports
    """
    then_plugins = []
    as_plugins = []
    typevar_imports = {}

    try:
        if is_remote:
            # For remote projects, use fsspec to read the chain file directly
            # Get credentials for remote access
            credentials = _load_env_credentials()

            # Get filesystem for remote access
            fs, _ = _get_filesystem(project_path, credentials)

            # Construct remote chain file path
            chain_file_path = f"{project_path.rstrip('/')}/{project_name}{CHAIN_FILE_SUFFIX}"

            # Check if remote chain file exists
            if not fs.exists(chain_file_path):
                get_logger().debug(f"No remote chain file found at {chain_file_path}")
                return then_plugins, as_plugins, typevar_imports

            # Read remote chain file content
            chain_source = fs.cat_file(chain_file_path).decode('utf-8')
            get_logger().debug(f"Successfully read remote chain file from {chain_file_path}")
            get_logger().debug(f"Remote chain file content preview: {chain_source[:500]}...")
        else:
            # For local projects, read from local filesystem
            actual_project_path = Path(project_path)
            chain_file = actual_project_path / f"{project_name}_chain.py"
            if not chain_file.exists():
                get_logger().debug(f"No chain file found at {chain_file}")
                return then_plugins, as_plugins, typevar_imports

            # Read local chain file
            chain_source = fs_utils.read_text(str(chain_file))

        # Parse the chain file content using AST service
        tree = parse_source_code(chain_source)

        # Find TypeVar definitions in project chain using AST service
        chain_module_suffix = CHAIN_FILE_SUFFIX.replace(PYTHON_EXTENSION, '')
        module_name = f"{project_name}.{project_name}{chain_module_suffix}"
        defined_typevars = find_typevar_definitions(tree, module_name)
        typevar_imports.update(defined_typevars)

        # Find all function definitions using AST service
        all_functions = find_function_definitions(tree)

        for func_node in all_functions:
            method_name = func_node.name

            # Check if it's a then_ or as_ method
            if method_name.startswith(PLUGIN_PREFIX_THEN) or method_name.startswith(PLUGIN_PREFIX_AS):
                # Extract method signature using AST service
                signature, method_typevars = build_method_signature(func_node, method_name, add_self=True)

                get_logger().debug(f"Found {method_name} method in {project_name} with signature: {signature}")

                plugin_info = PluginInfo(
                    name=method_name,
                    signature=signature,
                    project_name=project_name,
                    project_path=str(project_path),  # Keep original path for reference
                    is_remote=is_remote
                )

                if method_name.startswith(PLUGIN_PREFIX_THEN):
                    then_plugins.append(plugin_info)
                else:
                    as_plugins.append(plugin_info)

        plugins_dir = actual_project_path / PLUGINS_DIR
        if plugins_dir.exists():
            # Scan then_ plugins
            then_plugins_dir = plugins_dir / THEN_DIR
            if then_plugins_dir.exists():
                pattern = str(then_plugins_dir / f"{PLUGIN_PREFIX_THEN}*{PYTHON_EXTENSION}")
                matching_files = fs_utils.glob(pattern)
                for file_path in matching_files:
                    plugin_file = Path(file_path)
                    if plugin_file.name.startswith("_"):
                        continue

                    try:
                        # Use AST service for plugin file parsing
                        # Find function definitions using AST service
                        functions = parse_file_for_functions(plugin_file, PLUGIN_PREFIX_THEN)

                        for func_node in functions:
                            if func_node.name.startswith(PLUGIN_PREFIX_THEN):
                                signature, method_typevars = build_method_signature(func_node, func_node.name, add_self=True)

                                get_logger().debug(f"Found {func_node.name} plugin in {plugin_file.name} with signature: {signature}")

                                plugin_info = PluginInfo(
                                    name=func_node.name,
                                    signature=signature,
                                    project_name=project_name,
                                    project_path=str(project_path),
                                    is_remote=is_remote
                                )
                                then_plugins.append(plugin_info)
                    except Exception as e:
                        # No silent failures - raise proper error
                        msg = f"Failed to parse plugin file {plugin_file}: {e}"
                        raise StubGenerationError(msg) from e

            # Scan as_ plugins
            as_plugins_dir = plugins_dir / AS_DIR
            if as_plugins_dir.exists():
                pattern = str(as_plugins_dir / f"{PLUGIN_PREFIX_AS}*{PYTHON_EXTENSION}")
                matching_files = fs_utils.glob(pattern)
                for file_path in matching_files:
                    plugin_file = Path(file_path)
                    if plugin_file.name.startswith("_"):
                        continue

                    try:
                        # Use AST service for plugin file parsing
                        # Find function definitions using AST service
                        functions = parse_file_for_functions(plugin_file, PLUGIN_PREFIX_AS)

                        for func_node in functions:
                            if func_node.name.startswith(PLUGIN_PREFIX_AS):
                                signature, method_typevars = build_method_signature(func_node, func_node.name, add_self=True)

                                get_logger().debug(f"Found {func_node.name} plugin in {plugin_file.name} with signature: {signature}")

                                plugin_info = PluginInfo(
                                    name=func_node.name,
                                    signature=signature,
                                    project_name=project_name,
                                    project_path=str(project_path),
                                    is_remote=is_remote
                                )
                                as_plugins.append(plugin_info)
                    except Exception as e:
                        # No silent failures - raise proper error
                        msg = f"Failed to parse plugin file {plugin_file}: {e}"
                        raise StubGenerationError(msg) from e

        get_logger().debug(MSG_STUB_DISCOVERED_PROJECT_METHODS.format(
            len(then_plugins), PLUGIN_TYPE_THEN, len(as_plugins), PLUGIN_TYPE_AS, project_name
        ))
        if typevar_imports:
            get_logger().debug(f"Found TypeVar imports from {project_name}: {list(typevar_imports.keys())}")

        return then_plugins, as_plugins, typevar_imports

    except Exception as e:
        msg = f"Failed to discover methods from {project_name} using AST: {e}"
        raise StubGenerationError(msg) from e


def _discover_hierarchical_plugins(project_path: Path | str) -> HierarchicalPlugins:
    """
    Discover all plugins in the project chain hierarchy, including base chainedpy methods.

    Args:
        project_path: Path to the starting project

    Returns:
        HierarchicalPlugins containing all discovered plugins from entire hierarchy

    Raises:
        StubGenerationError: If plugin discovery fails
    """
    try:
        # Load credentials for remote access
        credentials = _load_env_credentials()

        # Use the existing chain traversal service to get the full hierarchy

        all_then_plugins = []
        all_as_plugins = []
        all_typevar_imports = {}  # typevar_name -> import_statement

        # Traverse the project chain to get all projects in hierarchy
        chain = traverse_project_chain(str(project_path))
        get_logger().debug(f"Discovered {len(chain)} projects in chain hierarchy")

        # Discover plugins from each project in the chain using AST (excluding chainedpy itself)
        for project_info in chain:
            if project_info.name == "chainedpy":
                continue  # Skip chainedpy - we'll add its methods separately via AST

            get_logger().debug(f"Discovering plugins from {project_info.name} ({'remote' if project_info.is_remote else 'local'}) using AST")

            if project_info.is_remote:
                # For remote projects, first check if they've been downloaded locally
                current_project_path = Path(str(project_path))
                local_remote_chain_path = current_project_path / project_info.name

                if local_remote_chain_path.exists() and local_remote_chain_path.is_dir():
                    # Use local downloaded version with AST discovery
                    get_logger().debug(f"Found local downloaded version of remote chain {project_info.name} at {local_remote_chain_path}")
                    then_plugins, as_plugins, project_typevar_imports = _discover_project_methods_with_ast(
                        str(local_remote_chain_path), project_info.name, is_remote=False  # Treat as local
                    )
                else:
                    # Fall back to remote discovery
                    get_logger().debug(f"No local version found for remote chain {project_info.name}, using remote discovery")
                    then_plugins, as_plugins = _discover_project_plugins(project_info, credentials)
                    project_typevar_imports = {}  # Remote projects don't contribute TypeVars for now
            else:
                # For local projects, use AST-based discovery
                then_plugins, as_plugins, project_typevar_imports = _discover_project_methods_with_ast(
                    project_info.path, project_info.name, project_info.is_remote
                )
            all_then_plugins.extend(then_plugins)
            all_as_plugins.extend(as_plugins)
            all_typevar_imports.update(project_typevar_imports)

            get_logger().debug(MSG_STUB_DISCOVERED_PLUGINS.format(
                len(then_plugins), PLUGIN_TYPE_THEN, len(as_plugins), PLUGIN_TYPE_AS, project_info.name
            ))
            if project_typevar_imports:
                get_logger().debug(f"TypeVar imports from {project_info.name}: {list(project_typevar_imports.keys())}")

        get_logger().debug(MSG_STUB_TOTAL_PLUGINS.format(
            len(all_then_plugins), PLUGIN_TYPE_THEN, len(all_as_plugins), PLUGIN_TYPE_AS
        ))

        base_then_plugins, base_as_plugins, base_typevar_imports = _discover_base_chainedpy_methods()
        all_typevar_imports.update(base_typevar_imports)

        all_then_plugins.extend(base_then_plugins)
        all_as_plugins.extend(base_as_plugins)
        get_logger().debug(MSG_STUB_ADDED_BASE_METHODS.format(
            len(base_then_plugins), PLUGIN_TYPE_THEN, len(base_as_plugins), PLUGIN_TYPE_AS, DEFAULT_BASE_PROJECT
        ))
        get_logger().debug(f"Total TypeVar imports collected: {list(all_typevar_imports.keys())}")

        # Extract unique plugin names (in case of overrides, keep the first occurrence)
        seen_then_names = set()
        seen_as_names = set()
        unique_then_plugins = []
        unique_as_plugins = []

        for plugin in all_then_plugins:
            if plugin.name not in seen_then_names:
                unique_then_plugins.append(plugin)
                seen_then_names.add(plugin.name)

        for plugin in all_as_plugins:
            if plugin.name not in seen_as_names:
                unique_as_plugins.append(plugin)
                seen_as_names.add(plugin.name)

        current_project_name = Path(project_path).name

        # Separate plugins by their source
        base_then_plugins = []
        base_as_plugins = []
        hierarchy_then_plugins = []
        hierarchy_as_plugins = []
        current_then_plugins = []
        current_as_plugins = []

        for plugin in unique_then_plugins:
            if plugin.project_name == DEFAULT_BASE_PROJECT:
                base_then_plugins.append(plugin)
            elif plugin.project_name == current_project_name:
                current_then_plugins.append(plugin)
            else:
                hierarchy_then_plugins.append(plugin)

        for plugin in unique_as_plugins:
            if plugin.project_name == DEFAULT_BASE_PROJECT:
                base_as_plugins.append(plugin)
            elif plugin.project_name == current_project_name:
                current_as_plugins.append(plugin)
            else:
                hierarchy_as_plugins.append(plugin)

        def generate_method_signatures(plugins):
            methods = []
            for plugin in plugins:
                # Add comment indicating source chain
                source_comment = f"    # from {plugin.project_name}"

                if plugin.signature:
                    # Use the signature directly if it's already a complete method definition
                    if plugin.signature.startswith("def "):
                        method_def = f"    {plugin.signature}"
                        methods.append(f"{source_comment}\n{method_def}")
                    else:
                        # Parse signature: "(param1: Type1, param2: Type2) -> ReturnType"
                        if " -> " in plugin.signature:
                            params_part = plugin.signature.split(" -> ")[0][1:]  # Remove opening parenthesis
                            return_part = plugin.signature.split(" -> ")[1]
                            # Remove trailing closing parenthesis from params_part if present
                            if params_part.endswith(")"):
                                params_part = params_part[:-1]
                            method_def = f"    def {plugin.name}(self, {params_part}) -> {return_part}: ..."
                            methods.append(f"{source_comment}\n{method_def}")
                        else:
                            msg = f"Failed to parse signature for plugin {plugin.name}: {plugin.signature}"
                            # Remove double logging - StubGenerationError will log automatically
                            raise StubGenerationError(msg)
                else:
                    msg = f"No signature available for plugin {plugin.name} from {plugin.project_name}"
                    # Remove double logging - StubGenerationError will log automatically
                    raise StubGenerationError(msg)
            return methods

        base_then_methods = generate_method_signatures(base_then_plugins)
        base_as_methods = generate_method_signatures(base_as_plugins)
        hierarchy_then_methods = generate_method_signatures(hierarchy_then_plugins)
        hierarchy_as_methods = generate_method_signatures(hierarchy_as_plugins)
        current_then_methods = generate_method_signatures(current_then_plugins)
        current_as_methods = generate_method_signatures(current_as_plugins)

        # Generate combined method lists for backward compatibility
        then_methods = base_then_methods + hierarchy_then_methods + current_then_methods
        as_methods = base_as_methods + hierarchy_as_methods + current_as_methods

        all_then_names = [plugin.name for plugin in unique_then_plugins]
        all_as_names = [plugin.name for plugin in unique_as_plugins]

        get_logger().info(f"Discovered {len(unique_then_plugins)} unique {PLUGIN_TYPE_THEN}_ plugins and {len(unique_as_plugins)} unique {PLUGIN_TYPE_AS}_ plugins from current project")
        get_logger().debug(MSG_STUB_ORGANIZED_METHODS.format(
            len(base_then_methods), PLUGIN_TYPE_THEN, len(hierarchy_then_methods), PLUGIN_TYPE_THEN, len(current_then_methods), PLUGIN_TYPE_THEN
        ))
        get_logger().debug(MSG_STUB_ORGANIZED_METHODS.format(
            len(base_as_methods), PLUGIN_TYPE_AS, len(hierarchy_as_methods), PLUGIN_TYPE_AS, len(current_as_methods), PLUGIN_TYPE_AS
        ))

        return HierarchicalPlugins(
            then_plugins=unique_then_plugins,
            as_plugins=unique_as_plugins,
            all_then_names=all_then_names,
            all_as_names=all_as_names,
            then_methods=then_methods,
            as_methods=as_methods,
            base_then_methods=base_then_methods,
            base_as_methods=base_as_methods,
            hierarchy_then_methods=hierarchy_then_methods,
            hierarchy_as_methods=hierarchy_as_methods,
            current_then_methods=current_then_methods,
            current_as_methods=current_as_methods,
            all_typevar_imports=all_typevar_imports
        )

    except ChainTraversalError as e:
        msg = f"Failed to traverse project chain for {project_path}: {e}"
        raise StubGenerationError(msg) from e
    except Exception as e:
        msg = f"Failed to discover hierarchical plugins for {project_path}: {e}"
        raise StubGenerationError(msg) from e


# This function has been removed as all return type conversion now uses ast_service.py directly


def _extract_plugin_signature(plugin_file: Path, function_name: str) -> str | None:
    """Extract the actual function signature from a plugin file using AST service."""
    try:
        # Use AST service to parse file and find functions
        functions = parse_file_for_functions(plugin_file, function_name)

        for func_node in functions:
            if func_node.name == function_name:
                # Build method signature using AST service
                signature, _ = build_method_signature(func_node, function_name, add_self=False)
                # Extract just the parameters and return type part
                if signature.startswith("def ") and "(" in signature and ") ->" in signature:
                    start = signature.find("(")
                    end = signature.rfind(": ...")
                    if start != -1 and end != -1:
                        return signature[start:end]
                return signature

        msg = f"Function {function_name} not found in {plugin_file}"
        # Remove double logging - StubGenerationError will log automatically
        raise StubGenerationError(msg)
    except ASTServiceError as e:
        msg = f"AST parsing failed for {plugin_file} function {function_name}: {e}"
        raise StubGenerationError(msg) from e
    except Exception as e:
        msg = f"Failed to extract signature from {plugin_file} for function {function_name}: {e}"
        raise StubGenerationError(msg) from e




def generate_stub_content(project_path: Path | str) -> str:
    """Generate stub file content for a project.

    Example:
        ```python
        from chainedpy.services.stub_generation_service import generate_stub_content
        from chainedpy.services.project_lifecycle import create_project
        from pathlib import Path
        import shutil

        # Create test project
        project_path = create_project(Path("test_project"), "test_project")

        # Generate stub content
        stub_content = generate_stub_content(project_path)

        # Verify stub content structure
        assert "from typing import" in stub_content
        assert "class Chain" in stub_content
        assert "def then_map" in stub_content
        assert "def then_filter" in stub_content
        assert "def as_retry" in stub_content

        # Check type annotations
        assert "Chain[" in stub_content
        assert "_T" in stub_content
        assert "_O" in stub_content

        # Generate with string path
        stub_content_str = generate_stub_content(str(project_path))
        assert isinstance(stub_content_str, str)
        assert len(stub_content_str) > 0

        # Cleanup
        shutil.rmtree(project_path, ignore_errors=True)
        ```

    :param project_path: Path to the project.
    :type project_path: [Path][pathlib.Path] | [str][str]
    :return [str][str]: Generated stub file content.
    :raises StubGenerationError: If stub generation fails.
    """
    try:
        # @@ STEP 1: Initialize project path and package name. @@
        project_path = Path(project_path).expanduser().resolve()
        package_name = project_path.name

        # @@ STEP 2: Discover hierarchical plugins. @@
        hierarchical_plugins = _discover_hierarchical_plugins(project_path)
        then_names = hierarchical_plugins.all_then_names
        as_names = hierarchical_plugins.all_as_names
        then_methods = hierarchical_plugins.then_methods
        as_methods = hierarchical_plugins.as_methods
        # Get organized method lists.
        base_then_methods = hierarchical_plugins.base_then_methods
        base_as_methods = hierarchical_plugins.base_as_methods
        hierarchy_then_methods = hierarchical_plugins.hierarchy_then_methods
        hierarchy_as_methods = hierarchical_plugins.hierarchy_as_methods
        current_then_methods = hierarchical_plugins.current_then_methods
        current_as_methods = hierarchical_plugins.current_as_methods
        # Get all TypeVar imports.
        all_typevar_imports = hierarchical_plugins.all_typevar_imports

        # @@ STEP 3: Read project configuration. @@
        config = read_project_config(project_path)
        get_logger().debug(MSG_STUB_READ_CONFIG.format(config.base_project, config.summary))

        total_plugins = len(then_names) + len(as_names)

        # @@ STEP 4: Prepare summary and base import. @@
        # || S.S. 4.1: Use custom summary from config, with project_name substitution. ||
        summary = config.summary.format(project_name=package_name) if '{project_name}' in config.summary else config.summary

        # || S.S. 4.2: Determine the base import based on configuration. ||
        if config.base_project == DEFAULT_BASE_PROJECT:
            base_import = render_template(TEMPLATE_BASE_IMPORT_CHAINEDPY).strip()
            get_logger().debug(MSG_STUB_USING_BASE_IMPORT.format(DEFAULT_BASE_PROJECT, base_import))
        elif URL_SCHEME_SEPARATOR in config.base_project:
            # Remote base project - extract chain name from URL.
            parsed_url = urlparse(config.base_project)
            chain_name = Path(parsed_url.path).name
            base_import = render_template(TEMPLATE_BASE_IMPORT_REMOTE, chain_name=chain_name).strip()
            get_logger().debug(f"Using remote base import: {base_import}")
        else:
            # Custom project - import from its chain module.
            base_project_path = Path(config.base_project)
            get_logger().debug(f"Base project path from config: {base_project_path}")

            if not base_project_path.is_absolute():
                # Resolve relative path relative to current project.
                resolved_path = project_path.parent / base_project_path
                base_project_path = resolved_path.resolve()
                get_logger().debug(f"Resolved relative path: {project_path.parent} / {Path(config.base_project)} = {base_project_path}")

            base_project_name = base_project_path.name
            base_import = render_template(TEMPLATE_BASE_IMPORT_CUSTOM, base_project_name=base_project_name).strip()
            get_logger().debug(f"Using custom base import: {base_import}")

        # Convert backslashes to forward slashes to avoid Unicode escape issues
        escaped_project_path = str(project_path).replace('\\', '/')

        return render_stub_file(
            escaped_project_path=escaped_project_path,
            base_import=base_import,
            summary=summary,
            total_plugins=total_plugins,
            then_names=then_names,
            as_names=as_names,
            then_methods=then_methods,
            as_methods=as_methods,
            base_then_methods=base_then_methods,
            base_as_methods=base_as_methods,
            hierarchy_then_methods=hierarchy_then_methods,
            hierarchy_as_methods=hierarchy_as_methods,
            current_then_methods=current_then_methods,
            current_as_methods=current_as_methods,
            all_typevar_imports=all_typevar_imports  # Pass TypeVar imports to template
        )

    except TemplateServiceError as e:
        msg = f"Failed to render stub template for {project_path}: {e}"
        raise StubGenerationError(msg) from e
    except Exception as e:
        msg = f"Failed to generate stub content for {project_path}: {e}"
        raise StubGenerationError(msg) from e


def update_project_stub(project_path: Path | str, *, silent: bool = False) -> Path:
    """Update the .pyi stub file for a project.

    Example:
        ```python
        from chainedpy.services.stub_generation_service import update_project_stub
        from chainedpy.services.project_lifecycle import create_project
        from pathlib import Path
        import shutil

        # Create test project
        project_path = create_project(Path("test_project"), "test_project")

        # Update project stub
        stub_file = update_project_stub(project_path)

        # Verify stub file was created/updated
        assert stub_file.exists()
        assert stub_file.name == "test_project_chain.pyi"
        assert stub_file.parent == project_path

        # Verify stub content
        content = stub_file.read_text()
        assert "class Chain" in content
        assert "def then_map" in content
        assert "def then_filter" in content

        # Update silently
        stub_file_silent = update_project_stub(project_path, silent=True)
        assert stub_file_silent == stub_file
        assert stub_file_silent.exists()

        # Update with string path
        stub_file_str = update_project_stub(str(project_path))
        assert stub_file_str == stub_file

        # Cleanup
        shutil.rmtree(project_path, ignore_errors=True)
        ```

    :param project_path: Path to the project.
    :type project_path: [Path][pathlib.Path] | [str][str]
    :param silent: Whether to suppress output messages, defaults to False.
    :type silent: [bool][bool], optional
    :return [Path][pathlib.Path]: Path to the generated stub file.
    :raises StubGenerationError: If stub generation fails.
    """
    try:
        # @@ STEP 1: Initialize project path and stub file path. @@
        project_path = Path(project_path).expanduser().resolve()
        package_name = project_path.name
        stub_path = project_path / f"{package_name}{PYI_FILE_SUFFIX}"

        # @@ STEP 2: Generate stub content. @@
        content = generate_stub_content(project_path)

        # @@ STEP 3: Write the file and verify it was written correctly using fsspec. @@
        stub_path_str = str(stub_path)
        fs_utils.write_text(stub_path_str, content)

        # @@ STEP 4: Verify the content was actually written. @@
        written_content = fs_utils.read_text(stub_path_str)
        if written_content != content:
            msg = "Stub file content verification failed: written content does not match expected content"
            raise StubGenerationError(msg)

        get_logger().info(f"Stub file successfully written and verified: {stub_path}")

        # @@ STEP 5: Log completion if not silent. @@
        if not silent:
            get_logger().info(f"Stub written: {stub_path}")

        return stub_path

    except Exception as e:
        msg = f"Failed to write stub file {stub_path}: {e}"
        raise StubGenerationError(msg) from e

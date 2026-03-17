"""Template Service.

This service handles template rendering and file generation for ChainedPy projects.
It provides a centralized interface for all Jinja2 template operations, ensuring
consistent template rendering across the entire ChainedPy ecosystem.

The service manages template loading, context preparation, and rendering for various
file types including project files, configuration files, plugin skeletons, shell
scripts, and stub files. It maintains a configured Jinja2 environment with
appropriate settings for ChainedPy's template needs.

Note:
    This service was extracted from project.py to centralize template-related
    functionality and maintain clean separation between template rendering
    and other project operations. All template operations should go through
    this service for consistency.

Example:
    ```python
    from chainedpy.services.template_service import (
        render_template, render_project_file, create_plugin_file
    )
    from pathlib import Path

    # Render a template with context
    content = render_template(
        "project/chain_py.j2",
        project_name="my_project",
        base_import="from chainedpy import Chain"
    )

    # Render project-specific files
    chain_content = render_project_file(
        "chain_py",
        project_name="my_project",
        base_project="chainedpy"
    )

    # Create plugin files
    plugin_path = create_plugin_file(
        Path("./my_project"),
        "send_email",
        "then",
        update_stub=True
    )

    # Render configuration files
    config_content = render_config_file(
        base_project="chainedpy",
        summary="My custom project"
    )
    ```

See Also:
    - [render_template][chainedpy.services.template_service.render_template]: Core template rendering function
    - [render_project_file][chainedpy.services.template_service.render_project_file]: Render project-specific files
    - [create_plugin_file][chainedpy.services.template_service.create_plugin_file]: Create plugin skeletons
    - [chainedpy.constants][chainedpy.constants]: Template path constants
"""
from __future__ import annotations

# @@ STEP 1: Import standard library modules. @@
from pathlib import Path

# @@ STEP 2: Import third-party modules. @@
from jinja2 import Environment, PackageLoader, select_autoescape

# @@ STEP 3: Import internal constants. @@
from chainedpy.constants import (
    # File names and extensions
    INIT_FILE_NAME, CHAIN_FILE_SUFFIX, PYTHON_EXTENSION, JINJA_EXTENSION,
    # Directory structure
    PLUGINS_DIR, THEN_DIR, AS_DIR, PROCESSORS_DIR, TEMPLATE_DIR, PACKAGE_NAME,
    # Template paths
    TEMPLATE_PROJECT_CHAIN_PY, TEMPLATE_PROJECT_INIT_PY,
    TEMPLATE_CONFIG_YAML, TEMPLATE_STUB_PYI,
    TEMPLATE_THEN_PLUGIN, TEMPLATE_AS_PLUGIN, TEMPLATE_PROCESSOR_PLUGIN,
    # Context keys
    CONTEXT_KEY_SHORT, CONTEXT_KEY_CLS, CONTEXT_KEY_SNAKE,
    # Validation patterns
    PATTERN_ALREADY_EXISTS,
    # Plugin prefixes and types
    PLUGIN_PREFIX_PROCESSOR, PLUGIN_TYPE_THEN, PLUGIN_TYPE_AS, PLUGIN_TYPE_PROCESSOR
)

# @@ STEP 4: Import ChainedPy services. @@
from chainedpy.services import filesystem_service as fs_utils
from chainedpy.services.logging_service import get_logger

# @@ STEP 5: Import ChainedPy internal modules. @@
from chainedpy.exceptions import TemplateServiceError

# @@ STEP 6: Import TYPE_CHECKING modules. @@
# (none)

# @@ STEP 7: Initialize Jinja2 environment for template rendering. @@
_env = Environment(
    loader=PackageLoader(PACKAGE_NAME, TEMPLATE_DIR),
    autoescape=select_autoescape(disabled_extensions=(JINJA_EXTENSION.lstrip('.'),)),
    keep_trailing_newline=True,
)


def render_template(template_name: str, **context) -> str:
    """Render a Jinja2 template with the given context.

    Example:
        ```python
        from chainedpy.services.template_service import render_template
        from chainedpy.exceptions import TemplateServiceError

        # Render project chain file template
        content = render_template(
            "project/chain_py.j2",
            project_name="my_project",
            base_import="from chainedpy import Chain",
            summary="My custom chain project"
        )

        assert "my_project" in content
        assert "from chainedpy import Chain" in content
        assert "class Chain" in content

        # Render plugin template
        plugin_content = render_template(
            "plugins/then_plugin.j2",
            method_name="send_email",
            project_name="email_project"
        )

        assert "send_email" in plugin_content
        assert "@then" in plugin_content

        # Error handling for missing template
        try:
            render_template("nonexistent.j2", var="value")
        except TemplateServiceError as e:
            print(f"Template not found: {e}")
            assert "nonexistent.j2" in str(e)

        # Error handling for missing variables
        try:
            render_template("project/chain_py.j2")  # Missing required variables
        except TemplateServiceError as e:
            print(f"Missing variables: {e}")
        ```

    :param template_name: Name of the template file.
    :type template_name: [str][str]
    :param context: Template context variables.
    :type context: [Any][typing.Any]
    :return [str][str]: Rendered template content as string.
    :raises TemplateServiceError: If template rendering fails.
    """
    try:
        # @@ STEP 1: Get template and render with context. @@
        template = _env.get_template(template_name)
        return template.render(**context)
    except Exception as e:
        error_msg = f"Failed to render template {template_name}: {e}"
        raise TemplateServiceError(error_msg)


def write_template_file(template_name: str, output_path: Path, overwrite: bool = False, **context) -> Path:
    """Render a template and write it to a file using fsspec.

    Example:
        ```python
        from chainedpy.services.template_service import write_template_file
        from chainedpy.exceptions import TemplateServiceError
        from pathlib import Path

        # Write project chain file
        output_path = write_template_file(
            "project/chain_py.j2",
            Path("my_project_chain.py"),
            project_name="my_project",
            base_import="from chainedpy import Chain"
        )

        assert output_path.exists()
        content = output_path.read_text()
        assert "my_project" in content
        assert "from chainedpy import Chain" in content

        # Write plugin file
        plugin_path = write_template_file(
            "plugins/then_plugin.j2",
            Path("plugins/then_send_email.py"),
            method_name="send_email",
            project_name="email_project"
        )

        assert plugin_path.exists()
        plugin_content = plugin_path.read_text()
        assert "send_email" in plugin_content

        # Error when file exists and overwrite=False
        try:
            write_template_file(
                "project/chain_py.j2",
                Path("my_project_chain.py"),  # Already exists
                overwrite=False,
                project_name="other_project"
            )
        except TemplateServiceError as e:
            print(f"File exists: {e}")
            assert "already exists" in str(e)

        # Overwrite existing file
        new_path = write_template_file(
            "project/chain_py.j2",
            Path("my_project_chain.py"),
            overwrite=True,
            project_name="updated_project",
            base_import="from chainedpy import Chain"
        )

        updated_content = new_path.read_text()
        assert "updated_project" in updated_content

        # Cleanup
        Path("my_project_chain.py").unlink(missing_ok=True)
        Path("plugins/then_send_email.py").unlink(missing_ok=True)
        Path("plugins").rmdir()
        ```

    :param template_name: Name of the template file.
    :type template_name: [str][str]
    :param output_path: Path where the rendered content should be written.
    :type output_path: [Path][pathlib.Path]
    :param overwrite: Whether to overwrite existing files, defaults to False.
    :type overwrite: [bool][bool], optional
    :param context: Template context variables.
    :type context: [Any][typing.Any]
    :return [Path][pathlib.Path]: Resolved output path.
    :raises TemplateServiceError: If template rendering or file writing fails.
    """
    # @@ STEP 1: Convert path to string and check for existing file. @@
    output_path_str = str(output_path)

    # Check if file exists and overwrite is not allowed.
    if fs_utils.exists(output_path_str) and not overwrite:
        raise TemplateServiceError(f"File already exists: {output_path}")

    try:
        # @@ STEP 2: Render the template. @@
        content = render_template(template_name, **context)

        # @@ STEP 3: Ensure parent directories exist. @@
        fs_utils.makedirs(str(output_path.parent), exist_ok=True)

        # @@ STEP 4: Write the content. @@
        fs_utils.write_text(output_path_str, content.rstrip() + "\n")

        get_logger().info(f"Template file written: {output_path}")
        return output_path.resolve()

    except TemplateServiceError:
        raise
    except Exception as e:
        error_msg = f"Failed to write template file {output_path}: {e}"
        raise TemplateServiceError(error_msg)


def render_shell_script(script_type: str, shell: str, **context) -> str:
    """Render shell script from template.

    Example:
        ```python
        from chainedpy.services.template_service import render_shell_script
        from chainedpy.exceptions import TemplateServiceError
        from pathlib import Path

        # Render bash activation script
        bash_script = render_shell_script(
            "activation",
            "bash",
            project_path="/path/to/project",
            project_name="my_project"
        )

        assert "export" in bash_script
        assert "my_project" in bash_script
        assert "/path/to/project" in bash_script

        # Render PowerShell deactivation script
        ps_script = render_shell_script(
            "deactivation",
            "powershell",
            project_name="my_project"
        )

        assert "$env:" in ps_script or "Remove-Variable" in ps_script

        # Render fish shell initialization
        fish_script = render_shell_script(
            "init",
            "fish",
            shell_config_path="~/.config/fish/config.fish"
        )

        assert "function" in fish_script or "set" in fish_script

        # Error handling for invalid script type
        try:
            render_shell_script("invalid_type", "bash")
        except TemplateServiceError as e:
            print(f"Invalid script type: {e}")
            assert "invalid_type" in str(e)

        # Error handling for invalid shell
        try:
            render_shell_script("activation", "invalid_shell")
        except TemplateServiceError as e:
            print(f"Invalid shell: {e}")
            assert "invalid_shell" in str(e)
        ```

    :param script_type: Type of script ('activation', 'deactivation', 'init').
    :type script_type: [str][str]
    :param shell: Shell type ('bash', 'fish', 'powershell', 'cmd').
    :type shell: [str][str]
    :param context: Template context variables.
    :type context: [Any][typing.Any]
    :return [str][str]: Rendered shell script content.
    :raises TemplateServiceError: If template rendering fails.
    """
    # @@ STEP 1: Construct template name from script type and shell. @@
    template_name = f"shell/{script_type}_{shell}{JINJA_EXTENSION}"
    return render_template(template_name, **context)


def render_project_file(file_type: str, **context) -> str:
    """Render project file from template.

    Example:
        ```python
        from chainedpy.services.template_service import render_project_file
        from chainedpy.exceptions import TemplateServiceError

        # Render chain.py file
        chain_content = render_project_file(
            "chain_py",
            project_name="my_project",
            base_import="from chainedpy import Chain",
            summary="My custom chain project"
        )

        assert "class Chain" in chain_content
        assert "my_project" in chain_content
        assert "from chainedpy import Chain" in chain_content
        assert "My custom chain project" in chain_content

        # Render __init__.py file
        init_content = render_project_file(
            "init_py",
            project_name="my_project",
            base_import="from chainedpy import Chain"
        )

        assert "__all__" in init_content
        assert "Chain" in init_content

        # Error handling for invalid file type
        try:
            render_project_file("invalid_type", project_name="test")
        except TemplateServiceError as e:
            print(f"Invalid file type: {e}")
            assert "invalid_type" in str(e)

        # Error handling for missing context
        try:
            render_project_file("chain_py")  # Missing required variables
        except TemplateServiceError as e:
            print(f"Missing context: {e}")
        ```

    :param file_type: Type of file ('chain_py', 'init_py').
    :type file_type: [str][str]
    :param context: Template context variables.
    :type context: [Any][typing.Any]
    :return [str][str]: Rendered file content.
    :raises TemplateServiceError: If template rendering fails.
    """
    # @@ STEP 1: Map file types to template constants. @@
    template_mapping = {
        'chain_py': TEMPLATE_PROJECT_CHAIN_PY,
        'init_py': TEMPLATE_PROJECT_INIT_PY
    }

    # @@ STEP 2: Validate file type and get template. @@
    if file_type not in template_mapping:
        raise TemplateServiceError(f"Unknown project file type: {file_type}")

    template_name = template_mapping[file_type]
    return render_template(template_name, **context)


def render_stub_file(**context) -> str:
    """Render stub file from template.

    Example:
        ```python
        from chainedpy.services.template_service import render_stub_file
        from chainedpy.exceptions import TemplateServiceError

        # Render stub file with method signatures
        stub_content = render_stub_file(
            project_name="my_project",
            base_import="from chainedpy import Chain",
            methods=[
                {
                    "name": "then_send_email",
                    "signature": "def then_send_email(self, to: str, subject: str) -> Chain[bool]:",
                    "source": "my_project"
                },
                {
                    "name": "then_process_data",
                    "signature": "def then_process_data(self, data: dict) -> Chain[dict]:",
                    "source": "my_project"
                }
            ]
        )

        assert "my_project" in stub_content
        assert "then_send_email" in stub_content
        assert "then_process_data" in stub_content
        assert "Chain[bool]" in stub_content
        assert "Chain[dict]" in stub_content

        # Render empty stub file
        empty_stub = render_stub_file(
            project_name="empty_project",
            base_import="from chainedpy import Chain",
            methods=[]
        )

        assert "empty_project" in empty_stub
        assert "from chainedpy import Chain" in empty_stub

        # Error handling for missing context
        try:
            render_stub_file()  # Missing required variables
        except TemplateServiceError as e:
            print(f"Missing context: {e}")
        ```

    :param context: Template context variables.
    :type context: [Any][typing.Any]
    :return [str][str]: Rendered stub file content.
    :raises TemplateServiceError: If template rendering fails.
    """
    # @@ STEP 1: Use stub template and render. @@
    template_name = TEMPLATE_STUB_PYI
    return render_template(template_name, **context)


def render_config_file(**context) -> str:
    """Render configuration file from template.

    Example:
        ```python
        from chainedpy.services.template_service import render_config_file
        from chainedpy.exceptions import TemplateServiceError
        import yaml

        # Render configuration file
        config_content = render_config_file(
            base_project="chainedpy",
            summary="My custom ChainedPy project"
        )

        # Verify YAML structure
        config_data = yaml.safe_load(config_content)
        assert config_data["project"]["base_project"] == "chainedpy"
        assert config_data["project"]["summary"] == "My custom ChainedPy project"

        # Render with different base project
        advanced_config = render_config_file(
            base_project="advanced_chain",
            summary="Advanced chain with custom features"
        )

        advanced_data = yaml.safe_load(advanced_config)
        assert advanced_data["project"]["base_project"] == "advanced_chain"
        assert "Advanced chain" in advanced_data["project"]["summary"]

        # Error handling for missing context
        try:
            render_config_file()  # Missing required variables
        except TemplateServiceError as e:
            print(f"Missing context: {e}")
        ```

    :param context: Template context variables.
    :type context: [Any][typing.Any]
    :return [str][str]: Rendered config file content.
    :raises TemplateServiceError: If template rendering fails.
    """
    # @@ STEP 1: Use config template and render. @@
    template_name = TEMPLATE_CONFIG_YAML
    return render_template(template_name, **context)


def create_plugin_file(plugin_type: str, project_path: Path, name: str, **template_context) -> Path:
    """Create a plugin file from template.

    Example:
        ```python
        from chainedpy.services.template_service import create_plugin_file
        from chainedpy.exceptions import TemplateServiceError
        from pathlib import Path
        import shutil

        # Create project directory
        project_path = Path("test_project")
        project_path.mkdir(exist_ok=True)

        # Create then plugin
        then_plugin_path = create_plugin_file(
            "then",
            project_path,
            "send_email",
            project_name="test_project"
        )

        assert then_plugin_path.exists()
        assert then_plugin_path.name == "then_send_email.py"
        assert "plugins" in str(then_plugin_path)

        content = then_plugin_path.read_text()
        assert "@then" in content
        assert "send_email" in content

        # Create as_ plugin
        as_plugin_path = create_plugin_file(
            "as",
            project_path,
            "retry",
            project_name="test_project"
        )

        assert as_plugin_path.exists()
        assert as_plugin_path.name == "as_retry.py"

        as_content = as_plugin_path.read_text()
        assert "@as_" in as_content
        assert "retry" in as_content

        # Create processor plugin
        proc_plugin_path = create_plugin_file(
            "processor",
            project_path,
            "validate",
            project_name="test_project"
        )

        assert proc_plugin_path.exists()
        assert proc_plugin_path.name == "processor_validate.py"

        proc_content = proc_plugin_path.read_text()
        assert "@processor" in proc_content
        assert "validate" in proc_content

        # Error handling for invalid plugin type
        try:
            create_plugin_file("invalid", project_path, "test")
        except TemplateServiceError as e:
            print(f"Invalid plugin type: {e}")
            assert "Invalid plugin type" in str(e)

        # Cleanup
        shutil.rmtree(project_path, ignore_errors=True)
        ```

    :param plugin_type: Type of plugin ('then', 'as', 'processor').
    :type plugin_type: [str][str]
    :param project_path: Project root path.
    :type project_path: [Path][pathlib.Path]
    :param name: Plugin name.
    :type name: str
    :param template_context: Additional template context.
    :type template_context: [Any][typing.Any]
    :return [Path][pathlib.Path]: Path to the created plugin file.
    :raises TemplateServiceError: If plugin creation fails.
    """
    # @@ STEP 1: Validate plugin type. @@
    if plugin_type not in (PLUGIN_TYPE_THEN, PLUGIN_TYPE_AS, PLUGIN_TYPE_PROCESSOR):
        raise TemplateServiceError(f"Invalid plugin type: {plugin_type}")

    # @@ STEP 2: Determine template name and output path. @@
    if plugin_type == PLUGIN_TYPE_PROCESSOR:
        template_name = TEMPLATE_PROCESSOR_PLUGIN
        output_dir = project_path / PLUGINS_DIR / PROCESSORS_DIR
        output_file = output_dir / f"{PLUGIN_PREFIX_PROCESSOR}{name}{PYTHON_EXTENSION}"
        method_name = f"{PLUGIN_PREFIX_PROCESSOR}{name}"
    else:
        template_name = TEMPLATE_THEN_PLUGIN if plugin_type == PLUGIN_TYPE_THEN else TEMPLATE_AS_PLUGIN
        output_dir = project_path / PLUGINS_DIR / (AS_DIR if plugin_type == PLUGIN_TYPE_AS else THEN_DIR)
        output_file = output_dir / f"{plugin_type}_{name}{PYTHON_EXTENSION}"
        method_name = f"{plugin_type}_{name}"

    # @@ STEP 3: Prepare template context. @@
    if plugin_type == PLUGIN_TYPE_PROCESSOR:
        cls_name = _camel(f"{PLUGIN_TYPE_PROCESSOR}_{name}")
    else:
        cls_name = _camel(name)

    # @@ STEP 4: Build template context. @@
    context = {
        CONTEXT_KEY_SHORT: name,
        CONTEXT_KEY_CLS: cls_name,
        CONTEXT_KEY_SNAKE: name,
        **template_context
    }

    # @@ STEP 5: Create plugin file from template. @@
    try:
        return write_template_file(template_name, output_file, overwrite=False, **context)
    except TemplateServiceError as e:
        if PATTERN_ALREADY_EXISTS in str(e):
            raise TemplateServiceError(f"Plugin {method_name} already exists: {output_file}")
        raise


def _camel(snake: str) -> str:
    """Convert snake_case to CamelCase.

    :param snake: Snake case string to convert.
    :type snake: str
    :return str: CamelCase string.
    """
    # @@ STEP 1: Split snake_case and capitalize each word. @@
    return "".join(word.capitalize() for word in snake.split("_"))


def create_project_files(project_path: Path, project_name: str, base_import: str) -> None:
    """Create core project files from templates.

    Example:
        ```python
        from chainedpy.services.template_service import create_project_files
        from chainedpy.exceptions import TemplateServiceError
        from pathlib import Path
        import shutil

        # Create project directory
        project_path = Path("test_project")
        project_path.mkdir(exist_ok=True)

        # Create project files
        create_project_files(
            project_path,
            "test_project",
            "from chainedpy import Chain"
        )

        # Verify __init__.py files were created
        assert (project_path / "__init__.py").exists()
        assert (project_path / "plugins" / "__init__.py").exists()
        assert (project_path / "plugins" / "then" / "__init__.py").exists()
        assert (project_path / "plugins" / "as_" / "__init__.py").exists()
        assert (project_path / "plugins" / "processors" / "__init__.py").exists()

        # Verify chain file was created
        chain_file = project_path / "test_project_chain.py"
        assert chain_file.exists()

        chain_content = chain_file.read_text()
        assert "from chainedpy import Chain" in chain_content
        assert "class Chain" in chain_content

        # Verify __init__.py content
        init_content = (project_path / "__init__.py").read_text()
        assert "__all__" in init_content

        # Error handling for invalid paths
        try:
            create_project_files(
                Path("/root/protected"),
                "test",
                "from chainedpy import Chain"
            )
        except TemplateServiceError as e:
            print(f"Permission error: {e}")

        # Cleanup
        shutil.rmtree(project_path, ignore_errors=True)
        ```

    :param project_path: Project root path.
    :type project_path: [Path][pathlib.Path]
    :param project_name: Name of the project.
    :type project_name: [str][str]
    :param base_import: Import statement for base Chain class.
    :type base_import: [str][str]
    :raises TemplateServiceError: If file creation fails.
    """
    try:
        # @@ STEP 1: Create __init__.py files using template. @@
        init_content = render_project_file("init_py")

        _ensure_pkg_init_with_content(project_path / INIT_FILE_NAME, init_content)
        _ensure_pkg_init_with_content(project_path / PLUGINS_DIR / INIT_FILE_NAME, init_content)

        for sub in (THEN_DIR, AS_DIR, PROCESSORS_DIR):
            _ensure_pkg_init_with_content(project_path / PLUGINS_DIR / sub / INIT_FILE_NAME, init_content)

        # @@ STEP 2: Create chain.py file using template. @@
        chain_py = project_path / f"{project_name}{CHAIN_FILE_SUFFIX}"
        chain_content = render_project_file("chain_py", base_import=base_import)

        fs_utils.write_text(str(chain_py), chain_content)
        get_logger().info(f"Created chain file: {chain_py}")

    except Exception as e:
        error_msg = f"Failed to create project files: {e}"
        raise TemplateServiceError(error_msg)


def _ensure_pkg_init_with_content(path: Path, content: str) -> None:
    """Ensure package __init__.py file exists with specific content using fsspec.

    :param path: Path to the __init__.py file.
    :type path: Path
    :param content: Content to write to the file.
    :type content: str
    :raises TemplateServiceError: If path is not a file.
    """
    # @@ STEP 1: Check if file exists and create if needed. @@
    path_str = str(path)
    if not fs_utils.exists(path_str):
        fs_utils.write_text(path_str, content)
    elif not path.is_file():
        # Note: For remote filesystems, we can't easily check if it's a file vs directory.
        # This check is mainly for local filesystem validation.
        raise TemplateServiceError(f"{path} is not a file")


def get_available_templates() -> list[str]:
    """Get list of available template files.

    :return list[str]: List of template file names.
    :raises TemplateServiceError: If listing templates fails.
    """
    try:
        # @@ STEP 1: List all available templates. @@
        return _env.list_templates()
    except Exception as e:
        msg = f"Failed to list templates: {e}"
        raise TemplateServiceError(msg) from e


def validate_template_context(template_name: str, context: dict) -> bool:
    """Validate that the provided context contains all required variables for a template.

    :param template_name: Name of the template.
    :type template_name: [str][str]
    :param context: Template context to validate.
    :type context: [dict][dict]
    :return [bool][bool]: True if context is valid.
    :raises TemplateServiceError: If validation fails.

    Example:
        ```python
        from chainedpy.services.template_service import validate_template_context
        from chainedpy.exceptions import TemplateServiceError

        # Valid context for project template
        valid_context = {
            "project_name": "my_project",
            "base_import": "from chainedpy import Chain",
            "summary": "Test project"
        }

        is_valid = validate_template_context("project/chain_py.j2", valid_context)
        assert is_valid == True

        # Invalid context (missing required variables)
        invalid_context = {
            "project_name": "my_project"
            # Missing base_import and summary
        }

        try:
            validate_template_context("project/chain_py.j2", invalid_context)
        except TemplateServiceError as e:
            print(f"Validation failed: {e}")
            assert "missing" in str(e).lower() or "undefined" in str(e).lower()

        # Valid context for plugin template
        plugin_context = {
            "method_name": "send_email",
            "project_name": "email_project"
        }

        is_valid = validate_template_context("plugins/then_plugin.j2", plugin_context)
        assert is_valid == True

        # Error for non-existent template
        try:
            validate_template_context("nonexistent.j2", {})
        except TemplateServiceError as e:
            print(f"Template not found: {e}")
        ```
    """
    try:
        # @@ STEP 1: Try to render with the provided context to check for missing variables. @@
        render_template(template_name, **context)
        return True
    except Exception as e:
        raise TemplateServiceError(f"Template context validation failed for {template_name}: {e}")

"""Shell Integration Service.

This service handles shell script generation and shell integration management for
ChainedPy projects. It provides functionality for generating activation/deactivation
scripts, managing shell initialization, and handling cross-platform shell compatibility.

The service supports multiple shell types including bash, zsh, fish, PowerShell, and
Windows command prompt. It generates appropriate scripts for each shell type and
manages the integration with shell configuration files for persistent activation.

Note:
    This service was extracted from project.py to centralize shell-related
    functionality and maintain clean separation between project management
    and shell integration concerns.

Example:
    ```python
    from chainedpy.services.shell_integration import (
        generate_activation_script, generate_deactivation_script,
        initialize_shell_integration, detect_shell
    )
    from pathlib import Path

    # Generate activation script
    project_path = Path("./my_project")
    activation_script = generate_activation_script(project_path, "bash")
    print(activation_script)

    # Generate deactivation script
    deactivation_script = generate_deactivation_script("bash")
    print(deactivation_script)

    # Initialize shell integration
    result = initialize_shell_integration(
        shell="bash",
        dry_run=False,
        force=False
    )
    print(result)

    # Auto-detect current shell
    current_shell = detect_shell()
    print(f"Detected shell: {current_shell}")
    ```

See Also:
    - [generate_activation_script][chainedpy.services.shell_integration.generate_activation_script]: Generate project activation scripts
    - [generate_deactivation_script][chainedpy.services.shell_integration.generate_deactivation_script]: Generate deactivation scripts
    - [initialize_shell_integration][chainedpy.services.shell_integration.initialize_shell_integration]: Set up shell integration
    - [chainedpy.services.template_service][chainedpy.services.template_service]: Template rendering for shell scripts
"""
from __future__ import annotations

# 1. Standard library imports
import os
import platform
import subprocess
from pathlib import Path

# 2. Third-party imports
# (none)

# 3. Internal constants
from chainedpy.constants import (
    # Environment variables
    ENV_ACTIVE_PROJECT, ENV_SHELL, ENV_PS_MODULE_PATH,
    # File names and extensions
    INIT_FILE_NAME, CHAIN_FILE_SUFFIX,
    # Shell types
    SHELL_BASH, SHELL_ZSH, SHELL_SH, SHELL_FISH, SHELL_CMD, SHELL_BATCH, SHELL_POWERSHELL,
    # Shell prompt patterns
    SHELL_PS1_VAR, SHELL_INTEGRATION_MARKER,
    # Platform and shell file path constants
    PLATFORM_WINDOWS, POWERSHELL_PROFILE_PATH, CHAINEDPY_BATCH_FILE,
    BASHRC_FILE, BASH_PROFILE_FILE, ZSHRC_FILE, FISH_CONFIG_PATH,
    # Template constants
    TEMPLATE_SHELL_INIT_DRY_RUN, TEMPLATE_SHELL_INIT_SUCCESS
)

# 4. ChainedPy services
from chainedpy.services import filesystem_service as fs_utils
from chainedpy.services.template_service import render_shell_script, render_template, TemplateServiceError

# 5. ChainedPy internal modules
from chainedpy.exceptions import ShellIntegrationError

# 6. TYPE_CHECKING imports (none)


# Remove redundant variable - use ENV_ACTIVE_PROJECT directly


def detect_shell() -> str:
    """Auto-detect the current shell.

    Example:
        ```python
        from chainedpy.services.shell_integration import detect_shell
        import os

        # Detect current shell
        shell = detect_shell()
        print(f"Detected shell: {shell}")

        # Common shells
        assert shell in ["bash", "fish", "powershell", "cmd", "unknown"]

        # Mock different shells
        original_shell = os.environ.get("SHELL", "")

        # Mock bash
        os.environ["SHELL"] = "/bin/bash"
        assert detect_shell() == "bash"

        # Mock fish
        os.environ["SHELL"] = "/usr/bin/fish"
        assert detect_shell() == "fish"

        # Mock PowerShell
        os.environ["SHELL"] = ""
        os.environ["PSModulePath"] = "C:\\Program Files\\PowerShell"
        shell = detect_shell()
        assert shell in ["powershell", "unknown"]

        # Restore original
        if original_shell:
            os.environ["SHELL"] = original_shell
        else:
            os.environ.pop("SHELL", None)
        ```

    :return [str][str]: Detected shell name.
    """
    # @@ STEP 1: Check environment variables first. @@
    shell_env = os.environ.get(ENV_SHELL, '').lower()
    if SHELL_BASH in shell_env:
        return SHELL_BASH
    elif SHELL_ZSH in shell_env:
        return SHELL_ZSH
    elif SHELL_FISH in shell_env:
        return SHELL_FISH

    # @@ STEP 2: Platform-specific detection. @@
    if platform.system() == PLATFORM_WINDOWS:
        # Check if we're in PowerShell.
        if os.environ.get(ENV_PS_MODULE_PATH):
            return SHELL_POWERSHELL
        else:
            return SHELL_CMD
    else:
        # Default to bash on Unix-like systems.
        return SHELL_BASH


def get_shell_config_path(shell: str) -> Path:
    """Get the configuration file path for a shell.

    Example:
        ```python
        from chainedpy.services.shell_integration import get_shell_config_path
        from chainedpy.exceptions import ShellIntegrationError
        from pathlib import Path

        # Get bash config path
        bash_config = get_shell_config_path("bash")
        assert bash_config.name in [".bashrc", ".bash_profile"]
        assert bash_config.is_absolute()

        # Get fish config path
        fish_config = get_shell_config_path("fish")
        assert "config.fish" in str(fish_config)

        # Get PowerShell config path
        ps_config = get_shell_config_path("powershell")
        assert "profile.ps1" in str(ps_config)

        # Unsupported shell
        try:
            get_shell_config_path("unsupported")
        except ShellIntegrationError as e:
            print(f"Unsupported shell: {e}")
            assert "unsupported" in str(e).lower()

        # Verify paths are in home directory
        home = Path.home()
        assert bash_config.is_relative_to(home)
        ```

    :param shell: Shell name to get config path for.
    :type shell: [str][str]
    :return [Path][pathlib.Path]: Path to shell configuration file.
    :raises ShellIntegrationError: If shell is not supported.
    """
    # @@ STEP 1: Get home directory. @@
    home = Path.home()

    # @@ STEP 2: Determine config path based on shell type. @@
    if shell == SHELL_BASH:
        # || S.S. 2.1: Try .bashrc first, then .bash_profile. ||
        bashrc = home / BASHRC_FILE
        if bashrc.exists():
            return bashrc
        return home / BASH_PROFILE_FILE
    elif shell == SHELL_ZSH:
        return home / ZSHRC_FILE
    elif shell == SHELL_FISH:
        return home / FISH_CONFIG_PATH
    elif shell == SHELL_POWERSHELL:
        # || S.S. 2.2: Get PowerShell profile path. ||
        try:
            result = subprocess.run([SHELL_POWERSHELL, '-Command', f'echo ${SHELL_PS1_VAR}ROFILE'],
                                  capture_output=True, text=True, check=True)
            return Path(result.stdout.strip())
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Fallback to default location.
            return home / POWERSHELL_PROFILE_PATH
    elif shell in (SHELL_CMD, SHELL_BATCH):
        # CMD doesn't have a standard config file, suggest creating a batch file.
        return home / CHAINEDPY_BATCH_FILE
    else:
        raise ShellIntegrationError(f"Unsupported shell: {shell}")


def _get_template_shell(shell: str) -> str:
    """Map shell names to template names for script generation.

    Example:
        ```python
        from chainedpy.services.shell_integration import _get_template_shell
        from chainedpy.exceptions import ShellIntegrationError

        # Supported shells
        assert _get_template_shell("bash") == "bash"
        assert _get_template_shell("fish") == "fish"
        assert _get_template_shell("powershell") == "powershell"
        assert _get_template_shell("cmd") == "cmd"

        # Unsupported shell
        try:
            _get_template_shell("unsupported")
        except ShellIntegrationError as e:
            print(f"Unsupported shell: {e}")
            assert "unsupported" in str(e)

        # Case sensitivity
        assert _get_template_shell("BASH") == "bash"
        assert _get_template_shell("Fish") == "fish"
        ```

    :param shell: Shell name to map.
    :type shell: [str][str]
    :return [str][str]: Template shell name.
    :raises ShellIntegrationError: If shell is not supported.
    """
    # @@ STEP 1: Map shell to template name. @@
    if shell in (SHELL_BASH, SHELL_ZSH, SHELL_SH):
        return SHELL_BASH
    elif shell == SHELL_FISH:
        return SHELL_FISH
    elif shell in (SHELL_CMD, SHELL_BATCH):
        return SHELL_CMD
    elif shell == SHELL_POWERSHELL:
        return SHELL_POWERSHELL
    else:
        raise ShellIntegrationError(f"Unsupported shell: {shell}")


def generate_activation_script(project_path: Path | str, shell: str = "bash") -> str:
    """Generate shell code to activate a ChainedPy project (like conda activate).

    Example:
        ```python
        from chainedpy.services.shell_integration import generate_activation_script
        from chainedpy.services.project_lifecycle import create_project
        from pathlib import Path
        import shutil

        # Create test project
        project_path = create_project(Path("test_project"), "test_project")

        # Generate bash activation script
        bash_script = generate_activation_script(project_path, "bash")
        assert "export" in bash_script
        assert str(project_path) in bash_script
        assert "CHAINEDPY_ACTIVE_PROJECT" in bash_script

        # Generate fish activation script
        fish_script = generate_activation_script(project_path, "fish")
        assert "set -x" in fish_script
        assert str(project_path) in fish_script

        # Generate PowerShell activation script
        ps_script = generate_activation_script(project_path, "powershell")
        assert "$env:" in ps_script
        assert str(project_path) in ps_script

        # With string path
        script = generate_activation_script(str(project_path), "bash")
        assert str(project_path) in script

        # Cleanup
        shutil.rmtree(project_path, ignore_errors=True)
        ```

    :param project_path: Path to the ChainedPy project.
    :type project_path: [Path][pathlib.Path] | [str][str]
    :param shell: Shell type to generate script for, defaults to "bash".
    :type shell: [str][str], optional
    :return [str][str]: Shell activation script.
    :raises FileNotFoundError: If project path is invalid or not a ChainedPy project.
    :raises ShellIntegrationError: If script generation fails.
    """
    # @@ STEP 1: Normalize and validate project path. @@
    project_path = Path(project_path).expanduser().resolve()
    if project_path.is_file():
        project_path = project_path.parent
    if not (project_path / INIT_FILE_NAME).exists():
        raise FileNotFoundError(f"{project_path} is not a Python package")

    # @@ STEP 2: Validate project structure. @@
    chain_file = project_path / f"{project_path.name}{CHAIN_FILE_SUFFIX}"
    if not chain_file.exists():
        raise FileNotFoundError(f"Not a ChainedPy project: missing {chain_file}")

    # @@ STEP 3: Prepare template variables. @@
    project_path_str = str(project_path).replace("\\", "\\\\")
    template_shell = _get_template_shell(shell)

    # @@ STEP 4: Generate activation script. @@
    try:
        return render_shell_script(
            "activation",
            template_shell,
            env_var=ENV_ACTIVE_PROJECT,
            project_path_str=project_path_str,
            project_name=project_path.name
        )
    except TemplateServiceError as e:
        raise ShellIntegrationError(f"Failed to generate activation script: {e}") from e


def generate_deactivation_script(shell: str = "bash") -> str:
    """Generate shell code to deactivate the current ChainedPy project.

    Example:
        ```python
        from chainedpy.services.shell_integration import generate_deactivation_script

        # Generate bash deactivation script
        bash_script = generate_deactivation_script("bash")
        assert "unset" in bash_script
        assert "CHAINEDPY_ACTIVE_PROJECT" in bash_script

        # Generate fish deactivation script
        fish_script = generate_deactivation_script("fish")
        assert "set -e" in fish_script
        assert "CHAINEDPY_ACTIVE_PROJECT" in fish_script

        # Generate PowerShell deactivation script
        ps_script = generate_deactivation_script("powershell")
        assert "Remove-Variable" in ps_script or "$env:" in ps_script
        assert "CHAINEDPY_ACTIVE_PROJECT" in ps_script

        # Default shell (bash)
        default_script = generate_deactivation_script()
        assert "unset" in default_script
        ```

    :param shell: Shell type to generate script for, defaults to "bash".
    :type shell: [str][str], optional
    :return [str][str]: Shell deactivation script.
    :raises ShellIntegrationError: If script generation fails.
    """
    # @@ STEP 1: Get template shell name. @@
    template_shell = _get_template_shell(shell)

    # @@ STEP 2: Generate deactivation script. @@
    try:
        return render_shell_script(
            "deactivation",
            template_shell,
            env_var=ENV_ACTIVE_PROJECT
        )
    except TemplateServiceError as e:
        raise ShellIntegrationError(f"Failed to generate deactivation script: {e}") from e


def get_reload_command(shell: str | None = None) -> str:
    """Get the command to reload shell configuration.

    Example:
        ```python
        from chainedpy.services.shell_integration import get_reload_command

        # Get reload command for bash
        bash_reload = get_reload_command("bash")
        assert "source" in bash_reload
        assert ".bashrc" in bash_reload or ".bash_profile" in bash_reload

        # Get reload command for fish
        fish_reload = get_reload_command("fish")
        assert "source" in fish_reload
        assert "config.fish" in fish_reload

        # Get reload command for PowerShell
        ps_reload = get_reload_command("powershell")
        assert "." in ps_reload or "&" in ps_reload
        assert "profile.ps1" in ps_reload

        # Auto-detect shell
        auto_reload = get_reload_command()
        assert isinstance(auto_reload, str)
        assert len(auto_reload) > 0
        ```

    :param shell: Shell type to get reload command for, defaults to None.
    :type shell: [str][str] | [None][None], optional
    :return [str][str]: Shell reload command.
    """
    # @@ STEP 1: Detect shell if not provided. @@
    if shell is None:
        shell = detect_shell()

    # @@ STEP 2: Get shell configuration path. @@
    config_path = get_shell_config_path(shell)

    # @@ STEP 3: Return appropriate reload command for shell. @@
    if shell == SHELL_POWERSHELL:
        return f'. ${SHELL_PS1_VAR}ROFILE'
    elif shell == SHELL_FISH:
        return f'source {config_path}'
    elif shell in (SHELL_BASH, SHELL_ZSH):
        return f'source {config_path}'
    elif shell in (SHELL_CMD, SHELL_BATCH):
        return f'call {config_path}'
    else:
        return 'restart your shell'


def generate_shell_init(shell: str) -> str:
    """Generate shell initialization code for ChainedPy integration.

    Example:
        ```python
        from chainedpy.services.shell_integration import generate_shell_init
        from chainedpy.exceptions import ShellIntegrationError

        # Generate bash initialization
        bash_init = generate_shell_init("bash")
        assert "function" in bash_init or "alias" in bash_init
        assert "chainedpy" in bash_init

        # Generate fish initialization
        fish_init = generate_shell_init("fish")
        assert "function" in fish_init
        assert "chainedpy" in fish_init

        # Generate PowerShell initialization
        ps_init = generate_shell_init("powershell")
        assert "function" in ps_init or "Set-Alias" in ps_init
        assert "chainedpy" in ps_init

        # Unsupported shell
        try:
            generate_shell_init("unsupported")
        except ShellIntegrationError as e:
            print(f"Unsupported shell: {e}")
        ```

    :param shell: Shell type to generate initialization code for.
    :type shell: [str][str]
    :return [str][str]: Shell initialization script.
    :raises ShellIntegrationError: If script generation fails.
    """
    # @@ STEP 1: Get template shell name. @@
    template_shell = _get_template_shell(shell)

    # @@ STEP 2: Generate shell initialization script. @@
    try:
        return render_shell_script("init", template_shell)
    except TemplateServiceError as e:
        raise ShellIntegrationError(f"Failed to generate shell init script: {e}") from e


def initialize_shell_integration(shell: str | None = None, dry_run: bool = False, force: bool = False) -> str:
    """Initialize ChainedPy shell integration automatically.

    Example:
        ```python
        from chainedpy.services.shell_integration import initialize_shell_integration
        from chainedpy.exceptions import ShellIntegrationError

        # Dry run to see what would be done
        message = initialize_shell_integration(shell="bash", dry_run=True)
        print(f"Dry run result: {message}")
        assert "would" in message.lower() or "dry run" in message.lower()

        # Initialize for specific shell
        try:
            message = initialize_shell_integration(shell="bash", force=True)
            print(f"Initialization result: {message}")
            assert "initialized" in message.lower() or "success" in message.lower()
        except ShellIntegrationError as e:
            print(f"Initialization failed: {e}")

        # Auto-detect shell and initialize
        try:
            message = initialize_shell_integration(force=True)
            print(f"Auto-detect result: {message}")
        except ShellIntegrationError as e:
            print(f"Auto-detect failed: {e}")

        # Initialize without force (should warn if already exists)
        message = initialize_shell_integration(shell="bash")
        print(f"Non-force result: {message}")
        ```

    :param shell: Shell type to initialize integration for, defaults to None.
    :type shell: [str][str] | [None][None], optional
    :param dry_run: If True, show what would be done without making changes, defaults to False.
    :type dry_run: [bool][bool], optional
    :param force: If True, reinitialize even if already initialized, defaults to False.
    :type force: [bool][bool], optional
    :return [str][str]: Status message about initialization.
    :raises ShellIntegrationError: If initialization fails.
    """
    # @@ STEP 1: Detect shell if not provided. @@
    if shell is None:
        shell = detect_shell()

    # @@ STEP 2: Get shell configuration and generate initialization code. @@
    config_path = get_shell_config_path(shell)
    shell_code = generate_shell_init(shell)

    # @@ STEP 3: Check if already initialized. @@
    marker = SHELL_INTEGRATION_MARKER
    already_initialized = False

    config_path_str = str(config_path)
    if fs_utils.exists(config_path_str):
        try:
            content = fs_utils.read_text(config_path_str)
            if marker in content:
                already_initialized = True
        except (UnicodeDecodeError, PermissionError):
            # If we can't read the file, assume not initialized.
            pass

    # @@ STEP 4: Handle dry run mode. @@
    if dry_run:
        status = "already initialized" if already_initialized else "would be initialized"
        return render_template(TEMPLATE_SHELL_INIT_DRY_RUN,
                             shell=shell,
                             config_path=config_path,
                             status=status,
                             shell_code=shell_code)

    # @@ STEP 5: Check if already initialized and not forcing. @@
    if already_initialized and not force:
        # TODO: USE JINJA2 TEMPLATE, NO HARDCODED F-STRING LIKE THIS AT ALL.
        return f"""ChainedPy shell integration is already initialized in:
{config_path}

If you want to reinitialize (not recommended), run:
chainedpy init --force

To check what's currently configured, run:
chainedpy init --dry-run"""

    # @@ STEP 6: Create config directory if it doesn't exist. @@
    fs_utils.makedirs(str(config_path.parent), exist_ok=True)

    # @@ STEP 7: Append the shell integration code. @@
    try:
        config_path_str = str(config_path)
        # || S.S. 7.1: Read existing content if file exists. ||
        existing_content = ""
        if fs_utils.exists(config_path_str):
            existing_content = fs_utils.read_text(config_path_str)

        # || S.S. 7.2: Append new content. ||
        new_content = existing_content + '\n\n' + shell_code + '\n'
        fs_utils.write_text(config_path_str, new_content)

        # || S.S. 7.3: Generate reload command and provide clear instructions. ||
        reload_cmd = get_reload_command(shell)

        return render_template(TEMPLATE_SHELL_INIT_SUCCESS,
                             config_path=config_path,
                             reload_cmd=reload_cmd)

    except Exception as e:
        error_msg = f"Failed to initialize shell integration: {e}"
        raise ShellIntegrationError(error_msg) from e

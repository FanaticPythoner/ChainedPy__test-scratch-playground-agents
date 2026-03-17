"""Command Handlers Service.

This service contains pure command handling logic extracted from [cli.py][chainedpy.cli] to maintain
clean separation between argument parsing and business logic. Each command handler is responsible
for orchestrating the appropriate services to fulfill CLI command requests.

The handlers provide a clean interface between the CLI layer and the service layer, ensuring
that command logic can be easily tested and reused programmatically. All handlers follow
consistent patterns for error handling, logging, and user feedback.

Note:
    Command handlers should focus on orchestration and delegation to specialized services.
    They should not contain complex business logic themselves, but rather coordinate
    between multiple services to achieve the desired outcome.

Example:
    ```python
    from chainedpy.services.command_handlers import (
        handle_create_project, handle_activate_project
    )
    import argparse

    # Create mock arguments (normally from CLI)
    args = argparse.Namespace(
        name="my_project",
        dest=Path("./projects"),
        base_project="chainedpy",
        summary="My custom project"
    )

    # Handle project creation
    handle_create_project(args)

    # Handle project activation
    activation_args = argparse.Namespace(
        project_path=Path("./projects/my_project"),
        shell="bash"
    )
    handle_activate_project(activation_args)
    ```

See Also:
    - [chainedpy.cli][chainedpy.cli]: CLI module that uses these handlers
    - [chainedpy.services.project_lifecycle][chainedpy.services.project_lifecycle]: Project management services
    - [chainedpy.services.shell_integration][chainedpy.services.shell_integration]: Shell integration services
"""
from __future__ import annotations

# @@ STEP 1: Import standard library modules. @@
import argparse
import sys
from pathlib import Path

# @@ STEP 2: Import third-party modules. @@
# (none)

# 3. Internal constants
from chainedpy.constants import (
    # Default values
    DEFAULT_BASE_PROJECT,
    # URL patterns
    URL_SCHEME_SEPARATOR,
    # Message templates
    MSG_ERROR_PREFIX, MSG_SUCCESS_GLOBAL_PROJECT_SET,
    MSG_NO_PROJECTS_FOUND, MSG_AVAILABLE_PROJECTS, MSG_ACTIVE_PROJECT_MARKER,
    MSG_PLUGIN_STUB_UPDATED, MSG_PLUGIN_STUB_HELP,
    # File names
    CONFIG_FILE_NAME,
    # Argument names
    ARG_PROJECT_PATH, ARG_BASE_PROJECT, ARG_SUMMARY, ARG_GITHUB_TOKEN,
    ARG_GITLAB_TOKEN, ARG_UPDATE_PYI, ARG_FORCE, ARG_VERBOSE,
    # Plugin types
    PLUGIN_TYPE_THEN, PLUGIN_TYPE_AS, PLUGIN_TYPE_PROCESSOR,
    # Plugin prefixes
    PLUGIN_PREFIX_THEN, PLUGIN_PREFIX_AS, TEMPLATE_PLUGIN_SUCCESS, TEMPLATE_REMOTE_CHAIN_UPDATE, TEMPLATE_REMOTE_CHAIN_CHECK,
    TEMPLATE_REMOTE_CHAIN_LIST, TEMPLATE_REMOTE_CHAIN_STATUS, TEMPLATE_PROJECT_LIST,
    TEMPLATE_SHELL_RELOAD, TEMPLATE_VALIDATION_MESSAGES,
    TEMPLATE_PROJECT_CREATED_ACTIVATED, TEMPLATE_PROJECT_CREATED_MANUAL_ACTIVATION,
)

# 4. ChainedPy services
from chainedpy.services.credential_service import create_env_file, CredentialServiceError
from chainedpy.services.logging_service import get_logger
from chainedpy.services.project_lifecycle import (
    get_active_project, read_project_config, _update_chain_file_with_import
)
from chainedpy.services.project_remote_chain_service import (
    ProjectRemoteChainServiceError, detect_chain_changes, update_project_chains,
    get_project_chain_import, list_project_remote_chains, get_remote_chain_status
)
from chainedpy.services.project_validation import (
    validate_base_project, merge_credentials, ProjectValidationError, validate_local_project
)
from chainedpy.services.shell_integration import (
    generate_activation_script, generate_deactivation_script,
    initialize_shell_integration, get_reload_command, ShellIntegrationError
)
from chainedpy.services.stub_generation_service import update_project_stub
from chainedpy.services.template_service import render_template, create_plugin_file

# 5. ChainedPy internal modules
from chainedpy.project import (
    get_active_project as project_get_active_project, create_project, activate_project,
    set_global_project, list_projects, update_project_stub as project_update_project_stub,
    update_project_base, show_project_chain, create_then_plugin, create_as_plugin, create_processor
)

def _positive_exit(message: str) -> None:
    """Exit with success message.

    Example:
        ```python
        from chainedpy.services.command_handlers import _positive_exit

        # Exit with success message
        _positive_exit("Project created successfully!")
        # This will print the message and exit with code 0

        # Used in command handlers
        _positive_exit("Operation completed successfully")
        ```

    :param message: Success message to display.
    :type message: [str][str]
    """
    print(message)
    sys.exit(0)


def _die(message: str, code: int = 1) -> None:
    """Exit with error message.

    Example:
        ```python
        from chainedpy.services.command_handlers import _die

        # Exit with error message and default code
        _die("Project creation failed!")
        # This will print the message and exit with code 1

        # Exit with custom error code
        _die("Invalid configuration", code=2)
        # This will print the message and exit with code 2

        # Used in error handling
        try:
            risky_operation()
        except Exception as e:
            _die(f"Operation failed: {e}")
        ```

    :param message: Error message to display.
    :type message: [str][str]
    :param code: Exit code, defaults to 1.
    :type code: [int][int], optional
    """
    get_logger().error(f"{MSG_ERROR_PREFIX} {message}")
    print(f"{MSG_ERROR_PREFIX} {message}", file=sys.stderr)
    sys.exit(code)




def _resolve_project_path(args: argparse.Namespace) -> Path:
    """Resolve project path from args or active project."""
    if hasattr(args, ARG_PROJECT_PATH) and args.project_path:
        return args.project_path

    active_project = get_active_project()
    if active_project:
        return active_project

    _die("No project path specified and no active project. "
         "Use --project-path or activate a project first.")
    return Path()  # Never reached, but satisfies type checker


def _resolve_remote_project_path(args: argparse.Namespace) -> Path:
    """Resolve project path for remote chain operations with expanded path resolution."""
    if hasattr(args, ARG_PROJECT_PATH) and args.project_path:
        return Path(args.project_path).expanduser().resolve()

    # Use current directory or active project
    project_path = get_active_project()
    if not project_path:
        project_path = Path.cwd()

    return project_path


def _validate_chainedpy_project(project_path: Path) -> None:
    """Validate that the given path is a ChainedPy project."""
    if not (project_path / CONFIG_FILE_NAME).exists():
        _die(f"❌ Not a ChainedPy project: {project_path}")


def _validate_remote_chainedpy_project(project_path: Path) -> tuple[Path, object] | None:
    """Validate ChainedPy project and return config for remote operations.

    Returns None if project has no remote dependencies.
    """
    _validate_chainedpy_project(project_path)

    # Read project config
    config = read_project_config(project_path)

    # Check if it has remote dependencies
    if "://" not in config.base_project:
        message = _render_validation_message("no_remote_dependencies", project_path=project_path)
        print(message)
        return None

    return project_path, config


def _create_plugin_with_optional_stub_update(
    plugin_type: str,
    project_path: Path,
    plugin_name: str,
    update_pyi: bool
) -> Path:
    """Create a plugin with optional stub update."""
    if update_pyi:
        # Create plugin without automatic stub update, then update manually
        file_path = create_plugin_file(plugin_type, project_path, plugin_name)
        update_project_stub(project_path, silent=False)
        return file_path
    else:
        # Use the standard function which updates stub silently
        if plugin_type == PLUGIN_TYPE_THEN:
            return create_then_plugin(project_path, plugin_name)
        elif plugin_type == PLUGIN_TYPE_AS:
            return create_as_plugin(project_path, plugin_name)
        elif plugin_type == PLUGIN_TYPE_PROCESSOR:
            return create_processor(project_path, plugin_name)
        else:
            _die(f"Unknown plugin type: {plugin_type}")
            return Path()  # Never reached, but satisfies type checker


def _generate_plugin_success_message(
    plugin_type: str,
    plugin_name: str,
    file_path: Path,
    update_pyi: bool
) -> str:
    """Generate plugin success message using Jinja2 template."""
    # Map plugin types to their prefixes and method types
    plugin_config = {
        PLUGIN_TYPE_THEN: {
            "prefix": PLUGIN_PREFIX_THEN,
            "method_type": "Method name",
            "usage_example": f".{PLUGIN_PREFIX_THEN}{plugin_name}(\n        params\n    )"
        },
        PLUGIN_TYPE_AS: {
            "prefix": PLUGIN_PREFIX_AS,
            "method_type": "Method name",
            "usage_example": f".{PLUGIN_PREFIX_AS}{plugin_name}(\n        params\n    )"
        },
        PLUGIN_TYPE_PROCESSOR: {
            "prefix": "",  # Processors don't have prefixes in the name
            "method_type": "Processor name",
            "usage_example": f".then_process(\n        {plugin_name}(params)\n    )"
        }
    }

    config = plugin_config.get(plugin_type)
    if not config:
        _die(f"Unknown plugin type: {plugin_type}")
        return ""  # Never reached, but satisfies type checker

    stub_message = MSG_PLUGIN_STUB_UPDATED if update_pyi else ""
    stub_help_message = "" if update_pyi else MSG_PLUGIN_STUB_HELP

    context = {
        "plugin_prefix": config["prefix"],
        "plugin_name": plugin_name,
        "plugin_type": plugin_type,
        "file_path": file_path,
        "method_type": config["method_type"],
        "stub_message": stub_message,
        "stub_help_message": stub_help_message,
        "usage_example": config["usage_example"]
    }

    return render_template(TEMPLATE_PLUGIN_SUCCESS, **context)


def _render_validation_message(message_type: str, **context) -> str:
    """Render validation message using template."""
    return render_template(TEMPLATE_VALIDATION_MESSAGES, message_type=message_type, **context)


def _render_project_list_message(projects: list, active_project: Path | None) -> str:
    """Render project list message using template."""
    return render_template(TEMPLATE_PROJECT_LIST,
                          projects=projects,
                          active_project=active_project,
                          no_projects_message=MSG_NO_PROJECTS_FOUND,
                          available_projects_message=MSG_AVAILABLE_PROJECTS,
                          active_marker=MSG_ACTIVE_PROJECT_MARKER)


def _render_shell_reload_message(reload_command: str) -> str:
    """Render shell reload message using template."""
    return render_template(TEMPLATE_SHELL_RELOAD, reload_command=reload_command)


def _render_remote_chain_update_message(project_path: Path, base_project: str,
                                       force_update: bool, has_changes: bool,
                                       updated_chains: list = None) -> str:
    """Render remote chain update message using template."""
    updated_count = len(updated_chains) if updated_chains else 0
    updated_chain_names = [chain.name for chain in updated_chains] if updated_chains else []

    return render_template(TEMPLATE_REMOTE_CHAIN_UPDATE,
                          project_path=project_path,
                          base_project=base_project,
                          force_update=force_update,
                          has_changes=has_changes,
                          updated_count=updated_count,
                          updated_chains=updated_chain_names)


def _render_remote_chain_check_message(project_path: Path, has_changes: bool) -> str:
    """Render remote chain check message using template."""
    return render_template(TEMPLATE_REMOTE_CHAIN_CHECK,
                          project_path=project_path,
                          has_changes=has_changes)


def _render_remote_chain_list_message(project_name: str, remote_chains: list, verbose: bool) -> str:
    """Render remote chain list message using template."""
    return render_template(TEMPLATE_REMOTE_CHAIN_LIST,
                          project_name=project_name,
                          remote_chains=remote_chains,
                          verbose=verbose)


def _render_remote_chain_status_message(project_name: str, status: dict) -> str:
    """Render remote chain status message using template."""
    total_chains = len(status['remote_chains'])
    chains_with_updates = sum(1 for c in status['remote_chains'] if c['has_updates'])
    total_size = sum(c['size_mb'] for c in status['remote_chains'])

    return render_template(TEMPLATE_REMOTE_CHAIN_STATUS,
                          project_name=project_name,
                          status=status,
                          total_chains=total_chains,
                          chains_with_updates=chains_with_updates,
                          total_size=total_size)


def _handle_remote_chain_service_error(e: Exception, operation: str) -> None:
    """Handle ProjectRemoteChainServiceError with consistent error reporting."""
    if isinstance(e, ProjectRemoteChainServiceError):
        _die(f"❌ Failed to {operation}: {e}")
    else:
        _die(f"❌ Unexpected error: {e}")


def _handle_generic_error(e: Exception, operation: str) -> None:
    """Handle generic exceptions with consistent error reporting."""
    _die(f"Failed to {operation}: {e}")


def _validate_base_project_if_not_default(base_project: str, credentials: dict | None = None) -> None:
    """Validate base project if it's not the default chainedpy."""
    if base_project != DEFAULT_BASE_PROJECT:
        try:
            if credentials is None:
                credentials = merge_credentials()  # Load from environment
            validate_base_project(base_project, credentials)

            if URL_SCHEME_SEPARATOR in base_project:
                message = _render_validation_message("validated_remote_project", base_project=base_project)
                get_logger().info(message)
                print(message, file=sys.stderr)

        except ProjectValidationError as e:
            _die(str(e))


def _create_plugin_handler(plugin_type: str, args: argparse.Namespace) -> None:
    """Generic plugin creation handler to eliminate duplication."""
    try:
        project_path = _resolve_project_path(args)
        validate_local_project(project_path)

        update_pyi = getattr(args, ARG_UPDATE_PYI, False)

        # Get plugin name based on plugin type
        if plugin_type == PLUGIN_TYPE_PROCESSOR:
            plugin_name = args.name
        else:
            plugin_name = args.name_after_prefix

        file_path = _create_plugin_with_optional_stub_update(
            plugin_type, project_path, plugin_name, update_pyi
        )

        success_message = _generate_plugin_success_message(
            plugin_type, plugin_name, file_path, update_pyi
        )
        _positive_exit(success_message)
    except Exception as e:
        _handle_generic_error(e, f"create {plugin_type} plugin")


def handle_create_project(args: argparse.Namespace) -> None:
    """Handle create-project command.

    Example:
        ```python
        from chainedpy.services.command_handlers import handle_create_project
        import argparse

        # Create namespace with required arguments
        args = argparse.Namespace(
            dest="./my_project",
            name="my_project",
            base_project="chainedpy",
            summary="My test project",
            github_token=None,
            gitlab_token=None,
            activate=False
        )

        # Handle project creation
        handle_create_project(args)
        # This will create the project and display success message

        # With activation
        args.activate = True
        handle_create_project(args)
        # This will create and activate the project
        ```

    :param args: Parsed command line arguments.
    :type args: [argparse.Namespace][argparse.Namespace]
    """
    # Extract arguments
    base_project = getattr(args, ARG_BASE_PROJECT, DEFAULT_BASE_PROJECT)
    summary = getattr(args, ARG_SUMMARY, None)
    github_token = getattr(args, ARG_GITHUB_TOKEN, None)
    gitlab_token = getattr(args, ARG_GITLAB_TOKEN, None)

    # Validate base project if not chainedpy
    credentials = merge_credentials(github_token, gitlab_token)
    _validate_base_project_if_not_default(base_project, credentials)

    # Create the project
    try:
        proj_dir = create_project(
            args.dest, args.name, base_project=base_project, summary=summary
        )

        # Handle credential tokens if provided via CLI
        if github_token or gitlab_token:
            try:
                create_env_file(proj_dir, github_token, gitlab_token)
            except CredentialServiceError as e:
                message = _render_validation_message("credential_warning", warning_message=str(e))
                get_logger().error(message)
                print(message, file=sys.stderr)
    except Exception as e:
        _handle_generic_error(e, "create project")

    # Automatically activate the newly created project
    try:
        activate_project(proj_dir)
        message = render_template(TEMPLATE_PROJECT_CREATED_ACTIVATED, project_dir=proj_dir)
        _positive_exit(message)
    except Exception:
        # If activation fails, still show success but mention manual activation
        message = render_template(TEMPLATE_PROJECT_CREATED_MANUAL_ACTIVATION, project_dir=proj_dir)
        _positive_exit(message)


def handle_set_global_project(args: argparse.Namespace) -> None:
    """Handle set-global-project command."""
    try:
        set_global_project(args.project_path)
        _positive_exit(MSG_SUCCESS_GLOBAL_PROJECT_SET)
    except Exception as e:
        _handle_generic_error(e, "set global project")


def handle_activate_project(args: argparse.Namespace) -> None:
    """Handle activate-project command."""
    try:
        shell_code = generate_activation_script(args.project_path, args.shell)
        get_logger().info(shell_code)
    except (FileNotFoundError, ShellIntegrationError) as e:
        _die(str(e))


def handle_deactivate_project(args: argparse.Namespace) -> None:
    """Handle deactivate-project command."""
    try:
        shell_code = generate_deactivation_script(args.shell)
        get_logger().info(shell_code)
    except ShellIntegrationError as e:
        _die(str(e))


def handle_init(args: argparse.Namespace) -> None:
    """Handle init command."""
    try:
        result = initialize_shell_integration(args.shell, args.dry_run, args.force)
        get_logger().info(result)
    except ShellIntegrationError as e:
        _die(str(e))


def handle_reload(args: argparse.Namespace) -> None:
    """Handle reload command."""
    try:
        reload_cmd = get_reload_command(args.shell)
        message = _render_shell_reload_message(reload_cmd)
        print(message)
    except ShellIntegrationError as e:
        _die(str(e))


def handle_list_projects(args: argparse.Namespace) -> None:
    """Handle list-projects command."""
    try:
        if not args.search_paths:
            get_logger().warning("No search paths provided. Use --search-paths to specify directories to search for projects. Seraching in Path.cwd()...")
            projects = list_projects([Path.cwd()])
        else:
            projects = list_projects(args.search_paths)


        active = project_get_active_project()

        message = _render_project_list_message(projects, active)
        print(message)
    except Exception as e:
        _handle_generic_error(e, "list projects")


def handle_update_project_pyi(args: argparse.Namespace) -> None:
    """Handle update-project-pyi command."""
    try:
        project_path = _resolve_project_path(args)
        project_update_project_stub(project_path)
        _positive_exit("Stub regenerated")
    except Exception as e:
        _handle_generic_error(e, "update project stub")


def handle_update_base_project(args: argparse.Namespace) -> None:
    """Handle update-base-project command."""

    project_path = _resolve_project_path(args)
    try:
        validate_local_project(project_path)
    except Exception as e:
        _handle_generic_error(e, "validate local project")
    new_base_project = args.new_base_project
    summary = getattr(args, ARG_SUMMARY, None)

    # Validate new base project if not chainedpy
    _validate_base_project_if_not_default(new_base_project)

    try:
        update_project_base(project_path, new_base_project, summary)
        _positive_exit(f"Base project updated to: {new_base_project}")
    except Exception as e:
        _handle_generic_error(e, "update base project")


def handle_create_then_plugin(args: argparse.Namespace) -> None:
    """Handle create-then-plugin command."""
    _create_plugin_handler(PLUGIN_TYPE_THEN, args)


def handle_create_as_plugin(args: argparse.Namespace) -> None:
    """Handle create-as-plugin command."""
    _create_plugin_handler(PLUGIN_TYPE_AS, args)


def handle_create_processor(args: argparse.Namespace) -> None:
    """Handle create-processor command."""
    _create_plugin_handler(PLUGIN_TYPE_PROCESSOR, args)


def handle_show_project_chain(args: argparse.Namespace) -> None:
    """Handle show-project-chain command."""
    try:
        project_path = _resolve_project_path(args)
        result = show_project_chain(project_path)
        # Main command output should go to stdout for CLI users and tests
        print(result)
        # Exit with success code to match test expectations
        sys.exit(0)
    except Exception as e:
        _handle_generic_error(e, "show project chain")



def handle_update_remote_chains(args: argparse.Namespace) -> None:
    """Handle update-remote-chains command."""
    try:
        project_path = _resolve_remote_project_path(args)
        result = _validate_remote_chainedpy_project(project_path)
        if result is None:
            return
        project_path, config = result

        # Check for changes if not forcing update
        force_update = getattr(args, ARG_FORCE, False)
        has_changes = True  # Default to true for force updates

        if not force_update:
            has_changes = detect_chain_changes(project_path, config.base_project)
            if not has_changes:
                message = _render_remote_chain_update_message(
                    project_path, config.base_project, force_update, has_changes
                )
                print(message)
                return

        # Update the chains
        updated_chains = update_project_chains(config.base_project, project_path)

        # Update the chain file
        base_import = get_project_chain_import(config.base_project, project_path)
        _update_chain_file_with_import(project_path, project_path.name, base_import)

        # Render success message
        message = _render_remote_chain_update_message(
            project_path, config.base_project, force_update, has_changes, updated_chains
        )
        print(message)

    except Exception as e:
        _handle_remote_chain_service_error(e, "update remote chains")


def handle_check_remote_updates(args: argparse.Namespace) -> None:
    """Handle check-remote-updates command."""
    try:
        project_path = _resolve_remote_project_path(args)
        result = _validate_remote_chainedpy_project(project_path)
        if result is None:
            return
        project_path, config = result

        # Check for changes without downloading
        has_changes = detect_chain_changes(project_path, config.base_project)

        message = _render_remote_chain_check_message(project_path, has_changes)
        print(message)

    except Exception as e:
        _handle_remote_chain_service_error(e, "check remote updates")


def handle_list_remote_chains(args: argparse.Namespace) -> None:
    """Handle list-remote-chains command."""
    try:
        project_path = _resolve_remote_project_path(args)
        result = _validate_remote_chainedpy_project(project_path)
        if result is None:
            return
        project_path, config = result

        # List remote chains
        remote_chains = list_project_remote_chains(project_path, config.base_project)

        verbose = getattr(args, ARG_VERBOSE, False)

        message = _render_remote_chain_list_message(project_path.name, remote_chains, verbose)
        print(message)

    except Exception as e:
        _handle_remote_chain_service_error(e, "list remote chains")


def handle_remote_chain_status(args: argparse.Namespace) -> None:
    """Handle remote-chain-status command."""
    try:
        project_path = _resolve_remote_project_path(args)
        result = _validate_remote_chainedpy_project(project_path)
        if result is None:
            return
        project_path, config = result

        # Get detailed status
        status = get_remote_chain_status(project_path, config.base_project)

        message = _render_remote_chain_status_message(project_path.name, status)
        print(message)

    except Exception as e:
        _handle_remote_chain_service_error(e, "get remote chain status")

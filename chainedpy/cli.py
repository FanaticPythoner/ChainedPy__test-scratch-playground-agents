"""ChainedPy Command Line Interface.

This module provides the main CLI entry point and argument parsing for all ChainedPy commands.
It handles project creation, management, plugin generation, shell integration, and remote chain
management. The CLI is designed to provide a comprehensive set of tools for working with
ChainedPy projects throughout their entire lifecycle.

The module delegates actual command execution to service handlers in [chainedpy.services.command_handlers][chainedpy.services.command_handlers],
maintaining clean separation between argument parsing and business logic. This design ensures
that CLI functionality can be easily tested and reused programmatically.

Note:
    All command handlers are imported from the services layer to maintain proper
    separation of concerns. The CLI module focuses solely on argument parsing
    and command routing.

Example:
    ```bash
    # Create a new project
    chainedpy create-project --name myproject --dest ./projects

    # Activate a project for shell integration
    eval "$(chainedpy activate-project --project-path ./myproject)"

    # Create a new plugin
    chainedpy create-then-plugin --name-after-prefix send_email

    # Update remote chains
    chainedpy update-remote-chains --project-path ./myproject
    ```

See Also:
    - [command_handlers][chainedpy.services.command_handlers]: Service layer command implementations
    - [constants][chainedpy.constants]: CLI command constants and defaults
    - [main][chainedpy.cli.main]: Main CLI entry point function
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from chainedpy.constants import (
    # CLI commands
    CMD_CREATE_PROJECT, CMD_SET_GLOBAL_PROJECT, CMD_ACTIVATE_PROJECT,
    CMD_DEACTIVATE_PROJECT, CMD_INIT, CMD_RELOAD, CMD_LIST_PROJECTS,
    CMD_UPDATE_PROJECT_PYI, CMD_UPDATE_BASE_PROJECT, CMD_CREATE_THEN_PLUGIN,
    CMD_CREATE_AS_PLUGIN, CMD_CREATE_PROCESSOR, CMD_SHOW_PROJECT_CHAIN,
    # Remote chain management commands (project-local)
    CMD_UPDATE_REMOTE_CHAINS, CMD_CHECK_REMOTE_UPDATES, CMD_LIST_REMOTE_CHAINS, CMD_REMOTE_CHAIN_STATUS,
    # Default values
    DEFAULT_BASE_PROJECT, DEFAULT_SUMMARY_FORMAT,
    # Shell types
    SUPPORTED_SHELLS
)

# Import command handlers from services
from chainedpy.services.command_handlers import (
    handle_create_project,
    handle_set_global_project,
    handle_activate_project,
    handle_deactivate_project,
    handle_init,
    handle_reload,
    handle_list_projects,
    handle_update_project_pyi,
    handle_update_base_project,
    handle_create_then_plugin,
    handle_create_as_plugin,
    handle_create_processor,
    handle_show_project_chain,
    # Remote chain management handlers (project-local)
    handle_update_remote_chains,
    handle_check_remote_updates,
    handle_list_remote_chains,
    handle_remote_chain_status,
    _die
)



def _path(path_like: str) -> Path:
    """Convert path-like string to resolved Path object.


    Note:
        This function expands user home directory (~) and resolves relative paths
        to absolute paths, ensuring consistent path handling across the CLI.

    Example:
        ```python
        from chainedpy.cli import _path

        # Convert relative path
        path = _path("./myproject")
        assert path.is_absolute()

        # Expand user home directory
        path = _path("~/projects/myproject")
        assert str(path).startswith("/")

        # Handle already absolute paths
        path = _path("/absolute/path/to/project")
        assert path == Path("/absolute/path/to/project")
        ```
    :param path_like: Path-like string to convert.
    :type path_like: [str][str]
    :return [Path][pathlib.Path]: Resolved Path object.
    """
    # @@ STEP 1: Convert to Path and resolve. @@
    return Path(path_like).expanduser().resolve()


def _build_parser() -> argparse.ArgumentParser:
    """Build the argument parser for the CLI.

    Note:
        This function creates a comprehensive argument parser with subcommands for
        all ChainedPy operations including project management, plugin creation,
        shell integration, and remote chain management.

    Example:
        ```python
        from chainedpy.cli import _build_parser

        # Build the parser
        parser = _build_parser()

        # Parse create-project command
        args = parser.parse_args([
            "create-project",
            "--name", "myproject",
            "--dest", "./projects"
        ])
        assert args.cmd == "create-project"
        assert args.name == "myproject"

        # Parse plugin creation command
        args = parser.parse_args([
            "create-then-plugin",
            "--name-after-prefix", "send_email"
        ])
        assert args.cmd == "create-then-plugin"
        ```

    :return [argparse.ArgumentParser][argparse.ArgumentParser]: Configured argument parser.
    """
    # @@ STEP 1: Create root parser and subparsers. @@
    root = argparse.ArgumentParser(prog="chainedpy", description="ChainedPy CLI")
    sub = root.add_subparsers(dest="cmd", required=True)

    # @@ STEP 2: Define project creation command. @@
    p = sub.add_parser(CMD_CREATE_PROJECT, help="Scaffold a new project")
    p.add_argument("--name", required=True, help="Project (package) name")
    p.add_argument("--dest", required=True, type=_path, help="Destination folder")
    p.add_argument("--base-project", type=str, default=DEFAULT_BASE_PROJECT,
                   help=f"Base project to extend (default: {DEFAULT_BASE_PROJECT}). "
                        f"Can be '{DEFAULT_BASE_PROJECT}', local path, or remote URL "
                        "(e.g., https://github.com/user/repo)")
    p.add_argument("--github-token", type=str,
                   help="GitHub token for private repository access")
    p.add_argument("--gitlab-token", type=str,
                   help="GitLab token for private repository access")
    p.add_argument("--create-env", action="store_true",
                   help="Create .env file with credential placeholders")
    p.add_argument("--summary", type=str,
                   help="Short summary of what this project does "
                        f"(default: '{DEFAULT_SUMMARY_FORMAT}')")

    # @@ STEP 3: Define project management commands. @@
    p = sub.add_parser(CMD_SET_GLOBAL_PROJECT, help="Patch imports to use project chain (permanent)")
    p.add_argument("--project-path", required=True, type=_path, help="Project root path")

    # @@ STEP 4: Define shell integration commands. @@
    p = sub.add_parser(CMD_ACTIVATE_PROJECT,
                       help="Generate shell code to activate project (use with eval)")
    p.add_argument("--project-path", required=True, type=_path, help="Project root path")
    p.add_argument("--shell",
                   choices=SUPPORTED_SHELLS,
                   default="bash", help="Shell type for generated code")

    p = sub.add_parser(CMD_DEACTIVATE_PROJECT,
                       help="Generate shell code to deactivate current project (use with eval)")
    p.add_argument("--shell",
                   choices=SUPPORTED_SHELLS,
                   default="bash", help="Shell type for generated code")

    p = sub.add_parser(CMD_INIT,
                       help="Initialize ChainedPy shell integration (like conda init)")
    p.add_argument("--shell",
                   choices=SUPPORTED_SHELLS,
                   help="Shell type (auto-detected if not specified)")
    p.add_argument("--dry-run", action="store_true",
                   help="Show what would be done without making changes")
    p.add_argument("--force", action="store_true",
                   help="Force reinitialize even if already configured")

    p = sub.add_parser(CMD_RELOAD,
                       help="Generate command to reload shell configuration")
    p.add_argument("--shell",
                   choices=SUPPORTED_SHELLS,
                   help="Shell type (auto-detected if not specified)")

    # @@ STEP 5: Define project listing and management commands. @@
    p = sub.add_parser(CMD_LIST_PROJECTS, help="List available projects and show active project")
    p.add_argument("--search-paths", nargs="*", type=_path,
                   help="Additional paths to search for projects")

    p = sub.add_parser(CMD_UPDATE_PROJECT_PYI, help="Regenerate .pyi stub")
    p.add_argument("--project-path", type=_path,
                   help="Project root path (uses active project if not specified)")

    p = sub.add_parser(CMD_UPDATE_BASE_PROJECT, help="Change which project this project extends")
    p.add_argument("--project-path", type=_path,
                   help="Project root path (uses active project if not specified)")
    p.add_argument("--new-base-project", required=True, type=str,
                   help=f"New base project to extend. Can be '{DEFAULT_BASE_PROJECT}', local path, "
                        "or remote URL (e.g., https://github.com/user/repo)")
    p.add_argument("--summary", type=str,
                   help="Optional: Update project summary as well")

    # @@ STEP 6: Define plugin creation commands. @@
    p = sub.add_parser(CMD_CREATE_THEN_PLUGIN, help="Generate a then_* plugin skeleton")
    p.add_argument("--name-after-prefix", required=True, help="E.g. 'send_http'")
    p.add_argument("--project-path", type=_path,
                   help="Project root path (uses active project if not specified)")
    p.add_argument("--update-pyi", action="store_true",
                   help="Automatically update the .pyi stub file after creating the plugin")

    p = sub.add_parser(CMD_CREATE_AS_PLUGIN, help="Generate an as_* plugin skeleton")
    p.add_argument("--name-after-prefix", required=True, help="E.g. 'redis_cache'")
    p.add_argument("--project-path", type=_path,
                   help="Project root path (uses active project if not specified)")
    p.add_argument("--update-pyi", action="store_true",
                   help="Automatically update the .pyi stub file after creating the plugin")

    p = sub.add_parser(CMD_CREATE_PROCESSOR, help="Generate a processor plugin skeleton")
    p.add_argument("--name", required=True, help="Processor name (snake_case)")
    p.add_argument("--project-path", type=_path,
                   help="Project root path (uses active project if not specified)")
    p.add_argument("--update-pyi", action="store_true",
                   help="Automatically update the .pyi stub file after creating the plugin")

    # @@ STEP 7: Define project chain display command. @@
    p = sub.add_parser(CMD_SHOW_PROJECT_CHAIN, help="Show the inheritance chain for a project")
    p.add_argument("--project-path", type=_path,
                   help="Project root path (uses active project if not specified)")

    # @@ STEP 8: Define remote chain management commands. @@
    p = sub.add_parser(CMD_UPDATE_REMOTE_CHAINS, help="Update remote chains in a project")
    p.add_argument("--project-path", type=_path,
                   help="Project root path (uses active project if not specified)")
    p.add_argument("--force", action="store_true",
                   help="Force update even if no changes are detected")

    p = sub.add_parser(CMD_CHECK_REMOTE_UPDATES, help="Check for updates to remote chains without downloading")
    p.add_argument("--project-path", type=_path,
                   help="Project root path (uses active project if not specified)")

    p = sub.add_parser(CMD_LIST_REMOTE_CHAINS, help="List all remote chains used by a project")
    p.add_argument("--project-path", type=_path,
                   help="Project root path (uses active project if not specified)")
    p.add_argument("--verbose", "-v", action="store_true",
                   help="Show detailed information about each remote chain")

    p = sub.add_parser(CMD_REMOTE_CHAIN_STATUS, help="Show detailed status of remote chains")
    p.add_argument("--project-path", type=_path,
                   help="Project root path (uses active project if not specified)")

    # @@ STEP 9: Return configured parser. @@
    return root

def main(argv: list[str] | None = None) -> None:  # pragma: no cover
    """Main CLI entry point - refactored to use service handlers.

    Note:
        This function serves as the main entry point for the ChainedPy CLI. It parses
        command line arguments and routes them to appropriate service handlers. All
        business logic is delegated to the service layer for better testability.

    Example:
        ```python
        from chainedpy.cli import main

        # Programmatic CLI usage
        main(["create-project", "--name", "myproject", "--dest", "./projects"])

        # Create a plugin
        main([
            "create-then-plugin",
            "--name-after-prefix", "send_email",
            "--project-path", "./myproject"
        ])

        # List projects
        main(["list-projects"])

        # Error handling is built-in
        try:
            main(["invalid-command"])
        except SystemExit:
            print("Command failed as expected")
        ```

    :param argv: Command line arguments, defaults to None.
    :type argv: [list][list][[str][str]] | [None][None], optional
    """
    # @@ STEP 1: Parse command line arguments. @@
    args = _build_parser().parse_args(argv or sys.argv[1:])
    cmd = args.cmd

    # @@ STEP 2: Route commands to appropriate service handlers. @@
    try:
        if cmd == CMD_CREATE_PROJECT:
            handle_create_project(args)
        elif cmd == CMD_SET_GLOBAL_PROJECT:
            handle_set_global_project(args)
        elif cmd == CMD_ACTIVATE_PROJECT:
            handle_activate_project(args)
        elif cmd == CMD_DEACTIVATE_PROJECT:
            handle_deactivate_project(args)
        elif cmd == CMD_INIT:
            handle_init(args)
        elif cmd == CMD_RELOAD:
            handle_reload(args)
        elif cmd == CMD_LIST_PROJECTS:
            handle_list_projects(args)
        elif cmd == CMD_UPDATE_PROJECT_PYI:
            handle_update_project_pyi(args)
        elif cmd == CMD_UPDATE_BASE_PROJECT:
            handle_update_base_project(args)
        elif cmd == CMD_CREATE_THEN_PLUGIN:
            handle_create_then_plugin(args)
        elif cmd == CMD_CREATE_AS_PLUGIN:
            handle_create_as_plugin(args)
        elif cmd == CMD_CREATE_PROCESSOR:
            handle_create_processor(args)
        elif cmd == CMD_SHOW_PROJECT_CHAIN:
            handle_show_project_chain(args)
        # Remote chain management commands (project-local)
        elif cmd == CMD_UPDATE_REMOTE_CHAINS:
            handle_update_remote_chains(args)
        elif cmd == CMD_CHECK_REMOTE_UPDATES:
            handle_check_remote_updates(args)
        elif cmd == CMD_LIST_REMOTE_CHAINS:
            handle_list_remote_chains(args)
        elif cmd == CMD_REMOTE_CHAIN_STATUS:
            handle_remote_chain_status(args)
        else:
            _die(f"Unknown command: {cmd}")

    except Exception as exc:
        _die(str(exc))

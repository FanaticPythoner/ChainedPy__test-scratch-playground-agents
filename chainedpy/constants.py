"""ChainedPy Constants.

This module provides centralized constants for all hardcoded strings, paths, and configuration
values used across the ChainedPy project. By centralizing these values, we eliminate technical
debt from scattered string literals and make maintenance significantly easier.

The constants are organized into logical groups including filesystem paths, file names,
environment variables, project structure, CLI commands, template paths, and default values.
All constants follow the SCREAMING_SNAKE_CASE naming convention with descriptive prefixes
to indicate their domain (ENV_, CMD_, TEMPLATE_, etc.).

Note:
    Constants are organized from most fundamental to most complex, with later constants
    building upon earlier ones where possible. This reduces duplication and ensures
    consistency across the codebase.

Example:
    ```python
    from chainedpy.constants import (
        CONFIG_FILE_NAME, PLUGINS_DIR, CMD_CREATE_PROJECT,
        TEMPLATE_PROJECT_CHAIN_PY, DEFAULT_BASE_PROJECT
    )

    # Use constants instead of hardcoded strings
    config_path = project_root / CONFIG_FILE_NAME
    plugins_path = project_root / PLUGINS_DIR

    # CLI command constants
    if command == CMD_CREATE_PROJECT:
        handle_create_project()

    # Template path constants
    template_path = template_dir / TEMPLATE_PROJECT_CHAIN_PY
    ```

See Also:
    - [chainedpy.cli][chainedpy.cli]: CLI module that uses command constants
    - [chainedpy.services.template_service][chainedpy.services.template_service]: Template service using template path constants
    - [chainedpy.services.filesystem_service][chainedpy.services.filesystem_service]: Filesystem service using file name constants
"""
from __future__ import annotations

from pathlib import Path


# TODO: A LOT OF THESE ARE NOT USING THE OTHER CONSTANTS. THEY SHOULD BE ORDERED FROM SMALLEST & MOST REUSED TO LARGEST & LEAST REUSED. THEN THE OTHER CONSTANTS SHOULD REUSE THE ONES THAT ARE REUSABLE. NOT HARDCODE IT THEMSELVES.

# @@ STEP 1: Define filesystem constants. @@

PYCACHE_DIR = "__pycache__"
"""[str][str]: Standard Python cache directory name.

Used for identifying and excluding Python bytecode cache directories
during project operations and file system traversals.

:type: [str][str]
"""

# @@ STEP 2: Define file names and extensions. @@
CONFIG_FILE_NAME = "chainedpy.yaml"
"""[str][str]: Configuration file name for ChainedPy projects.

:type: [str][str]
"""

INIT_FILE_NAME = "__init__.py"
"""[str][str]: Standard Python package initialization file name.

:type: [str][str]
"""

CHAIN_FILE_SUFFIX = "_chain.py"
"""[str][str]: Suffix for chain implementation files.

:type: [str][str]
"""

PYI_FILE_SUFFIX = "_chain.pyi"
"""[str][str]: Suffix for chain type stub files.

:type: [str][str]
"""

PYTHON_EXTENSION = ".py"
"""[str][str]: Standard Python file extension.

:type: [str][str]
"""

PYI_EXTENSION = ".pyi"
"""[str][str]: Python type stub file extension.

:type: [str][str]
"""

JINJA_EXTENSION = ".j2"
"""[str][str]: Jinja2 template file extension.

:type: [str][str]
"""

ENV_FILE_NAME = ".env"
"""[str][str]: Environment variables file name.

:type: [str][str]
"""

ENV_FILE_EXTENSION = ".env"
"""[str][str]: Environment file extension.

:type: [str][str]
"""

DEFAULT_ENV_FILE_NAME = "default.env"
"""[str][str]: Default environment template file name.

:type: [str][str]
"""

# @@ STEP 3: Define environment variables. @@
ENV_ACTIVE_PROJECT = "CHAINEDPY_ACTIVE_PROJECT"
"""[str][str]: Environment variable for tracking the currently active ChainedPy project.

:type: [str][str]
"""

ENV_PROJECT_NAME = "CHAINEDPY_PROJECT_NAME"
"""[str][str]: Environment variable for storing the active project name.

:type: [str][str]
"""

ENV_PROJECT_STACK = "CHAINEDPY_PROJECT_STACK"
"""[str][str]: Environment variable for tracking nested project activations.

:type: [str][str]
"""

ENV_SHELL = "SHELL"
"""[str][str]: Standard shell environment variable.

:type: [str][str]
"""

ENV_PS_MODULE_PATH = "PSModulePath"
"""[str][str]: PowerShell module path environment variable.

:type: [str][str]
"""

# @@ STEP 4: Define project structure constants. @@
PLUGINS_DIR = "plugins"
THEN_DIR = "then"
AS_DIR = "as_"
PROCESSORS_DIR = "processors"
CHAINEDPY_DIR = ".chainedpy"
CREDENTIALS_DIR = "credentials"
TEMPLATE_DIR = "tpl"
PACKAGE_NAME = "chainedpy"
CHAIN_CLASS_NAME = "Chain"

# || S.S. 4.1: Define plugin directory paths (relative to project root). ||
PLUGINS_THEN_PATH = f"{PLUGINS_DIR}/{THEN_DIR}"
PLUGINS_AS_PATH = f"{PLUGINS_DIR}/{AS_DIR}"
PLUGINS_PROCESSORS_PATH = f"{PLUGINS_DIR}/{PROCESSORS_DIR}"

# @@ STEP 5: Define default values. @@
DEFAULT_BASE_PROJECT = "chainedpy"
DEFAULT_SUMMARY_TEMPLATE = "ChainedPy project: {project_name}"
DEFAULT_SUMMARY_FORMAT = "ChainedPy project: {}"

# @@ STEP 6: Define shell types and supported shells. @@
SHELL_BASH = "bash"
SHELL_ZSH = "zsh"
SHELL_SH = "sh"
SHELL_FISH = "fish"
SHELL_CMD = "cmd"
SHELL_BATCH = "batch"
SHELL_POWERSHELL = "powershell"

# || S.S. 6.1: Define all supported shells list. ||
SUPPORTED_SHELLS = [
    SHELL_BASH, SHELL_ZSH, SHELL_SH, SHELL_FISH,
    SHELL_CMD, SHELL_BATCH, SHELL_POWERSHELL
]

# @@ STEP 7: Define template paths. @@

# || S.S. 7.1: Define project templates. ||
TEMPLATE_PROJECT_CHAIN_PY = "project/chain_py.j2"
TEMPLATE_PROJECT_INIT_PY = "project/init_py.j2"

# || S.S. 7.2: Define config templates. ||
TEMPLATE_CONFIG_YAML = "config/chainedpy_yaml.j2"

# || S.S. 7.3: Define plugin templates. ||
TEMPLATE_THEN_PLUGIN = "plugins/then_plugin.j2"
TEMPLATE_AS_PLUGIN = "plugins/as_plugin.j2"
TEMPLATE_PROCESSOR_PLUGIN = "plugins/processor_plugin.j2"

# || S.S. 7.4: Define stub templates. ||
TEMPLATE_STUB_PYI = "stub/chain_pyi.j2"

# || S.S. 7.5: Define shell activation templates. ||
TEMPLATE_ACTIVATION_BASH = "shell/activation_bash.j2"
TEMPLATE_ACTIVATION_CMD = "shell/activation_cmd.j2"
TEMPLATE_ACTIVATION_FISH = "shell/activation_fish.j2"
TEMPLATE_ACTIVATION_POWERSHELL = "shell/activation_powershell.j2"

# || S.S. 7.6: Define import templates. ||
TEMPLATE_BASE_IMPORT_CHAINEDPY = "imports/base_import_chainedpy.j2"
TEMPLATE_BASE_IMPORT_REMOTE = "imports/base_import_remote.j2"
TEMPLATE_BASE_IMPORT_CUSTOM = "imports/base_import_custom.j2"
TEMPLATE_BASE_IMPORT_LOCAL = "imports/base_import_local.j2"
TEMPLATE_TYPEVAR_IMPORT = "imports/typevar_import.j2"

# || S.S. 7.7: Define shell init templates. ||
TEMPLATE_SHELL_INIT_DRY_RUN = "shell/init_dry_run_status.j2"
TEMPLATE_SHELL_INIT_SUCCESS = "shell/init_success_message.j2"

# || S.S. 7.8: Define shell deactivation templates. ||
TEMPLATE_DEACTIVATION_BASH = "shell/deactivation_bash.j2"
TEMPLATE_DEACTIVATION_CMD = "shell/deactivation_cmd.j2"
TEMPLATE_DEACTIVATION_FISH = "shell/deactivation_fish.j2"
TEMPLATE_DEACTIVATION_POWERSHELL = "shell/deactivation_powershell.j2"

# || S.S. 7.9: Define shell init templates. ||
TEMPLATE_INIT_BASH = "shell/init_bash.j2"
TEMPLATE_INIT_CMD = "shell/init_cmd.j2"
TEMPLATE_INIT_FISH = "shell/init_fish.j2"
TEMPLATE_INIT_POWERSHELL = "shell/init_powershell.j2"

# || S.S. 7.10: Define message templates. ||
TEMPLATE_PLUGIN_SUCCESS = "messages/plugin_success.j2"
TEMPLATE_REMOTE_CHAIN_UPDATE = "messages/remote_chain_update.j2"
TEMPLATE_REMOTE_CHAIN_CHECK = "messages/remote_chain_check.j2"
TEMPLATE_REMOTE_CHAIN_LIST = "messages/remote_chain_list.j2"
TEMPLATE_REMOTE_CHAIN_STATUS = "messages/remote_chain_status.j2"
TEMPLATE_PROJECT_LIST = "messages/project_list.j2"
TEMPLATE_SHELL_RELOAD = "messages/shell_reload.j2"
TEMPLATE_VALIDATION_MESSAGES = "messages/validation_messages.j2"
TEMPLATE_PROJECT_CHAIN = "messages/project_chain.j2"
TEMPLATE_STALE_PROJECT_WARNING = "messages/stale_project_warning.j2"
TEMPLATE_STALE_PROJECT_CLEANUP_SUCCESS = "messages/stale_project_cleanup_success.j2"
TEMPLATE_GITIGNORE_ENTRY = "gitignore/entry.j2"
TEMPLATE_METHOD_SIGNATURE = "ast/method_signature.j2"
TEMPLATE_OVERLOAD_SIGNATURE = "ast/overload_signature.j2"
TEMPLATE_PROJECT_CREATED_ACTIVATED = "messages/project_created_activated.j2"
TEMPLATE_PROJECT_CREATED_MANUAL_ACTIVATION = "messages/project_created_manual_activation.j2"

# || S.S. 7.11: Define credential templates. ||
TEMPLATE_REPOSITORY_ENV = "credentials/repository_env_template.j2"

# || S.S. 7.12: Define base chain import paths. ||
BASE_CHAIN_IMPORT = "from chainedpy.chain import Chain"

# @@ STEP 8: Define CLI commands. @@
CMD_CREATE_PROJECT = "create-project"
CMD_SET_GLOBAL_PROJECT = "set-global-project"
CMD_ACTIVATE_PROJECT = "activate-project"
CMD_DEACTIVATE_PROJECT = "deactivate-project"
CMD_INIT = "init"
CMD_RELOAD = "reload"
CMD_LIST_PROJECTS = "list-projects"
CMD_UPDATE_PROJECT_PYI = "update-project-pyi"
CMD_UPDATE_BASE_PROJECT = "update-base-project"
CMD_CREATE_THEN_PLUGIN = "create-then-plugin"
CMD_CREATE_AS_PLUGIN = "create-as-plugin"
CMD_CREATE_PROCESSOR = "create-processor"
CMD_SHOW_PROJECT_CHAIN = "show-project-chain"
# Remote chain management commands (project-local).
CMD_UPDATE_REMOTE_CHAINS = "update-remote-chains"
CMD_CHECK_REMOTE_UPDATES = "check-remote-updates"
CMD_LIST_REMOTE_CHAINS = "list-remote-chains"
CMD_REMOTE_CHAIN_STATUS = "remote-chain-status"

# ─── ARGUMENT NAMES ─────────────────────────────────────────────────────────
ARG_PROJECT_PATH = "project_path"
ARG_BASE_PROJECT = "base_project"
ARG_SUMMARY = "summary"
ARG_GITHUB_TOKEN = "github_token"
ARG_GITLAB_TOKEN = "gitlab_token"
ARG_UPDATE_PYI = "update_pyi"
ARG_NAME_AFTER_PREFIX = "name_after_prefix"
ARG_NAME = "name"
ARG_FORCE = "force"
ARG_VERBOSE = "verbose"

# ─── PLUGIN PREFIXES ────────────────────────────────────────────────────────
PLUGIN_PREFIX_THEN = "then_"
PLUGIN_PREFIX_AS = "as_"
PLUGIN_PREFIX_PROCESSOR = "processor_"

# ─── PLUGIN TYPES ───────────────────────────────────────────────────────────
PLUGIN_TYPE_THEN = "then"
PLUGIN_TYPE_AS = "as"
PLUGIN_TYPE_PROCESSOR = "processor"

# ─── FILE PATHS ─────────────────────────────────────────────────────────────
ACTIVE_PROJECT_FILE = Path.home() / ".chainedpy_active_project"

# ─── PROJECT-LOCAL REMOTE CHAIN SYSTEM ────────────────────────────────────
# Remote chains are downloaded directly into project directories
REMOTE_CHAIN_META_FILE_NAME = ".chainedpy_remote_meta.json"
REMOTE_CHAIN_DEFAULT_TTL_HOURS = 24
# Metadata dictionary keys
METADATA_KEY_URL = "url"
METADATA_KEY_DOWNLOADED_AT = "downloaded_at"
METADATA_KEY_DEPENDENCIES = "dependencies"
METADATA_KEY_FILES = "files"
METADATA_KEY_TTL_HOURS = "ttl_hours"
METADATA_KEY_LOCAL_PATH = "local_path"
METADATA_KEY_SIZE_MB = "size_mb"

# Search paths must be provided explicitly by callers

# ─── URL SCHEMES ────────────────────────────────────────────────────────────
URL_SCHEME_SEPARATOR = "://"

# Supported URL schemes for remote filesystem operations
SUPPORTED_URL_SCHEMES = {'http', 'https', 'file', 's3', 'gcs', 'azure', 'abfs', 'ftp', 'sftp'}

# ─── MESSAGE TEMPLATES ─────────────────────────────────────────────────────
MSG_ERROR_PREFIX = "ERROR:"
MSG_PROJECT_ACTIVATED = "ChainedPy project activated: {}"
MSG_PROJECT_DEACTIVATED = "ChainedPy project deactivated: {}"
MSG_NO_ACTIVE_PROJECT = "No ChainedPy project is currently active"
MSG_NO_PROJECTS_FOUND = "No ChainedPy projects found."
MSG_AVAILABLE_PROJECTS = "Available ChainedPy projects:"
MSG_ACTIVE_PROJECT_MARKER = " (ACTIVE)"

# Success messages
MSG_SUCCESS_PROJECT_CREATED = "Project created at {}"
MSG_SUCCESS_PLUGIN_CREATED = "✅ {} {} created successfully!"
MSG_SUCCESS_GLOBAL_PROJECT_SET = "Global project set (imports patched)"
MSG_PLUGIN_STUB_UPDATED = "🔧 Type hints updated automatically!"
MSG_PLUGIN_STUB_HELP = """5. When done editing, regenerate type hints:
   chainedpy update-project-pyi --help"""
MSG_STUB_DISCOVERED_BASE_METHODS = "Discovered {} base {}_and {} base {}_methods from {}.chain using AST"
MSG_STUB_DISCOVERED_PROJECT_METHODS = "Discovered {} {}_and {} {}_methods from {} using AST"
MSG_STUB_DISCOVERED_PLUGINS = "Found {} {}_and {} {}_plugins in {}"
MSG_STUB_TOTAL_PLUGINS = "Total plugins after chain traversal: {} {}_, {} {}_ "
MSG_STUB_ADDED_BASE_METHODS = "Added {} base {}_and {} base {}_methods from {}"
MSG_STUB_ORGANIZED_METHODS = "Organized: {} base {}_, {} hierarchy {}_, {} current {}_ "
MSG_STUB_FAILED_DISCOVER_BASE = "Failed to discover base {} methods using AST: {}"
MSG_STUB_READ_CONFIG_DEFAULT = "Using default configuration: base_project={}, summary={}"
MSG_STUB_READ_CONFIG = "Read config: base_project={}, summary={}"
MSG_STUB_USING_BASE_IMPORT = "Using {} base import: {}"

# Error message patterns
MSG_ERROR_FAILED_TO = "Failed to {}: {}"
MSG_ERROR_PROJECT_NOT_FOUND = "Project path does not exist: {}"
MSG_ERROR_NOT_PYTHON_PACKAGE = "{} is not a Python package"
MSG_ERROR_NOT_CHAINEDPY_PROJECT = "Not a ChainedPy project: missing {}"
MSG_ERROR_INVALID_BASE_PROJECT = "Invalid base project: {}"

# ─── CONFIGURATION KEYS ────────────────────────────────────────────────────
CONFIG_KEY_PROJECT = "project"
CONFIG_KEY_BASE_PROJECT = "base_project"
CONFIG_KEY_SUMMARY = "summary"

# ─── CREDENTIAL KEYS ────────────────────────────────────────────────────────
CREDENTIAL_KEYS = [
    "GITHUB_TOKEN", "GITLAB_TOKEN", "BITBUCKET_TOKEN",
    "FTP_USERNAME", "FTP_PASSWORD", "SFTP_USERNAME", "SFTP_PASSWORD"
]

# GitHub credential keys
GITHUB_TOKEN_KEY = "github_token"
# GitLab credential keys
GITLAB_TOKEN_KEY = "gitlab_token"
GITLAB_PRIVATE_TOKEN_KEY = "gitlab_private_token"

# ─── PLATFORM CONSTANTS ────────────────────────────────────────────────────
PLATFORM_WINDOWS = "Windows"
PLATFORM_LINUX = "Linux"
PLATFORM_DARWIN = "Darwin"
GITLAB_PRIVATE_TOKEN_KEY = "gitlab_private_token"
# FTP credential keys
FTP_USERNAME_KEY = "ftp_username"
FTP_PASSWORD_KEY = "ftp_password"
# SFTP credential keys
SFTP_USERNAME_KEY = "sftp_username"
SFTP_PASSWORD_KEY = "sftp_password"
GITHUB_TOKEN_PLACEHOLDER = "your_github_token_here"
GITLAB_TOKEN_PLACEHOLDER = "your_gitlab_token_here"

# Credential validation error message
CREDENTIAL_VALIDATION_ERROR_MSG = "{credential_type} must be a non-empty string"

# ─── TEMPLATE CONTEXT KEYS ─────────────────────────────────────────────────
CONTEXT_KEY_SHORT = "short"
CONTEXT_KEY_CLS = "cls"
CONTEXT_KEY_SNAKE = "snake"
CONTEXT_KEY_PROJECT_NAME = "project_name"
CONTEXT_KEY_BASE_PROJECT = "base_project"
CONTEXT_KEY_SUMMARY = "summary"
CONTEXT_KEY_BASE_IMPORT = "base_import"

# ─── VALIDATION PATTERNS ───────────────────────────────────────────────────
PATTERN_PRIVATE_PREFIX = "_"
PATTERN_ALREADY_EXISTS = "already exists"

AST_TYPE_ANY = "Any"
AST_TYPE_CHAIN = "Chain"
AST_TYPE_WRAPPER = "Wrapper"
AST_TYPE_LINK = "Link"

# ─── LOGGING MESSAGES ──────────────────────────────────────────────────────
LOG_CONFIG_UPDATED = "Configuration file updated: {}"
LOG_CREATED_CONFIG_FILE = "Created config file: {}"
LOG_CREATED_CHAIN_FILE = "Created chain file: {}"
LOG_PROJECT_FILES_CREATED = "Successfully created all project files for {}"
LOG_FAILED_WRITE_ACTIVE_PROJECT = "Failed to write active project to {}"
LOG_FAILED_READ_ACTIVE_PROJECT = "Failed to read active project from {}"

# ─── SHELL PROMPT PATTERNS ─────────────────────────────────────────────────
SHELL_PROMPT_PREFIX = "(chainedpy:{})"
SHELL_PS1_VAR = "PS1"
SHELL_INTEGRATION_MARKER = "# ChainedPy shell integration"
POWERSHELL_PROFILE_PATH = "Documents/PowerShell/Microsoft.PowerShell_profile.ps1"
CHAINEDPY_BATCH_FILE = "chainedpy_init.bat"
BASHRC_FILE = ".bashrc"
BASH_PROFILE_FILE = ".bash_profile"
ZSHRC_FILE = ".zshrc"
FISH_CONFIG_PATH = ".config/fish/config.fish"

# ─── FILESYSTEM TYPES ──────────────────────────────────────────────────────
FS_TYPE_LOCAL = "local"
FS_TYPE_FILE = "file"

# GitHub domain constants
GITHUB_RAW_DOMAIN = "raw.githubusercontent.com"
GITHUB_DOMAIN = "github.com"
GITHUB_API_DOMAIN = "api.github.com"
# GitLab domain constants
GITLAB_DOMAIN = "gitlab.com"
GITLAB_KEYWORD = "gitlab"
# GitLab API constants
GITLAB_PRIVATE_TOKEN_HEADER = "PRIVATE-TOKEN"
# Filesystem type constants
FS_TYPE_GITHUB = "github"
FS_TYPE_GITLAB = "gitlab"
FS_TYPE_HTTP = "http"
FS_TYPE_HTTPS = "https"
FS_TYPE_FTP = "ftp"
FS_TYPE_SFTP = "sftp"
REPO_TYPE_GITHUB = "github"
REPO_TYPE_GITLAB = "gitlab"
REPO_TYPE_FTP = "ftp"
REPO_TYPE_SFTP = "sftp"
REPO_TYPE_UNKNOWN = "unknown"
# URL scheme constants
URL_SCHEME_FTP = "ftp://"
URL_SCHEME_SFTP = "sftp://"
URL_SCHEME_SSH = "ssh://"
URL_SCHEME_HTTPS = f"{FS_TYPE_HTTPS}://"

# ─── GITIGNORE ENTRIES ─────────────────────────────────────────────────────
# Environment file patterns
GITIGNORE_ENV_COMMENT = "# ChainedPy Environment Files"
GITIGNORE_ENV_FILE = ".env"
GITIGNORE_ENV_LOCAL = ".env.local"
GITIGNORE_ENV_WILDCARD = ".env.*.local"

# Python gitignore patterns
GITIGNORE_PYTHON_COMMENT = "# Python"
GITIGNORE_PYTHON_ENTRIES = [
    "__pycache__/",
    "*.py[cod]",
    "*$py.class",
    "*.so",
    ".Python",
    "build/",
    "develop-eggs/",
    "dist/",
    "downloads/",
    "eggs/",
    ".eggs/",
    "lib/",
    "lib64/",
    "parts/",
    "sdist/",
    "var/",
    "wheels/",
    "*.egg-info/",
    ".installed.cfg",
    "*.egg",
    "MANIFEST"
]

# Gitignore file patterns
GITIGNORE_FILE_NAME = ".gitignore"
GITIGNORE_PROJECT_HEADER = "# ChainedPy Project Gitignore\n# Auto-generated - edit as needed\n"
GITIGNORE_REMOTE_CHAIN_COMMENT = "ChainedPy Remote Chain: {}"


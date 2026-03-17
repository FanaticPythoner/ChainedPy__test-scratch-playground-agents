"""
Workspace fixtures for ChainedPy tests.

Provides centralized temporary workspace and directory management fixtures
following ChainedPy's service patterns.
"""
from __future__ import annotations

import pytest

from tests.services.filesystem_test_service import create_temp_workspace


@pytest.fixture
def temp_workspace():
    """Create a temporary workspace for testing.

    This is the centralized replacement for the temp_workspace fixture
    that was duplicated across all test files.

    :return Path: Temporary workspace directory that will be cleaned up automatically.
    :raises OSError: If workspace creation fails.
    """
    # @@ STEP 1: Create temporary workspace using service. @@
    with create_temp_workspace() as workspace:
        # @@ STEP 2: Yield workspace for test usage. @@
        yield workspace


@pytest.fixture
def temp_workspace_with_subdirs(temp_workspace):
    """Create a temporary workspace with common subdirectories.

    :param temp_workspace: Base temporary workspace fixture.
    :type temp_workspace: Path
    :return Dict[str, Path]: Dictionary mapping subdirectory names to paths.
    :raises OSError: If subdirectory creation fails.
    """
    # @@ STEP 1: Define subdirectory structure. @@
    subdirs = {
        'projects': temp_workspace / 'projects',
        'cache': temp_workspace / 'cache',
        'config': temp_workspace / 'config',
        'plugins': temp_workspace / 'plugins'
    }

    # @@ STEP 2: Create all subdirectories. @@
    for subdir in subdirs.values():
        subdir.mkdir(parents=True, exist_ok=True)

    # @@ STEP 3: Add workspace itself to the dictionary. @@
    subdirs['workspace'] = temp_workspace

    # @@ STEP 4: Yield subdirectories for test usage. @@
    yield subdirs


@pytest.fixture
def isolated_workspace(temp_workspace, monkeypatch):
    """Create an isolated workspace with environment variable isolation.

    :param temp_workspace: Base temporary workspace fixture.
    :type temp_workspace: Path
    :param monkeypatch: Pytest monkeypatch fixture.
    :type monkeypatch: Any
    :return Path: Isolated workspace with clean environment.
    :raises OSError: If cache directory creation fails.
    """
    # @@ STEP 1: Clear relevant environment variables. @@
    env_vars_to_clear = [
        'CHAINEDPY_ACTIVE_PROJECT',
        'CHAINEDPY_PROJECT_NAME',
        'CHAINEDPY_PROJECT_STACK',
        'GITHUB_TOKEN',
        'GITLAB_TOKEN',
        'GITLAB_PRIVATE_TOKEN'
    ]

    # || S.S. 1.1: Remove each environment variable. ||
    for var in env_vars_to_clear:
        monkeypatch.delenv(var, raising=False)

    # @@ STEP 2: Set isolated cache directory. @@
    cache_dir = temp_workspace / '.chainedpy_cache'
    cache_dir.mkdir(exist_ok=True)
    monkeypatch.setenv('CHAINEDPY_CACHE_DIR', str(cache_dir))

    # @@ STEP 3: Yield isolated workspace for test usage. @@
    yield temp_workspace


@pytest.fixture
def workspace_with_env_file(temp_workspace):
    """Create a workspace with a .env file for credential testing.

    :param temp_workspace: Base temporary workspace fixture.
    :type temp_workspace: Path
    :return Dict[str, Path]: Dictionary with workspace and env_file paths.
    :raises OSError: If env file creation fails.
    """
    # @@ STEP 1: Create .env file with test credentials. @@
    env_file = temp_workspace / '.env'
    env_content = """# Test environment file
GITHUB_TOKEN=test_github_token
GITLAB_TOKEN=test_gitlab_token
GITLAB_PRIVATE_TOKEN=test_gitlab_private_token
FTP_USERNAME=test_ftp_user
FTP_PASSWORD=test_ftp_pass
SFTP_USERNAME=test_sftp_user
SFTP_PASSWORD=test_sftp_pass
"""
    env_file.write_text(env_content)

    # @@ STEP 2: Yield workspace and env file paths. @@
    yield {
        'workspace': temp_workspace,
        'env_file': env_file
    }


@pytest.fixture
def workspace_with_chainedpy_env(temp_workspace):
    """Create a workspace with a .chainedpy.env file in home directory simulation.

    :param temp_workspace: Base temporary workspace fixture.
    :type temp_workspace: Path
    :return Dict[str, Path]: Dictionary with workspace and chainedpy_env_file paths.
    :raises OSError: If directory or file creation fails.
    """
    # @@ STEP 1: Simulate home directory. @@
    home_dir = temp_workspace / 'home'
    home_dir.mkdir(exist_ok=True)

    # @@ STEP 2: Create .chainedpy.env file. @@
    chainedpy_env_file = home_dir / '.chainedpy.env'
    env_content = """# ChainedPy specific environment file
GITHUB_TOKEN=chainedpy_github_token
GITLAB_TOKEN=chainedpy_gitlab_token
"""
    chainedpy_env_file.write_text(env_content)

    # @@ STEP 3: Yield workspace and environment file paths. @@
    yield {
        'workspace': temp_workspace,
        'home_dir': home_dir,
        'chainedpy_env_file': chainedpy_env_file
    }


@pytest.fixture
def readonly_workspace(temp_workspace):
    """Create a workspace with read-only permissions for permission testing.

    :param temp_workspace: Base temporary workspace fixture.
    :type temp_workspace: Path
    :return Path: Read-only workspace (permissions restored after test).
    :raises OSError: If permission changes fail.
    """
    # @@ STEP 1: Make workspace read-only. @@
    original_mode = temp_workspace.stat().st_mode
    temp_workspace.chmod(0o444)

    try:
        # @@ STEP 2: Yield read-only workspace for test usage. @@
        yield temp_workspace
    finally:
        # @@ STEP 3: Restore original permissions. @@
        temp_workspace.chmod(original_mode)


@pytest.fixture
def workspace_with_existing_projects(temp_workspace):
    """Create a workspace with some existing project directories (empty).

    :param temp_workspace: Base temporary workspace fixture.
    :type temp_workspace: Path
    :return Dict[str, Path]: Dictionary mapping project names to their paths.
    :raises OSError: If directory or file creation fails.
    """
    # @@ STEP 1: Define project names and initialize dictionary. @@
    project_names = ['existing_project_1', 'existing_project_2', 'legacy_project']
    projects = {}

    # @@ STEP 2: Create each project directory. @@
    for name in project_names:
        project_dir = temp_workspace / name
        project_dir.mkdir()
        # || S.S. 2.1: Create minimal structure to make it look like a project. ||
        (project_dir / '__init__.py').touch()
        projects[name] = project_dir

    # @@ STEP 3: Add workspace reference and yield projects. @@
    projects['workspace'] = temp_workspace
    yield projects


@pytest.fixture
def workspace_with_git_repo(temp_workspace):
    """Create a workspace that simulates a git repository structure.

    :param temp_workspace: Base temporary workspace fixture.
    :type temp_workspace: Path
    :return Dict[str, Path]: Dictionary with workspace and git-related paths.
    :raises OSError: If directory or file creation fails.
    """
    # @@ STEP 1: Create .git directory to simulate git repo. @@
    git_dir = temp_workspace / '.git'
    git_dir.mkdir()

    # @@ STEP 2: Create some git-like files. @@
    (git_dir / 'config').touch()
    (git_dir / 'HEAD').write_text('ref: refs/heads/main\n')

    # @@ STEP 3: Create .gitignore. @@
    gitignore = temp_workspace / '.gitignore'
    gitignore.write_text("""__pycache__/
*.pyc
*.pyo
*.pyd
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
""")

    # @@ STEP 4: Yield workspace and git-related paths. @@
    yield {
        'workspace': temp_workspace,
        'git_dir': git_dir,
        'gitignore': gitignore
    }


@pytest.fixture
def workspace_with_cache_structure(temp_workspace):
    """Create a workspace with ChainedPy cache directory structure.

    :param temp_workspace: Base temporary workspace fixture.
    :type temp_workspace: Path
    :return Dict[str, Path]: Dictionary with workspace and cache-related paths.
    :raises OSError: If directory or file creation fails.
    """
    # @@ STEP 1: Create cache directory structure. @@
    cache_dir = temp_workspace / '.chainedpy' / 'cache'
    cache_dir.mkdir(parents=True)

    # @@ STEP 2: Create subdirectories. @@
    repositories_dir = cache_dir / 'repositories'
    repositories_dir.mkdir()

    credentials_dir = cache_dir / 'credentials'
    credentials_dir.mkdir()

    # @@ STEP 3: Create cache index file. @@
    cache_index = cache_dir / 'cache_index.json'
    cache_index.write_text('{}')

    # @@ STEP 4: Yield workspace and cache-related paths. @@
    yield {
        'workspace': temp_workspace,
        'cache_dir': cache_dir,
        'repositories_dir': repositories_dir,
        'credentials_dir': credentials_dir,
        'cache_index': cache_index
    }

# ChainedPy

ChainedPy is a zero-dependency micro-framework for building **awaitable, mutation-free pipelines** (“chains”) that execute sequentially *or* in parallel and return an ordinary Python value.

| Feature               | Details                                                                                          |
| --------------------- | ------------------------------------------------------------------------------------------------ |
| **Seven core verbs**  | `then_map · then_flat_map · then_filter · then_foreach · then_reduce · then_parallel · then_if`  |
| **Wrapper verbs**     | `as_retry · as_timeout · as_log · as_cache · as_on_error`   -  decorate the **previous** link only |
| **Remote chains**     | Extend projects from GitHub/GitLab with automatic dependency resolution and caching             |
| **Fully awaitable**   | `result = await Chain(seed)…`                                                                    |
| **Parallel helpers**  | `then_parallel(…)`, `then_parallel_foreach(…)` (configurable concurrency)                        |
| **No hidden state**   | every link returns a *new* value; no mutation, ever                                              |
| **Zero dependencies** | requires only the Python `asyncio` std-lib                                                       |

---

## Installation

```bash
pip install chainedpy
```

For remote repository support (GitHub, GitLab, FTP, etc.):

```bash
pip install chainedpy[remote]
```

### Remote Repository Access

ChainedPy supports extending projects from remote repositories (GitHub, GitLab, FTP, etc.) with automatic dependency resolution and caching:

```bash
# Public repository (no credentials needed)
chainedpy create-project --name my_project \
  --base-project "https://raw.githubusercontent.com/user/repo/main/project_folder"

# Private repository with credentials
chainedpy create-project --name my_project \
  --base-project "https://raw.githubusercontent.com/user/private_repo/main/project_folder" \
  --github-token "your_github_token" \
  --create-env

# Create .env file for credential management
chainedpy create-project --name my_project --create-env
```

#### Remote Chain Features

- **Automatic Dependency Resolution**: Recursively downloads all dependencies
- **Per-Repository Credentials**: Different tokens for different repositories
- **Local Caching**: Downloaded chains are cached for faster access
- **Cache Management**: Built-in commands to manage cached remote chains

#### Cache Management

```bash
# List cached remote chains
chainedpy cache-list

# Show cache statistics
chainedpy cache-status

# Clean expired cache entries
chainedpy cache-clean

# Clear all cache
chainedpy cache-clear --confirm

# Refresh a specific cached chain
chainedpy cache-refresh --url "https://github.com/user/repo"
```

The `--create-env` flag creates a `.env` file with credential placeholders that you can fill in for private repository access.

---

## 60-second Quick Start

```python
import asyncio, aiohttp
from chainedpy import Chain

async def fetch(url: str):
    async with aiohttp.ClientSession() as s:
        async with s.get(url) as r:
            return await r.json()

async def main() -> list[str]:
    return await (
        Chain(["https://httpbin.org/uuid", "https://httpbin.org/anything"])
        .then_parallel_foreach(lambda url: Chain(url).then_map(fetch))
        .then_return(lambda lst: [d["url"] for d in lst])
    )
print(asyncio.run(main()))
```

---

## Core Concepts

| Term             | Meaning                                                                          |
| ---------------- | -------------------------------------------------------------------------------- |
| **stream value** | The single object that flows from one link to the next.                          |
| **link**         | An `async` function inserted by a `then_…` or `as_…` call.                       |
| **chain**        | An immutable sequence of links; itself `await`-able.                             |
| **wrapper**      | An `as_…` verb that **decorates only the previous link** (retry, timeout, log…). |

---

## API Surface (synopsis)

`Chain(...)`

* `Chain(value)`  -  seed with any object
* `Chain(a=1, b=2)`  -  seed with kwargs stored as dict

**Core `then_` verbs**

* `then_map(fn)`
* `then_flat_map(fn)`
* `then_filter(pred)`
* `then_foreach(fn)`
* `then_parallel_foreach(fn, limit=None)`
* `then_reduce(init, reducer)`
* `then_if(condition=, then=, otherwise=)` *(revolutionary auto-chaining syntax)*
* `then_switch(key_selector, cases, default=None)`
* `then_when(key_selector).case(key, handler).default(handler)`
* `then_parallel(*chains)`
* `then_process(Proc.X, param=None)`

**Wrapper `as_` verbs**

* `as_retry(attempts=3, delay=1.0)`
* `as_timeout(seconds)`
* `as_log(label="", level=logging.DEBUG)`
* `as_cache(ttl=60.0)`
* `as_on_error(handler)`

Termination

* `await Chain(... )`  -  returns final stream value
* `await Chain(... ).then_return(fn)`  -  returns `fn(value)`

---

## Documentation

User and API reference lives in `docs/` (MkDocs). Build locally:

```
pip install mkdocs-material
mkdocs serve
```

---

## Contributing

### Development Setup

```bash
# Clone the repository
git clone https://github.com/your-org/chainedpy.git
cd chainedpy

# Install dependencies
python -m pip install -r requirements.txt

# Run tests
python -m pytest tests/ -v

# Build documentation
mkdocs serve
```

### Contributing Guidelines
 
1. **Fork and open a PR.**
2. `python -m pytest tests/ -v` and `mkdocs build` must pass.
3. Follow the [chainedpy coding standards](chainedpy_standards.md).
4. Include comprehensive unit tests for all new functionality.
5. Update documentation for any API changes.
6. Keep PRs small and focused on a single feature or bug fix.

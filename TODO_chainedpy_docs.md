# ChainedPy Documentation TODO

This file tracks ALL remaining documentation tasks for the ChainedPy codebase. Every function, method, and class must have comprehensive docstrings with examples following the established standards.

## COMPLETED FILES ✅

These files have ALL functions/methods/classes fully documented:

1. **chainedpy/exceptions.py** - ALL 21 exception classes ✅
2. **chainedpy/services/filesystem_service.py** - ALL 11 functions ✅
3. **chainedpy/services/template_service.py** - ALL 12 functions ✅
4. **chainedpy/services/logging_service.py** - ALL 3 functions ✅
5. **chainedpy/plugins/wrappers.py** - ALL 5 wrapper functions ✅
6. **chainedpy/models.py** - 1 class (already complete) ✅
7. **chainedpy/services/ast_service.py** - ALL 14 functions ✅
8. **chainedpy/services/project_file_service.py** - ALL 8 functions ✅
9. **chainedpy/services/credential_service.py** - ALL 8 functions ✅
10. **chainedpy/services/chain_traversal_service.py** - ALL 6 functions ✅
11. **chainedpy/services/gitignore_service.py** - ALL 5 functions ✅
12. **chainedpy/services/project_validation.py** - ALL 4 functions ✅

## PARTIALLY COMPLETED FILES 🔄

### chainedpy/chain.py (6/64 functions completed)
**MISSING DOCUMENTATION:**
- `Chain.__init__()` - needs comprehensive docstring with examples
- `Chain._add_link()` - needs comprehensive docstring with examples
- `Chain._replace_last()` - needs comprehensive docstring with examples
- `Chain._run()` - needs comprehensive docstring with examples
- `Chain.__await__()` - needs comprehensive docstring with examples
- `Chain.__repr__()` - needs comprehensive docstring with examples
- `_ChainMethods.then_map()` - needs comprehensive docstring with examples
- `_ChainMethods.then_if()` - needs comprehensive docstring with examples
- `_ChainMethods.then_filter()` - needs comprehensive docstring with examples
- `_ChainMethods.then_flat_map()` - needs comprehensive docstring with examples
- `_ChainMethods.then_switch()` - needs comprehensive docstring with examples
- `_ChainMethods.then_foreach()` - needs comprehensive docstring with examples
- `_ChainMethods.then_parallel_foreach()` - needs comprehensive docstring with examples
- `_ChainMethods.then_reduce()` - needs comprehensive docstring with examples
- `_ChainMethods.then_parallel()` - needs comprehensive docstring with examples
- `_ChainMethods.as_retry()` - needs comprehensive docstring with examples
- `_ChainMethods.as_timeout()` - needs comprehensive docstring with examples
- `_ChainMethods.as_log()` - needs comprehensive docstring with examples
- `_ChainMethods.as_cache()` - needs comprehensive docstring with examples
- `_ChainMethods.as_on_error()` - needs comprehensive docstring with examples
- All remaining `then_process()` overloads (52 remaining)
- Shadow `Chain.__init__()` - needs comprehensive docstring with examples
- Shadow `Chain.__await__()` - needs comprehensive docstring with examples

### chainedpy/cli.py (1/3 functions completed)
**MISSING DOCUMENTATION:**
- `_path()` - needs comprehensive docstring with examples
- `_build_parser()` - needs comprehensive docstring with examples

### chainedpy/link.py (3/30 functions completed)
**MISSING DOCUMENTATION:**
- `Link` class - needs comprehensive docstring with examples
- `Link.__call__()` - needs comprehensive docstring with examples
- `Wrapper` class - needs comprehensive docstring with examples
- `Wrapper.wrap()` - needs comprehensive docstring with examples
- `Processor` class - needs comprehensive docstring with examples
- `Processor.apply()` - needs comprehensive docstring with examples
- All remaining methods and classes (24 remaining)

### chainedpy/project.py (3/8 functions completed)
**MISSING DOCUMENTATION:**
- 5 remaining functions need comprehensive docstrings with examples

### chainedpy/register.py (4/6 functions completed)
**MISSING DOCUMENTATION:**
- 2 remaining functions need comprehensive docstrings with examples

### chainedpy/plugins/processors.py (1/8 functions completed)
**MISSING DOCUMENTATION:**
- 7 remaining functions need comprehensive docstrings with examples

### chainedpy/typing.py (1/3 functions completed)
**MISSING DOCUMENTATION:**
- 2 remaining functions need comprehensive docstrings with examples

### chainedpy/plugins/core.py (12/15 functions completed)
**MISSING DOCUMENTATION:**
- 3 remaining functions need comprehensive docstrings with examples

### chainedpy/services/stub_generation_service.py (12/15 functions completed)
**MISSING DOCUMENTATION:**
- 3 remaining functions need comprehensive docstrings with examples

### chainedpy/services/shell_integration.py (8/10 functions completed)
**MISSING DOCUMENTATION:**
- 2 remaining functions need comprehensive docstrings with examples

### chainedpy/services/remote_chain_service.py (3/8 functions completed)
**MISSING DOCUMENTATION:**
- 5 remaining functions need comprehensive docstrings with examples

### chainedpy/services/command_handlers.py (3/15 functions completed)
**MISSING DOCUMENTATION:**
- 12 remaining functions need comprehensive docstrings with examples

### chainedpy/services/project_lifecycle.py (3/12 functions completed)
**MISSING DOCUMENTATION:**
- 9 remaining functions need comprehensive docstrings with examples

### chainedpy/services/project_remote_chain_service.py (2/10 functions completed)
**MISSING DOCUMENTATION:**
- 8 remaining functions need comprehensive docstrings with examples

## DOCUMENTATION STANDARDS

Each function/method/class must have:

1. **Comprehensive docstring** with proper reST format
2. **Type annotations** with proper cross-references like `[str][str]`, `[Path][pathlib.Path]`
3. **Detailed parameter descriptions** with types
4. **Return value description** with type
5. **Exception documentation** where applicable
6. **Complete example** showing realistic usage
7. **Example should be runnable** and demonstrate the function's purpose
8. **Examples should include assertions** to verify behavior
9. **Examples should include cleanup** where necessary (file operations, etc.)

## PRIORITY ORDER

1. **HIGH PRIORITY**: Core chain functionality (`chain.py`, `link.py`)
2. **MEDIUM PRIORITY**: CLI and project management (`cli.py`, `project.py`, `project_lifecycle.py`)
3. **LOW PRIORITY**: Remaining service files and utilities

## ESTIMATED WORK REMAINING

- **Total functions/methods/classes**: ~400
- **Completed**: ~150
- **Remaining**: ~250
- **Estimated time**: 20-30 hours of focused work

## CRITICAL MISSING FILES TO CHECK

These files may contain additional functions that need documentation:

1. **chainedpy/services/env_service.py** - Environment variable handling
2. **chainedpy/services/plugin_discovery_service.py** - Plugin discovery logic
3. **chainedpy/services/dependency_service.py** - Dependency management
4. **chainedpy/services/cache_service.py** - Caching functionality
5. **chainedpy/services/validation_service.py** - Validation utilities
6. **chainedpy/services/config_service.py** - Configuration management
7. **chainedpy/services/git_service.py** - Git operations
8. **chainedpy/services/package_service.py** - Package management
9. **chainedpy/services/test_service.py** - Testing utilities
10. **chainedpy/services/build_service.py** - Build operations

## IMMEDIATE NEXT STEPS

1. **Complete chain.py** - This is the core of the framework (64 functions total, 58 remaining)
2. **Complete link.py** - Core abstractions (30 functions total, 27 remaining)
3. **Complete cli.py** - User interface (3 functions total, 2 remaining)
4. **Complete project.py** - Project management (8 functions total, 5 remaining)
5. **Complete remaining service files** - Support functionality

## QUALITY CHECKLIST FOR EACH FUNCTION

- [ ] Comprehensive docstring with proper reST format
- [ ] All parameters documented with types using cross-references
- [ ] Return value documented with type using cross-references
- [ ] Exceptions documented where applicable
- [ ] Complete realistic example with imports
- [ ] Example includes setup if needed
- [ ] Example includes assertions to verify behavior
- [ ] Example includes cleanup if needed (files, directories, etc.)
- [ ] Type annotations use proper format: `[str][str]`, `[Path][pathlib.Path]`
- [ ] Example is self-contained and runnable
- [ ] Example demonstrates the function's primary purpose
- [ ] Example shows edge cases where relevant

## DETAILED BREAKDOWN BY FILE

### chainedpy/services/env_service.py
**STATUS**: NOT STARTED
**FUNCTIONS NEEDING DOCUMENTATION**: ALL functions (estimated 5-8 functions)

### chainedpy/services/plugin_discovery_service.py
**STATUS**: NOT STARTED
**FUNCTIONS NEEDING DOCUMENTATION**: ALL functions (estimated 6-10 functions)

### chainedpy/services/dependency_service.py
**STATUS**: NOT STARTED
**FUNCTIONS NEEDING DOCUMENTATION**: ALL functions (estimated 4-6 functions)

### chainedpy/services/cache_service.py
**STATUS**: NOT STARTED
**FUNCTIONS NEEDING DOCUMENTATION**: ALL functions (estimated 3-5 functions)

### chainedpy/plugins/__init__.py
**STATUS**: NOT CHECKED
**FUNCTIONS NEEDING DOCUMENTATION**: Any functions present

### chainedpy/__init__.py
**STATUS**: NOT CHECKED
**FUNCTIONS NEEDING DOCUMENTATION**: Any functions present

### chainedpy/services/__init__.py
**STATUS**: NOT CHECKED
**FUNCTIONS NEEDING DOCUMENTATION**: Any functions present

### chainedpy/constants.py
**STATUS**: NOT CHECKED
**FUNCTIONS NEEDING DOCUMENTATION**: Any functions present

## SPECIFIC FUNCTION LISTS

### chainedpy/chain.py - DETAILED MISSING FUNCTIONS
1. `Chain.__init__(self, value: _T | None = None, **kwargs)`
2. `Chain._add_link(self, link: Link[_T, _O]) -> "Chain[_O]"`
3. `Chain._replace_last(self, link: Link[_I, _T]) -> "Chain[_T]"`
4. `Chain._run(self) -> _T`
5. `Chain.__await__(self)`
6. `Chain.__repr__(self) -> str`
7. `_ChainMethods.then_map(self, transform: Callable[[_T], _O | Awaitable[_O] | "Chain[_O]"]) -> "Chain[_O]"`
8. `_ChainMethods.then_if(self, condition: Callable[[_T], bool | Awaitable[bool]], *, then: Callable[[_T], _O | Awaitable[_O] | "Chain[_O]"], otherwise: Callable[[_T], _O | Awaitable[_O] | "Chain[_O]"] | None = None) -> "Chain[_O]"`
9. `_ChainMethods.then_filter(self, predicate: Callable[[_T], bool | Awaitable[bool]]) -> "Chain[_T | None]"`
10. `_ChainMethods.then_flat_map(self, transform: Callable[[_T], Iterable[_O] | Awaitable[Iterable[_O]] | "Chain[Iterable[_O]]"]) -> "Chain[list[_O]]"`
11. `_ChainMethods.then_switch(self, cases: Dict[_K, Callable[[_T], _O | Awaitable[_O] | "Chain[_O]"]], *, key: Callable[[_T], _K] = lambda x: x, default: Callable[[_T], _O | Awaitable[_O] | "Chain[_O]"] | None = None) -> "Chain[_O]"`
12. `_ChainMethods.then_foreach(self, transform: Callable[[_E], _V | Awaitable[_V] | "Chain[_V]"]) -> "Chain[list[_V]]"`
13. `_ChainMethods.then_parallel_foreach(self, *, transform: Callable[[_E], _V | Awaitable[_V] | "Chain[_V]"], limit: int | None = None) -> "Chain[list[_V]]"`
14. `_ChainMethods.then_reduce(self, *, initial: _O, accumulator: Callable[[_O, _E], _O | Awaitable[_O]]) -> "Chain[_O]"`
15. `_ChainMethods.then_parallel(self, *operations: Callable[[_T], _O | Awaitable[_O] | "Chain[_O]"]) -> "Chain[list[_O]]"`
16. `_ChainMethods.as_retry(self, *, attempts: int = 3, delay: float = 1.0, backoff: float = 2.0, exceptions: tuple[type[Exception], ...] = (Exception,)) -> "Chain[_T]"`
17. `_ChainMethods.as_timeout(self, seconds: float) -> "Chain[_T]"`
18. `_ChainMethods.as_log(self, *, level: str = "INFO", message: str | None = None) -> "Chain[_T]"`
19. `_ChainMethods.as_cache(self, *, ttl: float = 60.0) -> "Chain[_T]"`
20. `_ChainMethods.as_on_error(self, handler: Callable[[Exception], _T | Awaitable[_T] | "Chain[_T]"]) -> "Chain[_T]"`
21. All `then_process()` overloads (8 different processor types)
22. Shadow class methods

### chainedpy/link.py - DETAILED MISSING FUNCTIONS
1. `Link` class docstring and examples
2. `Link.__call__(self, arg: I_co) -> O_co`
3. `Wrapper` class docstring and examples
4. `Wrapper.wrap(self, inner: Link[I_co, O_co]) -> Link[I_co, O_co]`
5. `Processor` class docstring and examples
6. `Processor.apply(self, value: I_co, *, param: str | None = None) -> O_co`
7. `maybe_await(value: Awaitable[O_co] | O_co) -> O_co`
8. All nested classes and methods within examples

## NOTES

- All docstrings must follow the established pattern with comprehensive examples
- Type annotations must use proper cross-reference format like `[str][str]`, `[Path][pathlib.Path]`
- Examples must be realistic and demonstrate actual usage
- Each example should be self-contained and runnable
- Focus on completing entire files rather than partial work
- Priority should be given to core functionality first (chain.py, link.py)
- Each function needs full parameter documentation with types
- Each function needs return value documentation with types
- Each function needs exception documentation where applicable
- Examples should include imports, setup, assertions, and cleanup

# ChainedPy Documentation Standards - MANDATORY COMPLIANCE

**ENFORCEMENT LEVEL: MANDATORY**
**SCOPE: ALL CONTRIBUTORS**
**VIOLATIONS: PULL REQUEST REJECTION**

This document defines **MANDATORY** documentation standards for the ChainedPy project. **ALL** contributors, maintainers, and developers **MUST** follow these standards without exception. Pull requests that violate these standards **WILL BE REJECTED**.

## Table of Contents

1. [MkDocs Configuration](#mkdocs-configuration)
2. [Docstring Format](#docstring-format)
3. [Cross-References and Links](#cross-references-and-links)
4. [Type Annotations](#type-annotations)
5. [Admonitions and Special Sections](#admonitions-and-special-sections)
6. [Code Examples](#code-examples)
7. [Module Documentation](#module-documentation)
8. [Class Documentation](#class-documentation)
9. [Function/Method Documentation](#functionmethod-documentation)
10. [Variable Documentation](#variable-documentation)

## MkDocs Configuration

### Required Plugins in `mkdocs.yml`

```yaml
plugins:
  - search
  - autorefs  # For internal cross-references
  - mkdocstrings:
      default_handler: python
      handlers:
        python:
          paths: [.]
          options:
            docstring_style: sphinx
            show_source: true
            show_bases: true
            show_root_heading: true
            show_root_toc_entry: true
            show_signature_annotations: true
            show_symbol_type_heading: true
            show_symbol_type_toc: true
            inherited_members: true
            members_order: source
            group_by_category: true
            separate_signature: true
            line_length: 80
            merge_init_into_class: true
            filters: ["!^__"]
            show_if_no_docstring: true
            show_module_attributes: true
            show_attributes: true
            cross_references: true
            external_links:
              typing.TypeVar: https://docs.python.org/3/library/typing.html#typing.TypeVar
              typing.Union: https://docs.python.org/3/library/typing.html#typing.Union
              typing.Optional: https://docs.python.org/3/library/typing.html#typing.Optional
              typing.List: https://docs.python.org/3/library/typing.html#typing.List
              typing.Dict: https://docs.python.org/3/library/typing.html#typing.Dict
              typing.Callable: https://docs.python.org/3/library/typing.html#typing.Callable
              typing.Any: https://docs.python.org/3/library/typing.html#typing.Any
              typing.Generic: https://docs.python.org/3/library/typing.html#typing.Generic
              pathlib.Path: https://docs.python.org/3/library/pathlib.html#pathlib.Path
```

### Required Dependencies in `requirements-dev-new.txt`

```
mkdocs==1.6.1
mkdocs-material==9.6.15
mkdocstrings-python
mkdocs-autorefs
pymdown-extensions
```

### Advanced Features Configuration

```yaml
plugins:
  - search
  - autorefs
  - mkdocstrings:
      default_handler: python
      handlers:
        python:
          paths: [.]
          # Load external inventories for automatic cross-references
          import:
            - https://docs.python.org/3/objects.inv  # Python standard library
            - https://docs.aiohttp.org/en/stable/objects.inv  # aiohttp
            - https://fsspec.readthedocs.io/en/latest/objects.inv  # fsspec
          options:
            # Core display options
            docstring_style: sphinx
            show_source: true
            show_bases: true
            show_root_heading: true
            show_root_toc_entry: true
            show_signature_annotations: true
            show_symbol_type_heading: true
            show_symbol_type_toc: true

            # Advanced signature options
            separate_signature: true
            signature_crossrefs: true
            line_length: 80
            annotations_path: brief
            modernize_annotations: true  # Requires Insiders
            show_overloads: true

            # Member organization
            inherited_members: true
            members_order: source
            group_by_category: true
            merge_init_into_class: true
            filters: ["!^__"]
            show_if_no_docstring: true
            show_module_attributes: true
            show_attributes: true

            # Cross-reference configuration
            cross_references: true

            # Advanced features (some require Insiders)
            backlinks: tree  # Show where API objects are referenced
            show_inheritance_diagram: true  # Mermaid inheritance diagrams
```

## Docstring Format

### RULE 1: Sphinx/reST Format - NO EXCEPTIONS

**MANDATORY**: ALL docstrings MUST use Sphinx/reST format. No other formats are permitted.

**MANDATORY**: Every class, method, and function MUST include at least one Example section. **NO EXCEPTIONS**.

**MANDATORY**: All docstrings MUST include ALL required fields as specified below.

```python
def example_function(param1: str, param2: int = 10) -> bool:
    """Short one-line summary.
    
    Longer description that can span multiple lines and provides
    detailed information about what the function does.
    
    :param param1: Description of param1
    :type param1: str
    :param param2: Description of param2, defaults to 10
    :type param2: int, optional
    :raises ValueError: When something goes wrong
    :return bool: Description of return value
    
    Note:
        Important notes about the function.
    
    Warning:
        Important warnings about usage.

    Example:
        ```python
        # Basic usage
        result = example_function("hello", 20)
        assert result is True

        # With default parameter
        result = example_function("world")
        assert result is True
        ```

    See Also:
        - [related_function][module.related_function]: Related functionality
        - [SomeClass][module.SomeClass]: Related class
    """
```

## Cross-References and Links

### Internal Cross-References (ChainedPy Classes/Functions)

Use the format: `[DisplayText][full.module.path.ClassName]`

```python
# Class references
[Chain][chainedpy.chain.Chain]
[Link][chainedpy.link.Link]

# Method references
[_run][chainedpy.chain.Chain._run]
[then_map][chainedpy.chain.Chain.then_map]

# Function references
[register_chain][chainedpy.register.register_chain]

# Module references
[constants][chainedpy.constants]

# Relative references (within same module)
[.method_name]  # References method in current class
[.ClassName]    # References class in current module
```

### External Links (Automatic via Inventories)

**AUTOMATIC CROSS-REFERENCES**: mkdocstrings-python automatically creates clickable links for:

```python
# Python standard library (via objects.inv)
[str]           # Links to Python str docs
[pathlib.Path]  # Links to pathlib.Path docs
[typing.Union]  # Links to typing.Union docs
[asyncio.Task]  # Links to asyncio.Task docs

# Third-party libraries (via loaded inventories)
[aiohttp.ClientSession]  # Links to aiohttp docs
[fsspec.AbstractFileSystem]  # Links to fsspec docs

# No manual configuration needed - just use the type name!
```

### Manual External Links (Fallback)

Only needed if automatic inventory loading fails:

```python
# Built-in types (fallback if inventory fails)
[TypeVar][typing.TypeVar]
[Union][typing.Union]
[Optional][typing.Optional]
[List][typing.List]
[Dict][typing.Dict]
[Callable][typing.Callable]
[Path][pathlib.Path]
```

## Type Annotations

### In Docstrings

Always include both `:type:` and `:return:` fields (for `:return:`, ensure you add the return type before the last `:`):

```python
def process_data(items: List[str]) -> Dict[str, int]:
    """Process a list of items.
    
    :param items: List of string items to process
    :type items: [List][typing.List][[str][str]]
    :return [Dict][typing.Dict][[str][str], [int][int]]: Mapping of items to their counts
    """
```

### TypeVar Documentation

```python
_T = TypeVar("_T", covariant=True)
"""[TypeVar][typing.TypeVar]: Primary type variable for values carried by the [Chain][chainedpy.chain.Chain].
    
    This is a covariant type variable used throughout the [Chain][chainedpy.chain.Chain] class to represent
    the type of value being carried through the chain operations.
    
    :type: [TypeVar][typing.TypeVar] (covariant=True)
"""
```

## Admonitions and Special Sections

### mkdocstrings-python Standard Admonitions

**OFFICIAL STANDARD**: mkdocstrings-python automatically converts Google-style sections to admonitions:

```python
"""Function description.

Note:
    This is a note section that will be rendered as a note admonition.

Warning:
    This is a warning section that will be rendered as a warning admonition.

Tip:
    This is a tip section that will be rendered as a tip admonition.

Example:
    This is an example section that will be rendered as an example admonition.

See Also:
    This is a see also section that will be rendered as a see-also admonition.
"""
```

### Supported Admonition Types

According to mkdocstrings-python documentation, these sections are automatically converted:

- `Note:` → Note admonition
- `Warning:` → Warning admonition
- `Tip:` → Tip admonition
- `Example:` → Example admonition
- `See Also:` → See Also admonition
- `Important:` → Important admonition
- `Caution:` → Caution admonition

### ❌ NEVER Use These (Sphinx-only)

```python
# DON'T USE THESE - THEY WON'T RENDER IN MKDOCS
::note::
::warning::
::seealso::
:class:`ClassName`
:meth:`method_name`
:func:`function_name`
```

## Code Examples

### RULE 2: ChainedPy Chain Formatting - STRICT COMPLIANCE

**MANDATORY**: ALL chain examples MUST follow the exact formatting pattern below. **NO DEVIATIONS PERMITTED**.

**REQUIRED PATTERN**:
```python
# ✅ MANDATORY FORMAT: Each method on separate line, including Chain()
result = await (
    Chain("hello")
    .then_map(str.upper)
    .then_map(lambda s: s + "!")
)
```

**FORBIDDEN PATTERNS**:
```python
# ❌ FORBIDDEN: Inline Chain / methods
result = await Chain("hello").then_map(str.upper)

# ❌ FORBIDDEN: Missing await
result = Chain("hello").then_map(str.upper)
```

### RULE 3: Example Requirements

**MANDATORY**: Always use triple backticks with language specification:

```python
"""Function description.

Example:
    ```python
    from chainedpy import Chain
    
    result = await (
        Chain("hello")
        .then_map(str.upper)
        .then_map(lambda s: s + "!")
    )
    
    assert result == "HELLO!"
    ```
"""
```

**MANDATORY**: ALL examples MUST include:
1. **Basic usage** - showing the most common use case
2. **Parameter variations** - showing different parameter combinations
3. **Error handling** - showing exception cases where applicable
4. **Assertions** - proving the example works correctly

**MANDATORY**: ALL chain examples MUST use the exact formatting pattern specified in RULE 2.

## Module Documentation

### Module-Level Docstring

```python
"""ChainedPy Core Chain Implementation.

This module contains the core [Chain][chainedpy.chain.Chain] class that provides the fluent chaining API. 
The Chain class is the heart of ChainedPy, enabling asynchronous pipeline execution with type safety 
and extensibility.

The module provides both runtime implementation and static typing shims to ensure optimal type 
inference while maintaining clean separation between runtime behavior and type checking concerns.

Note:
    This module uses TYPE_CHECKING blocks to provide enhanced type hints without affecting 
    runtime performance. The Chain class is designed to be both performant at runtime and 
    fully type-safe during development.

See Also:
    - [Link][chainedpy.link.Link]: Individual pipeline steps module
    - [register][chainedpy.register]: Method registration decorators module
    - [exceptions][chainedpy.exceptions]: Chain-specific exceptions module
"""
```

## Class Documentation

### Class Docstring Template

**MANDATORY: Every class MUST include comprehensive usage examples.**

```python
class ExampleClass:
    """Short description of the class.

    Longer description explaining the purpose, behavior, and usage
    of the class. Include important implementation details.

    :param init_param: Description of constructor parameter
    :type init_param: str
    :ivar instance_var: Description of instance variable
    :vartype instance_var: int

    Note:
        Important notes about the class behavior.

    Example:
        ```python
        # Basic instantiation
        obj = ExampleClass("value")

        # Using the main functionality
        result = obj.method()
        assert result is not None

        # Advanced usage pattern
        with ExampleClass("context") as ctx:
            data = ctx.process()
        ```

    See Also:
        - [RelatedClass][module.RelatedClass]: Related functionality
    """
```

## Function/Method Documentation

### Complete Template

**MANDATORY: Every function and method MUST include multiple usage examples. These should ALWAYS BE BEFORE ANY DOUBLE-COLON DIRECTIVES**

```python
def example_method(self, param1: str, param2: Optional[int] = None) -> bool:
    """Short description of what the method does.

    Detailed description explaining the method's behavior, side effects,
    and any important implementation details.

    Note:
        Important behavioral notes.

    Warning:
        Important warnings about usage.

    Example:
        ```python
        # Basic usage
        obj = ExampleClass("test")
        success = obj.example_method("value", 42)
        assert success is True

        # Using default parameter
        success = obj.example_method("value")
        assert success is True

        # Error handling
        try:
            obj.example_method("", 42)
        except ValueError as e:
            print(f"Expected error: {e}")
        ```

    See Also:
        - [related_method][module.Class.related_method]: Related functionality

    :param param1: Description of the first parameter
    :type param1: [str][str]
    :param param2: Description of optional parameter, defaults to None
    :type param2: [Optional][typing.Optional][[int][int]], optional
    :raises ValueError: When param1 is empty
    :raises TypeError: When param2 is not an integer
    :return [bool][bool]: True if operation succeeded, False otherwise
    """
```

## Variable Documentation

### Module-Level Variables

```python
DEFAULT_TIMEOUT: int = 30
"""[int][int]: Default timeout value in seconds for chain operations.

This constant defines the maximum time a chain operation will wait
before timing out. Used throughout the chain execution pipeline.

:type: [int][int]
"""
```

### Class-Level Variables

```python
class ExampleClass:
    """Class description."""
    
    CLASS_CONSTANT: str = "value"
    """[str][str]: Class-level constant description.
    
    Detailed explanation of what this constant represents
    and how it's used within the class.
    
    :type: [str][str]
    """
```

## COMPLIANCE CHECKLIST - MANDATORY VERIFICATION

### ✅ MANDATORY REQUIREMENTS - ALL MUST BE PRESENT

**BEFORE SUBMITTING ANY PULL REQUEST, VERIFY ALL ITEMS BELOW:**

- [ ] **Sphinx/reST docstring format** - NO other formats permitted
- [ ] **ALL required fields present**: `:param:`, `:type:`, `:return:`
- [ ] **Cross-references use correct syntax**: `[DisplayText][full.module.path]`
- [ ] **Admonitions use Google-style**: `Note:`, `Warning:`, `Example:`, `See Also:`
- [ ] **Example section present in EVERY docstring** - NO EXCEPTIONS
- [ ] **Multiple usage examples** - basic, advanced, error handling
- [ ] **Chain formatting follows RULE 2** - exact pattern required
- [ ] **All examples include assertions** - proving they work
- [ ] **All public APIs documented** - classes, methods, functions
- [ ] **Type annotations in docstrings** - not just in code
- [ ] **Error cases documented** - where applicable
- [ ] **Real-world context in examples** - not trivial demos

### ❌ VIOLATIONS - AUTOMATIC PULL REQUEST REJECTION

**ANY OF THE FOLLOWING WILL RESULT IN IMMEDIATE PR REJECTION:**

- [ ] **Missing Example sections** - ZERO TOLERANCE
- [ ] **Inline chain method calls** - `Chain().then_map().run()` FORBIDDEN
- [ ] **Incorrect chain formatting** - Must follow RULE 2 exactly
- [ ] **Sphinx-only directives** - `::note::`, `:class:` FORBIDDEN
- [ ] **Missing type annotations in docstrings** - Code types not enough
- [ ] **Hardcoded strings without cross-references** - Must link properly
- [ ] **Trivial examples without context** - Must show real usage
- [ ] **Missing docstrings on public APIs** - ALL must be documented
- [ ] **Using `Any` type without justification** - Explain why needed
- [ ] **Examples that don't follow ChainedPy standards** - Must be compliant

## ENFORCEMENT

**REVIEWERS**: Use this checklist to verify compliance before approving any PR.
**CONTRIBUTORS**: Self-check using this list before submitting.
**MAINTAINERS**: Reject any PR that violates these standards.

## CONFIGURATION DECISION MATRIX - WHEN TO MODIFY mkdocs.yml

**⚠️ WARNING: mkdocs.yml changes affect ALL contributors and build times. Only modify with team approval.**

### DECISION CRITERIA FOR EACH FEATURE

#### 1. `show_source: true` (DEFAULT: ENABLED)
**WHEN TO USE**: Always enabled for ChainedPy
**WHY**: Users need to see implementation details for chain methods
**IMPACT**: Increases page size, slower loading
**DECISION**: ✅ **MANDATORY** - Keep enabled

#### 2. `separate_signature: true` (DEFAULT: DISABLED)
**WHEN TO USE**: When function signatures are long (>60 chars)
**WHY**: Improves readability of complex type annotations
**IMPACT**: Changes visual layout for ALL functions
**DECISION**: ✅ **MANDATORY** - Enable for ChainedPy's complex signatures

#### 3. `signature_crossrefs: true` (DEFAULT: DISABLED)
**WHEN TO USE**: When you have `separate_signature: true`
**WHY**: Makes type annotations clickable in signatures
**IMPACT**: Requires separate_signature, affects ALL signatures
**DECISION**: ✅ **MANDATORY** - Enable with separate_signature

#### 4. `modernize_annotations: true`
**WHEN TO USE**: Only if absolutely necessary for type clarity
**WHY**: Shows modern `A | B` instead of `Union[A, B]`
**IMPACT**: Changes ALL type displays across documentation
**DECISION**: ❌ **DISABLED** - Not necessary, adds complexity

#### 5. `show_inheritance_diagram: true`
**WHEN TO USE**: Only if class hierarchies are extremely complex
**WHY**: Visual inheritance trees help understand relationships
**IMPACT**: Adds diagrams to ALL classes, increases page size significantly
**DECISION**: ❌ **DISABLED** - Not necessary, adds bloat

#### 6. `backlinks: tree`
**WHEN TO USE**: Only if tracking API usage is absolutely critical
**WHY**: Shows where each function/class is referenced
**IMPACT**: Scans ALL documentation, increases build time significantly
**DECISION**: ❌ **DISABLED** - Not necessary, slows builds

#### 7. External Inventories (IMPACT: Build Time)
**WHEN TO USE**: When you reference external libraries frequently
**WHY**: Automatic cross-references to Python docs, aiohttp, etc.
**IMPACT**: Downloads inventory files, increases build time
**DECISION**: ✅ **ENABLED** - ChainedPy uses aiohttp, fsspec, pathlib

```yaml
# ✅ APPROVED CONFIGURATION FOR CHAINEDPY
import:
  - https://docs.python.org/3/objects.inv  # Python stdlib
  - https://docs.aiohttp.org/en/stable/objects.inv  # aiohttp
  - https://fsspec.readthedocs.io/en/latest/objects.inv  # fsspec
```

### MODIFICATION APPROVAL PROCESS

**BEFORE CHANGING mkdocs.yml:**

1. **Identify the specific problem** you're trying to solve
2. **Check the decision matrix above** for the feature
3. **Consider impact on ALL contributors** (build time, page size, licensing)
4. **Get team approval** before modifying global configuration
5. **Test locally** with full documentation build
6. **Document the change** in this standards file

### FORBIDDEN MODIFICATIONS

**❌ DO NOT ENABLE WITHOUT TEAM APPROVAL:**
- Features that significantly increase build time
- Features that change visual layout dramatically
- Features that add unnecessary complexity
- External inventories for libraries we don't use

**❌ DO NOT DISABLE WITHOUT JUSTIFICATION:**
- `show_source` - Users need implementation details
- `cross_references` - Essential for navigation
- `show_signature_annotations` - Required for type clarity

## Code Comments

For comments, you need to add CLEAR section partitioning for big functions and methods with the format: 
 
> `# @@ STEP X: (description). @@`
 
 
Moreover, for sub steps, you need to use this format: 
 
> `# || S.S. X.Y: (description). ||` 
 
 
Lastly, inside steps/sub steps, you need to add comments where relevant. Comments ALWAYS have the following format: 
 
> `# (something that starts with a capital letter and ends with a dot)`
 
 
****EXTREMELY IMPORTANT NOTE****: DO NOT REMOVE THE EXISTING `# TODO` COMMENTS. 

## SUMMARY

These standards ensure **PERFECT** MkDocs rendering with:
- ✅ **Automatic cross-references** to Python stdlib and third-party libraries
- ✅ **Modern type annotations** with clickable links
- ✅ **Inheritance diagrams** with interactive nodes
- ✅ **Backlink tracking** showing API usage
- ✅ **Professional appearance** with zero manual configuration

**COMPLIANCE IS MANDATORY. NO EXCEPTIONS. NO NEGOTIATIONS.**

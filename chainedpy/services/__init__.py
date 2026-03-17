"""ChainedPy Services Module.

This package contains specialized services that implement the core business logic
for ChainedPy operations. Each service is responsible for a specific domain and
follows service-oriented architecture principles, providing clean separation of
concerns and reusable functionality across the ChainedPy ecosystem.

The services are organized by domain: filesystem operations, project management,
template processing, AST analysis, shell integration, and more. All services
maintain consistent error handling, logging, and type safety standards.

Note:
    Services are designed to be stateless and reusable. They can be imported
    and used independently or composed together to implement complex operations.
    Each service defines its own exception types for proper error handling.

Example:
    ```python
    from chainedpy.services import filesystem_service as fs
    from chainedpy.services import template_service
    from pathlib import Path

    # Use filesystem service
    content = fs.read_text(Path("config.yaml"))

    # Use template service
    rendered = template_service.render_template(
        "project/chain_py.j2",
        {"project_name": "my_project"}
    )
    ```

See Also:
    - [filesystem_service][chainedpy.services.filesystem_service]: File system operations
    - [template_service][chainedpy.services.template_service]: Jinja2 template rendering
    - [project_file_service][chainedpy.services.project_file_service]: Project configuration management
    - [ast_service][chainedpy.services.ast_service]: AST analysis and manipulation
"""

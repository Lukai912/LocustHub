from __future__ import annotations

import ast


def validate_locustfile(source: str) -> dict:
    errors: list[str] = []
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        return {"valid": False, "user_class_found": False, "task_count": 0, "errors": [f"Syntax error: {exc.msg}"]}

    user_class_found = False
    task_count = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            base_names = {base.id for base in node.bases if isinstance(base, ast.Name)}
            base_names.update(base.attr for base in node.bases if isinstance(base, ast.Attribute))
            if "HttpUser" in base_names:
                user_class_found = True
        if isinstance(node, ast.FunctionDef):
            # This is a static linter only. It counts @task decorators without
            # importing or executing untrusted tenant code inside the control plane.
            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Name) and decorator.id == "task":
                    task_count += 1
                elif isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Name) and decorator.func.id == "task":
                    task_count += 1

    if not user_class_found:
        errors.append("At least one class must inherit from HttpUser")
    if task_count == 0:
        errors.append("At least one @task function is required")
    return {"valid": not errors, "user_class_found": user_class_found, "task_count": task_count, "errors": errors}

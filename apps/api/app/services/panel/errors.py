class PanelServiceError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class ProjectNotFoundError(PanelServiceError):
    def __init__(self, project_key: str) -> None:
        super().__init__("PROJECT_NOT_FOUND", f"project {project_key} not found")


class RunNotFoundError(PanelServiceError):
    def __init__(self, project_key: str) -> None:
        super().__init__("RUN_NOT_FOUND", f"latest run for project {project_key} not found")

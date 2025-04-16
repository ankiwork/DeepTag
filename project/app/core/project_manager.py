import json


class ProjectManager:
    @staticmethod
    def load_projects(path: str) -> list[dict]:
        """Загружает список проектов из JSON."""
        try:
            with open(path, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return []

import json
import pytest
from pathlib import Path
from unittest.mock import patch
from PyQt6.QtWidgets import QApplication, QInputDialog

app = QApplication([])


@pytest.fixture
def projects_tab(tmp_path: Path):
    """Фикстура для создания тестового экземпляра ProjectsTab."""
    data_dir = tmp_path / "project" / "app" / "data"
    logs_dir = tmp_path / "project" / "app" / "logs"

    data_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)

    data_file = data_dir / "projects.json"
    log_file = logs_dir / "projects.log"

    with patch('project.app.ui.projects_tab.ProjectsTab.data_file', data_file), \
         patch('project.app.ui.projects_tab.ProjectsTab.log_file', log_file):

        from project.app.ui.projects_tab import ProjectsTab
        tab = ProjectsTab()
        yield tab

        handlers = tab.logger.handlers[:]
        for handler in handlers:
            handler.close()
            tab.logger.removeHandler(handler)

    data_file.unlink(missing_ok=True)
    log_file.unlink(missing_ok=True)    


def test_initialization(projects_tab):
    """Тест инициализации класса."""
    assert projects_tab.projects_data == []
    assert projects_tab.table.rowCount() == 0
    assert projects_tab.table.columnCount() == 3
    assert projects_tab.table.horizontalHeaderItem(0).text() == "Название"
    assert projects_tab.table.horizontalHeaderItem(1).text() == "Дата создания"
    assert projects_tab.table.horizontalHeaderItem(2).text() == "Время создания"


def test_add_project(projects_tab):
    """Тест добавления проекта."""
    test_name = "Test Project"
    projects_tab.project_name_input.setText(test_name)
    projects_tab._add_project()

    assert len(projects_tab.projects_data) == 1
    assert projects_tab.projects_data[0]["name"] == test_name
    assert projects_tab.table.rowCount() == 1
    assert projects_tab.table.item(0, 0).text() == test_name
    assert projects_tab.project_name_input.text() == ""


def test_add_empty_project(projects_tab, caplog: pytest.LogCaptureFixture):
    """Тест попытки добавления проекта без имени."""
    initial_count = len(projects_tab.projects_data)
    projects_tab._add_project()
    assert len(projects_tab.projects_data) == initial_count
    assert "Попытка добавить проект без названия" in caplog.text


def test_load_and_save_projects(projects_tab):
    """Тест загрузки и сохранения проектов."""
    test_data = [{"name": "Test", "date": "2023-01-01", "time": "12:00"}]

    # Явное указание типа для файла
    with open(projects_tab.data_file, 'w', encoding='utf-8') as f:
        json.dump(test_data, f)

    projects_tab._load_projects()
    assert len(projects_tab.projects_data) == 1

    projects_tab.projects_data[0]["name"] = "Updated"
    projects_tab._save_projects()

    with open(projects_tab.data_file, 'r', encoding='utf-8') as f:
        saved = json.load(f)
    assert saved[0]["name"] == "Updated"


def test_edit_project(projects_tab, monkeypatch: pytest.MonkeyPatch):
    """Тест редактирования проекта."""
    projects_tab.projects_data = [{"name": "Old", "date": "2023-01-01", "time": "12:00"}]
    projects_tab._update_table()
    projects_tab.table.setCurrentCell(0, 0)

    monkeypatch.setattr(QInputDialog, 'getText', lambda *args: ("New", True))
    projects_tab._edit_project()

    assert projects_tab.projects_data[0]["name"] == "New"
    assert projects_tab.table.item(0, 0).text() == "New"


def test_delete_project(projects_tab, monkeypatch: pytest.MonkeyPatch):
    """Тест удаления проекта."""
    projects_tab.projects_data = [{"name": "To Delete", "date": "2023-01-01", "time": "12:00"}]
    projects_tab._update_table()
    projects_tab.table.setCurrentCell(0, 0)

    monkeypatch.setattr(QInputDialog, 'exec', lambda *args: QInputDialog.DialogCode.Accepted)
    monkeypatch.setattr(QInputDialog, 'textValue', lambda *args: "To Delete")

    projects_tab._delete_project()
    assert len(projects_tab.projects_data) == 0
    assert projects_tab.table.rowCount() == 0


def test_delete_project_cancel(projects_tab, monkeypatch: pytest.MonkeyPatch):
    """Тест отмены удаления проекта."""
    projects_tab.projects_data = [{"name": "Not Deleted", "date": "2023-01-01", "time": "12:00"}]
    projects_tab._update_table()
    projects_tab.table.setCurrentCell(0, 0)

    monkeypatch.setattr(QInputDialog, 'exec', lambda *args: QInputDialog.DialogCode.Rejected)
    projects_tab._delete_project()

    assert len(projects_tab.projects_data) == 1


def test_get_selected_project(projects_tab):
    """Тест получения выбранного проекта."""
    assert projects_tab._get_selected_project() is None

    projects_tab.projects_data = [{"name": "Test", "date": "2023-01-01", "time": "12:00"}]
    projects_tab._update_table()
    projects_tab.table.setCurrentCell(0, 0)

    selected = projects_tab._get_selected_project()
    assert selected is not None
    assert selected["name"] == "Test"

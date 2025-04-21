import json
import pytest
from PyQt6.QtTest import QSignalSpy
from PyQt6.QtCore import QCoreApplication
from unittest.mock import patch, MagicMock
from PyQt6.QtWidgets import QApplication, QMessageBox, QInputDialog

from project.app.ui.subprojects_tab import SubprojectsTab

app = QApplication([])


@pytest.fixture
def subprojects_tab(tmp_path):
    """Фикстура для создания тестового экземпляра SubprojectsTab"""
    data_dir = tmp_path / "project" / "app" / "data"
    logs_dir = tmp_path / "project" / "app" / "logs"

    data_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)

    projects_file = data_dir / "projects.json"
    log_file = logs_dir / "subprojects.log"

    with patch('project.app.ui.subprojects_tab.SubprojectsTab.projects_file', projects_file), \
            patch('project.app.ui.subprojects_tab.SubprojectsTab.log_file', log_file):
        from project.app.ui.subprojects_tab import SubprojectsTab
        tab = SubprojectsTab()
        yield tab

        handlers = tab.logger.handlers[:]
        for handler in handlers:
            handler.close()
            tab.logger.removeHandler(handler)

    projects_file.unlink(missing_ok=True)
    log_file.unlink(missing_ok=True)


@pytest.fixture
def projects_tab_mock():
    """Фикстура-заглушка для ProjectsTab"""
    class MockProjectsTab:
        projects_updated = QSignalSpy()  # type: ignore

    return MockProjectsTab()


def test_initialization(subprojects_tab):
    """Тест инициализации класса"""
    assert subprojects_tab.projects == []
    assert subprojects_tab.filtered_projects == []
    assert subprojects_tab.current_project_index == -1
    assert subprojects_tab.current_project_data is None
    assert subprojects_tab.project_label.text() == "Выберите проект"
    assert subprojects_tab.search_input.placeholderText() == "Поиск проекта..."
    assert not subprojects_tab.prev_button.isEnabled()
    assert not subprojects_tab.next_button.isEnabled()
    assert not subprojects_tab.open_button.isEnabled()


def test_load_projects(subprojects_tab):
    """Тест загрузки проектов"""
    test_data = [
        {"name": "Project 1", "date": "2023-01-01", "time": "12:00"},
        {"name": "Project 2", "date": "2023-01-02", "time": "13:00"}
    ]

    with open(subprojects_tab.projects_file, 'w', encoding='utf-8') as f:
        json.dump(test_data, f)  # type: ignore

    subprojects_tab._load_projects()

    assert len(subprojects_tab.projects) == 2
    assert len(subprojects_tab.filtered_projects) == 2
    assert subprojects_tab.current_project_index == 0
    assert subprojects_tab.project_label.text() == "Выбран проект: Project 1"


def test_filter_projects(subprojects_tab):
    """Тест фильтрации проектов"""
    test_data = [
        {"name": "Alpha", "date": "2023-01-01", "time": "12:00"},
        {"name": "Beta", "date": "2023-01-02", "time": "13:00"},
        {"name": "Gamma", "date": "2023-01-03", "time": "14:00"}
    ]
    subprojects_tab.projects = test_data
    subprojects_tab.filtered_projects = test_data.copy()
    subprojects_tab.current_project_index = 0

    subprojects_tab._filter_projects("a")
    assert len(subprojects_tab.filtered_projects) == 3
    assert subprojects_tab.current_project_index == 0

    subprojects_tab._filter_projects("Beta")
    assert len(subprojects_tab.filtered_projects) == 1
    assert subprojects_tab.filtered_projects[0]["name"] == "Beta"
    assert subprojects_tab.current_project_index == 0

    subprojects_tab._filter_projects("")
    assert len(subprojects_tab.filtered_projects) == 3


def test_open_project(subprojects_tab, tmp_path):
    """Тест открытия проекта"""
    test_projects = [{"name": "Test Project", "date": "2023-01-01", "time": "12:00"}]
    with open(subprojects_tab.projects_file, 'w', encoding='utf-8') as f:
        json.dump(test_projects, f)  # type: ignore

    subprojects_tab._load_projects()
    subprojects_tab.current_project_index = 0

    project_file = tmp_path / "project" / "app" / "data" / "Test Project.json"
    project_file.parent.mkdir(parents=True, exist_ok=True)

    test_project_data = {
        "name": "Test Project",
        "subprojects": [{"name": "Sub1", "date": "2023-01-01", "time": "12:00"}],
        "created": "2023-01-01 12:00:00"
    }
    with open(project_file, 'w', encoding='utf-8') as f:
        json.dump(test_project_data, f)  # type: ignore

    mock_msgbox = MagicMock()
    with patch.object(QMessageBox, 'information', mock_msgbox):
        subprojects_tab._open_project()

    mock_msgbox.assert_called_once()
    assert "Test Project" in mock_msgbox.call_args[0][2]
    assert subprojects_tab.current_project_data is not None
    assert subprojects_tab.project_info_label.text().startswith("Проект: Test Project")
    assert subprojects_tab.subprojects_table.rowCount() == 1


def test_add_subproject(subprojects_tab, tmp_path):
    """Тест добавления подпроекта"""
    test_projects = [{"name": "Test Project", "date": "2023-01-01", "time": "12:00"}]
    with open(subprojects_tab.projects_file, 'w', encoding='utf-8') as f:
        json.dump(test_projects, f)  # type: ignore

    subprojects_tab._load_projects()
    subprojects_tab.current_project_index = 0
    subprojects_tab._open_project()

    subprojects_tab.subproject_name_input.setText("New Subproject")
    subprojects_tab._add_subproject()

    assert len(subprojects_tab.current_project_data["subprojects"]) == 1
    assert subprojects_tab.subprojects_table.rowCount() == 1
    assert subprojects_tab.subprojects_table.item(0, 0).text() == "New Subproject"


def test_edit_subproject(subprojects_tab, tmp_path):
    """Тест редактирования подпроекта"""
    test_projects = [{"name": "Test Project", "date": "2023-01-01", "time": "12:00"}]
    with open(subprojects_tab.projects_file, 'w', encoding='utf-8') as f:
        json.dump(test_projects, f)  # type: ignore

    project_file = tmp_path / "project" / "app" / "data" / "Test Project.json"
    test_data = {
        "name": "Test Project",
        "subprojects": [{"name": "Old Name", "date": "2023-01-01", "time": "12:00"}],
        "created": "2023-01-01 12:00:00"
    }
    with open(project_file, 'w', encoding='utf-8') as f:
        json.dump(test_data, f)  # type: ignore

    subprojects_tab._load_projects()
    subprojects_tab.current_project_index = 0
    subprojects_tab._open_project()
    subprojects_tab.subprojects_table.setCurrentCell(0, 0)

    with patch.object(QInputDialog, 'getText', return_value=("New Name", True)):
        subprojects_tab._edit_subproject()

    assert subprojects_tab.current_project_data["subprojects"][0]["name"] == "New Name"
    assert subprojects_tab.subprojects_table.item(0, 0).text() == "New Name"


def test_delete_subproject(subprojects_tab, tmp_path):
    """Тест удаления подпроекта"""
    test_projects = [{"name": "Test Project", "date": "2023-01-01", "time": "12:00"}]
    with open(subprojects_tab.projects_file, 'w', encoding='utf-8') as f:
        json.dump(test_projects, f)  # type: ignore

    project_file = tmp_path / "project" / "app" / "data" / "Test Project.json"
    test_data = {
        "name": "Test Project",
        "subprojects": [{"name": "To Delete", "date": "2023-01-01", "time": "12:00"}],
        "created": "2023-01-01 12:00:00"
    }
    with open(project_file, 'w', encoding='utf-8') as f:
        json.dump(test_data, f)  # type: ignore

    subprojects_tab._load_projects()
    subprojects_tab.current_project_index = 0
    subprojects_tab._open_project()
    subprojects_tab.subprojects_table.setCurrentCell(0, 0)

    with patch.object(QMessageBox, 'question', return_value=QMessageBox.StandardButton.Yes):
        subprojects_tab._delete_subproject()

    assert len(subprojects_tab.current_project_data["subprojects"]) == 0
    assert subprojects_tab.subprojects_table.rowCount() == 0


def test_navigation(subprojects_tab):
    """Тест навигации по проектам"""
    test_data = [
        {"name": "First", "date": "2023-01-01", "time": "12:00"},
        {"name": "Second", "date": "2023-01-02", "time": "13:00"}
    ]
    subprojects_tab.projects = test_data
    subprojects_tab.filtered_projects = test_data.copy()
    subprojects_tab.current_project_index = 0

    subprojects_tab._next_project()
    assert subprojects_tab.current_project_index == 1
    assert subprojects_tab.project_label.text() == "Выбран проект: Second"
    assert subprojects_tab.prev_button.isEnabled() is True
    assert subprojects_tab.next_button.isEnabled() is False

    subprojects_tab._prev_project()
    assert subprojects_tab.current_project_index == 0
    assert subprojects_tab.project_label.text() == "Выбран проект: First"


def test_reload_projects(subprojects_tab, projects_tab_mock):
    """Тест перезагрузки проектов при изменении"""
    subprojects_tab = SubprojectsTab(projects_tab_mock)

    test_data = [{"name": "Test", "date": "2023-01-01", "time": "12:00"}]
    with open(subprojects_tab.projects_file, 'w', encoding='utf-8') as f:
        json.dump(test_data, f)  # type: ignore

    projects_tab_mock.projects_updated.emit()  # type: ignore
    QCoreApplication.processEvents()

    assert len(subprojects_tab.projects) == 1
    assert subprojects_tab.projects[0]["name"] == "Test"


def test_update_project_display(subprojects_tab):
    """Тест обновления отображения проекта"""
    subprojects_tab._update_project_display("New Project")
    assert subprojects_tab.project_label.text() == "Выбран проект: New Project"

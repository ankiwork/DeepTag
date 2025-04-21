import json
import pytest
from pathlib import Path
from typing import Optional
from unittest.mock import patch, MagicMock
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QApplication, QMessageBox

app = QApplication([])


@pytest.fixture
def projects_tab():
    """Фикстура-заглушка для ProjectsTab с сигналом projects_updated"""

    class DummyProjectsTab(QObject):
        projects_updated = pyqtSignal()

        def __init__(self):
            super().__init__()
            self.projects_data = None

    return DummyProjectsTab()


@pytest.fixture
def subprojects_tab(tmp_path: Path, projects_tab: Optional[QObject] = None):
    """Фикстура для создания тестового экземпляра SubprojectsTab"""
    data_dir = tmp_path / "project" / "app" / "data"
    logs_dir = tmp_path / "project" / "app" / "logs"

    data_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)

    data_file = data_dir / "projects.json"
    log_file = logs_dir / "subprojects.log"

    with patch('project.app.ui.subprojects_tab.SubprojectsTab.projects_file', data_file), \
         patch('project.app.ui.subprojects_tab.SubprojectsTab.log_file', log_file):

        from project.app.ui.subprojects_tab import SubprojectsTab
        tab = SubprojectsTab(projects_tab) if projects_tab else SubprojectsTab()

        if projects_tab:
            projects_tab.projects_updated.connect(tab._reload_projects)  # type: ignore

        yield tab

        handlers = tab.logger.handlers[:]
        for handler in handlers:
            handler.close()
            tab.logger.removeHandler(handler)

    data_file.unlink(missing_ok=True)
    log_file.unlink(missing_ok=True)


def test_initialization(subprojects_tab):
    """Тест инициализации класса"""
    assert subprojects_tab.projects == []
    assert subprojects_tab.filtered_projects == []
    assert subprojects_tab.current_project_index == -1
    assert subprojects_tab.project_label.text() in ["Выберите проект", "Проекты не найдены"]
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
    assert subprojects_tab.prev_button.isEnabled() is False
    assert subprojects_tab.next_button.isEnabled() is True
    assert subprojects_tab.open_button.isEnabled() is True


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


def test_open_project(subprojects_tab, monkeypatch: pytest.MonkeyPatch):
    """Тест открытия проекта"""
    test_data = [{"name": "Test Project", "date": "2023-01-01", "time": "12:00"}]
    subprojects_tab.projects = test_data
    subprojects_tab.filtered_projects = test_data.copy()
    subprojects_tab.current_project_index = 0

    mock_msgbox = MagicMock()
    monkeypatch.setattr(QMessageBox, 'information', mock_msgbox)

    subprojects_tab._open_project()

    mock_msgbox.assert_called_once()
    assert "Test Project" in mock_msgbox.call_args[0][2]


def test_search_project(subprojects_tab):
    """Тест поиска проекта по точному совпадению"""
    test_data = [
        {"name": "Apple", "date": "2023-01-01", "time": "12:00"},
        {"name": "Banana", "date": "2023-01-02", "time": "13:00"}
    ]
    subprojects_tab.projects = test_data
    subprojects_tab.filtered_projects = test_data.copy()
    subprojects_tab.current_project_index = 0

    subprojects_tab.search_input.setText("Banana")
    subprojects_tab._filter_projects("Banana")
    subprojects_tab._search_project()

    assert len(subprojects_tab.filtered_projects) == 1
    assert subprojects_tab.filtered_projects[0]["name"] == "Banana"
    assert subprojects_tab.current_project_index == 0


def test_update_navigation_no_projects(subprojects_tab):
    """Тест обновления навигации при отсутствии проектов"""
    subprojects_tab._update_navigation()

    assert subprojects_tab.project_label.text() == "Проекты не найдены"
    assert not subprojects_tab.prev_button.isEnabled()
    assert not subprojects_tab.next_button.isEnabled()
    assert not subprojects_tab.open_button.isEnabled()


def test_update_project_display(subprojects_tab):
    """Тест обновления отображения проекта"""
    subprojects_tab._update_project_display("New Project")

    assert subprojects_tab.project_label.text() == "Выбран проект: New Project"
    assert subprojects_tab.search_input.text() == ""


def test_subprojects_update_on_projects_change(projects_tab, subprojects_tab, tmp_path):
    """Тест обновления подпроектов при изменении проектов"""
    test_data = [{"name": "Test", "date": "2023-01-01", "time": "12:00"}]

    assert len(subprojects_tab.projects) == 0

    with open(subprojects_tab.projects_file, 'w', encoding='utf-8') as f:
        json.dump(test_data, f)  # type: ignore

    assert subprojects_tab.projects_file.exists()

    projects_tab.projects_updated.emit()  # type: ignore

    assert len(subprojects_tab.projects) == 1
    assert subprojects_tab.projects[0]["name"] == "Test"


def test_reload_projects(subprojects_tab):
    """Тест перезагрузки проектов"""
    test_data = [{"name": "Test", "date": "2023-01-01", "time": "12:00"}]
    subprojects_tab.projects = test_data
    subprojects_tab.filtered_projects = test_data.copy()
    subprojects_tab.current_project_index = 0

    new_data = [{"name": "New", "date": "2023-01-02", "time": "13:00"}]
    with open(subprojects_tab.projects_file, 'w', encoding='utf-8') as f:
        json.dump(new_data, f)  # type: ignore

    subprojects_tab._reload_projects()

    assert len(subprojects_tab.projects) == 1
    assert subprojects_tab.projects[0]["name"] == "New"
    assert subprojects_tab.current_project_index == 0

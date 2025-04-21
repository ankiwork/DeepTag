import json
import pytest
from PyQt6.QtWidgets import *
from PyQt6.QtTest import QSignalSpy
from PyQt6.QtCore import QCoreApplication
from unittest.mock import patch, MagicMock

app = QApplication([])


@pytest.fixture
def projects_tab(tmp_path):
    """Фикстура для создания тестового экземпляра ProjectsTab"""
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


def test_projects_updated_signal(projects_tab):
    """Тест испускания сигнала при изменении проектов"""
    spy = QSignalSpy(projects_tab.projects_updated)

    projects_tab.project_name_input.setText("Test Project")
    projects_tab._add_project()
    assert len(spy) == 1

    projects_tab.table.setCurrentCell(0, 0)
    with patch.object(QInputDialog, 'getText', return_value=("Edited Project", True)):
        projects_tab._edit_project()
    assert len(spy) == 2

    with patch.object(QMessageBox, 'question', return_value=QMessageBox.StandardButton.Yes):
        projects_tab._delete_project()
    assert len(spy) == 3

    QCoreApplication.processEvents()


def test_initialization(projects_tab):
    """Тест инициализации класса"""
    assert projects_tab.projects_data == []
    assert projects_tab.table.rowCount() == 0
    assert projects_tab.table.columnCount() == 3
    assert projects_tab.table.horizontalHeaderItem(0).text() == "Название"
    assert projects_tab.table.horizontalHeaderItem(1).text() == "Дата создания"
    assert projects_tab.table.horizontalHeaderItem(2).text() == "Время создания"
    assert "background-color: #3D3D3D" in projects_tab.table.styleSheet()
    assert "background-color: #2D2D2D" in projects_tab.project_name_input.parent().styleSheet()


def test_add_project(projects_tab):
    """Тест добавления проекта"""
    test_name = "Test Project"
    projects_tab.project_name_input.setText(test_name)
    projects_tab._add_project()

    assert len(projects_tab.projects_data) == 1
    assert projects_tab.projects_data[0]["name"] == test_name
    assert projects_tab.table.rowCount() == 1
    assert projects_tab.table.item(0, 0).text() == test_name
    assert projects_tab.project_name_input.text() == ""


def test_add_empty_project(projects_tab):
    """Тест попытки добавления проекта без имени"""
    initial_count = len(projects_tab.projects_data)

    mock = MagicMock()
    with patch.object(QMessageBox, 'warning', mock):
        projects_tab._add_project()

    assert len(projects_tab.projects_data) == initial_count
    mock.assert_called_once()


def test_add_duplicate_project(projects_tab):
    """Тест добавления дубликата проекта"""
    test_name = "Test Project"
    projects_tab.project_name_input.setText(test_name)
    projects_tab._add_project()

    projects_tab.project_name_input.setText(test_name)

    mock = MagicMock()
    with patch.object(QMessageBox, 'warning', mock):
        projects_tab._add_project()

    assert len(projects_tab.projects_data) == 1
    mock.assert_called_once()


def test_load_and_save_projects(projects_tab):
    """Тест загрузки и сохранения проектов"""
    test_data = [{"name": "Test", "date": "2023-01-01", "time": "12:00:00"}]

    with open(projects_tab.data_file, 'w', encoding='utf-8') as f:
        json.dump(test_data, f)  # type: ignore

    projects_tab._load_projects()
    assert len(projects_tab.projects_data) == 1
    assert projects_tab.table.rowCount() == 1

    assert projects_tab.table.item(0, 0).text() == "Test"
    assert projects_tab.table.item(0, 1).text() == "2023-01-01"
    assert projects_tab.table.item(0, 2).text() == "12:00:00"

    projects_tab.projects_data[0]["name"] = "Modified"
    projects_tab._save_projects()

    with open(projects_tab.data_file, 'r', encoding='utf-8') as f:
        saved_data = json.load(f)

    assert saved_data[0]["name"] == "Modified"


def test_edit_project(projects_tab):
    """Тест редактирования проекта"""
    projects_tab.projects_data = [{"name": "Old", "date": "2023-01-01", "time": "12:00:00"}]
    projects_tab._update_table()
    projects_tab.table.setCurrentCell(0, 0)

    with patch.object(QInputDialog, 'getText', return_value=("New", True)):
        projects_tab._edit_project()

    assert projects_tab.projects_data[0]["name"] == "New"
    assert projects_tab.table.item(0, 0).text() == "New"


def test_edit_project_cancel(projects_tab):
    """Тест отмены редактирования проекта"""
    projects_tab.projects_data = [{"name": "Original", "date": "2023-01-01", "time": "12:00:00"}]
    projects_tab._update_table()
    projects_tab.table.setCurrentCell(0, 0)

    with patch.object(QInputDialog, 'getText', return_value=("", False)):
        projects_tab._edit_project()

    assert projects_tab.projects_data[0]["name"] == "Original"


def test_delete_project(projects_tab):
    """Тест удаления проекта"""
    projects_tab.projects_data = [{"name": "To Delete", "date": "2023-01-01", "time": "12:00:00"}]
    projects_tab._update_table()
    projects_tab.table.setCurrentCell(0, 0)

    with patch.object(QMessageBox, 'question', return_value=QMessageBox.StandardButton.Yes):
        projects_tab._delete_project()

    assert len(projects_tab.projects_data) == 0
    assert projects_tab.table.rowCount() == 0


def test_delete_project_cancel(projects_tab):
    """Тест отмены удаления проекта"""
    projects_tab.projects_data = [{"name": "Not Deleted", "date": "2023-01-01", "time": "12:00:00"}]
    projects_tab._update_table()
    projects_tab.table.setCurrentCell(0, 0)

    with patch.object(QMessageBox, 'question', return_value=QMessageBox.StandardButton.No):
        projects_tab._delete_project()

    assert len(projects_tab.projects_data) == 1


def test_get_selected_project(projects_tab):
    """Тест получения выбранного проекта"""
    assert projects_tab._get_selected_project() is None

    projects_tab.projects_data = [{"name": "Test", "date": "2023-01-01", "time": "12:00:00"}]
    projects_tab._update_table()
    projects_tab.table.setCurrentCell(0, 0)

    selected = projects_tab._get_selected_project()
    assert selected is not None
    assert selected["name"] == "Test"


def test_table_selection_behavior(projects_tab):
    """Тест поведения таблицы при выборе"""
    assert projects_tab.table.selectionBehavior() == QTableWidget.SelectionBehavior.SelectRows
    assert projects_tab.table.editTriggers() == QTableWidget.EditTrigger.NoEditTriggers


def test_table_header_resizing(projects_tab):
    """Тест поведения заголовков таблицы"""
    header = projects_tab.table.horizontalHeader()
    assert header.sectionResizeMode(0) == QHeaderView.ResizeMode.Stretch
    assert header.sectionResizeMode(1) == QHeaderView.ResizeMode.Stretch
    assert header.sectionResizeMode(2) == QHeaderView.ResizeMode.Stretch
    assert not projects_tab.table.verticalHeader().isVisible()
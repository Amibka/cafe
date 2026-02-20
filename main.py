import sqlite3
import sys
from pathlib import Path
from shutil import copy2

from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QMainWindow,
    QMessageBox,
    QTableWidgetItem,
)

from UI.ui_add_edit_coffee_form import Ui_AddEditCoffeeForm
from UI.ui_main import Ui_MainWindow


def get_base_dir():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


BASE_DIR = get_base_dir()
DB_PATH = BASE_DIR / "data" / "coffee.sqlite"


def ensure_database_exists():
    if DB_PATH.exists():
        return

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    if not getattr(sys, "frozen", False):
        return

    meipass_path = getattr(sys, "_MEIPASS", "")
    if not meipass_path:
        return

    bundled_db = Path(meipass_path) / "data" / "coffee.sqlite"
    if bundled_db.exists():
        copy2(bundled_db, DB_PATH)


class AddEditCoffeeForm(QDialog):
    def __init__(self, coffee_id=None, parent=None):
        super().__init__(parent)
        self.ui = Ui_AddEditCoffeeForm()
        self.ui.setupUi(self)
        self.coffee_id = coffee_id

        self.ui.is_ground_combo.addItem("В зернах", 0)
        self.ui.is_ground_combo.addItem("Молотый", 1)

        self.ui.save_button.clicked.connect(self.save_record)
        self.ui.cancel_button.clicked.connect(self.reject)

        if self.coffee_id is not None:
            self.load_record()

    def load_record(self):
        try:
            with sqlite3.connect(DB_PATH) as con:
                cur = con.cursor()
                row = cur.execute(
                    """
                    SELECT sort_name,
                           roast_level,
                           is_ground,
                           taste_description,
                           price,
                           package_volume
                    FROM coffee
                    WHERE id = ?
                    """,
                    (self.coffee_id,),
                ).fetchone()
        except sqlite3.Error as error:
            QMessageBox.critical(self, "Ошибка SQLite", str(error))
            self.reject()
            return

        if row is None:
            QMessageBox.warning(self, "Ошибка", "Запись не найдена.")
            self.reject()
            return

        self.ui.sort_name_edit.setText(row[0])
        self.ui.roast_level_edit.setText(row[1])
        self.ui.taste_description_edit.setText(row[3])
        self.ui.price_spin.setValue(float(row[4]))
        self.ui.package_volume_spin.setValue(int(row[5]))
        index = self.ui.is_ground_combo.findData(int(row[2]))
        if index >= 0:
            self.ui.is_ground_combo.setCurrentIndex(index)

    def save_record(self):
        sort_name = self.ui.sort_name_edit.text().strip()
        roast_level = self.ui.roast_level_edit.text().strip()
        taste_description = self.ui.taste_description_edit.text().strip()
        is_ground = int(self.ui.is_ground_combo.currentData())
        price = float(self.ui.price_spin.value())
        package_volume = int(self.ui.package_volume_spin.value())

        if not sort_name or not roast_level or not taste_description:
            QMessageBox.warning(
                self,
                "Ошибка",
                "Заполните все текстовые поля.",
            )
            return

        try:
            with sqlite3.connect(DB_PATH) as con:
                cur = con.cursor()
                if self.coffee_id is None:
                    cur.execute(
                        """
                        INSERT INTO coffee (
                            sort_name,
                            roast_level,
                            is_ground,
                            taste_description,
                            price,
                            package_volume
                        )
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (
                            sort_name,
                            roast_level,
                            is_ground,
                            taste_description,
                            price,
                            package_volume,
                        ),
                    )
                else:
                    cur.execute(
                        """
                        UPDATE coffee
                        SET sort_name = ?,
                            roast_level = ?,
                            is_ground = ?,
                            taste_description = ?,
                            price = ?,
                            package_volume = ?
                        WHERE id = ?
                        """,
                        (
                            sort_name,
                            roast_level,
                            is_ground,
                            taste_description,
                            price,
                            package_volume,
                            self.coffee_id,
                        ),
                    )
                con.commit()
        except sqlite3.Error as error:
            QMessageBox.critical(self, "Ошибка SQLite", str(error))
            return

        self.accept()


class CoffeeApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.refresh_button.clicked.connect(self.load_data)
        self.ui.add_button.clicked.connect(self.open_add_form)
        self.ui.edit_button.clicked.connect(self.open_edit_form)
        self.load_data()

    def load_data(self):
        if not DB_PATH.exists():
            QMessageBox.critical(
                self,
                "Ошибка",
                f"База данных не найдена: {DB_PATH}",
            )
            return

        try:
            with sqlite3.connect(DB_PATH) as con:
                cur = con.cursor()
                rows = cur.execute(
                    """
                    SELECT id,
                           sort_name,
                           roast_level,
                           is_ground,
                           taste_description,
                           price,
                           package_volume
                    FROM coffee
                    ORDER BY id
                    """
                ).fetchall()
        except sqlite3.Error as error:
            QMessageBox.critical(self, "Ошибка SQLite", str(error))
            return

        headers = [
            "ID",
            "Название сорта",
            "Степень обжарки",
            "Молотый/в зернах",
            "Описание вкуса",
            "Цена",
            "Объем упаковки",
        ]
        self.ui.coffee_table.setColumnCount(len(headers))
        self.ui.coffee_table.setHorizontalHeaderLabels(headers)
        self.ui.coffee_table.setRowCount(len(rows))

        for row_index, row_data in enumerate(rows):
            row_values = list(row_data)
            row_values[3] = "Молотый" if int(row_values[3]) else "В зернах"
            for col_index, value in enumerate(row_values):
                self.ui.coffee_table.setItem(
                    row_index,
                    col_index,
                    QTableWidgetItem(str(value)),
                )

        self.ui.coffee_table.resizeColumnsToContents()

    def open_add_form(self):
        dialog = AddEditCoffeeForm(parent=self)
        if dialog.exec():
            self.load_data()

    def open_edit_form(self):
        current_row = self.ui.coffee_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(
                self,
                "Ошибка",
                "Выберите запись для редактирования.",
            )
            return

        id_item = self.ui.coffee_table.item(current_row, 0)
        if id_item is None:
            QMessageBox.warning(
                self,
                "Ошибка",
                "Не удалось получить ID записи.",
            )
            return

        coffee_id = int(id_item.text())
        dialog = AddEditCoffeeForm(coffee_id=coffee_id, parent=self)
        if dialog.exec():
            self.load_data()


if __name__ == "__main__":
    ensure_database_exists()
    app = QApplication(sys.argv)
    window = CoffeeApp()
    window.show()
    sys.exit(app.exec())

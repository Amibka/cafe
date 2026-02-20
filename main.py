import sqlite3
import sys
from pathlib import Path

from PyQt6 import uic
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QMainWindow,
    QMessageBox,
    QTableWidgetItem,
)

DB_NAME = "coffee.sqlite"


class AddEditCoffeeForm(QDialog):
    def __init__(self, coffee_id=None, parent=None):
        super().__init__(parent)
        uic.loadUi("addEditCoffeeForm.ui", self)
        self.coffee_id = coffee_id

        self.is_ground_combo.addItem("В зернах", 0)
        self.is_ground_combo.addItem("Молотый", 1)

        self.save_button.clicked.connect(self.save_record)
        self.cancel_button.clicked.connect(self.reject)

        if self.coffee_id is not None:
            self.load_record()

    def load_record(self):
        try:
            with sqlite3.connect(DB_NAME) as con:
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

        self.sort_name_edit.setText(row[0])
        self.roast_level_edit.setText(row[1])
        self.taste_description_edit.setText(row[3])
        self.price_spin.setValue(float(row[4]))
        self.package_volume_spin.setValue(int(row[5]))
        index = self.is_ground_combo.findData(int(row[2]))
        if index >= 0:
            self.is_ground_combo.setCurrentIndex(index)

    def save_record(self):
        sort_name = self.sort_name_edit.text().strip()
        roast_level = self.roast_level_edit.text().strip()
        taste_description = self.taste_description_edit.text().strip()
        is_ground = int(self.is_ground_combo.currentData())
        price = float(self.price_spin.value())
        package_volume = int(self.package_volume_spin.value())

        if not sort_name or not roast_level or not taste_description:
            QMessageBox.warning(
                self,
                "Ошибка",
                "Заполните все текстовые поля.",
            )
            return

        try:
            with sqlite3.connect(DB_NAME) as con:
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
        uic.loadUi("main.ui", self)
        self.refresh_button.clicked.connect(self.load_data)
        self.add_button.clicked.connect(self.open_add_form)
        self.edit_button.clicked.connect(self.open_edit_form)
        self.load_data()

    def load_data(self):
        db_path = Path(DB_NAME)
        if not db_path.exists():
            QMessageBox.critical(
                self,
                "Ошибка",
                f"База данных не найдена: {DB_NAME}",
            )
            return

        try:
            with sqlite3.connect(DB_NAME) as con:
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
        self.coffee_table.setColumnCount(len(headers))
        self.coffee_table.setHorizontalHeaderLabels(headers)
        self.coffee_table.setRowCount(len(rows))

        for row_index, row_data in enumerate(rows):
            row_values = list(row_data)
            row_values[3] = "Молотый" if int(row_values[3]) else "В зернах"
            for col_index, value in enumerate(row_values):
                self.coffee_table.setItem(
                    row_index,
                    col_index,
                    QTableWidgetItem(str(value)),
                )

        self.coffee_table.resizeColumnsToContents()

    def open_add_form(self):
        dialog = AddEditCoffeeForm(parent=self)
        if dialog.exec():
            self.load_data()

    def open_edit_form(self):
        current_row = self.coffee_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(
                self,
                "Ошибка",
                "Выберите запись для редактирования.",
            )
            return

        id_item = self.coffee_table.item(current_row, 0)
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
    app = QApplication(sys.argv)
    window = CoffeeApp()
    window.setWindowTitle("Каталог кофе")
    window.show()
    sys.exit(app.exec())

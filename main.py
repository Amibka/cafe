import sqlite3
import sys
from pathlib import Path

from PyQt6 import uic
from PyQt6.QtWidgets import QApplication, QMainWindow, QMessageBox, QTableWidgetItem


DB_NAME = "coffee.sqlite"


class CoffeeApp(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("main.ui", self)

        self.refresh_button.clicked.connect(self.load_data)
        self.load_data()

    def load_data(self):
        db_path = Path(DB_NAME)
        if not db_path.exists():
            QMessageBox.critical(self, "Ошибка", f"База данных не найдена: {DB_NAME}")
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

        self.coffee_table.setRowCount(len(rows))
        self.coffee_table.setColumnCount(8)
        self.coffee_table.setHorizontalHeaderLabels(
            [
                "ID",
                "Название сорта",
                "Степень обжарки",
                "Молотый/в зернах",
                "Описание вкуса",
                "Цена",
                "Объем упаковки",
                "Ед. объема",
            ]
        )

        for row_index, row_data in enumerate(rows):
            for col_index, value in enumerate(row_data):
                if col_index == 3:
                    value = "Молотый" if int(value) else "В зернах"
                self.coffee_table.setItem(row_index, col_index, QTableWidgetItem(str(value)))

        self.coffee_table.resizeColumnsToContents()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CoffeeApp()
    window.setWindowTitle("Каталог кофе")
    window.show()
    sys.exit(app.exec())

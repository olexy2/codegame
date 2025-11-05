import json
import os
from time import sleep
import sys
import random
from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QGridLayout, QLineEdit, QLabel, QGraphicsBlurEffect, QStackedWidget, QMainWindow, QTextEdit
from PyQt6.QtGui import QFont, QMovie, QKeyEvent, QColor
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QUrl

class EnemyPlayer:
    def __init__(self):
        self.enemy_code = []          # digits are being saved here

    def exceptions(self, nums: list[int]) -> str | None:
        if len(nums) != 4:
            return "Type in exactly 4 digits"
        if len(set(nums)) != 4:
            return "Digits cannot repeat"
        if any(n < 0 or n > 9 for n in nums):
            return "Digits have to be in between 0-9."

        return None

class GuessPlayer:
    def __init__(self):
        self.guesser_code = []  # digits are being saved here [[2,3,4,5], [4,5,6,7]]
        self.guesser_hints = []

    def exceptions(self, nums: list[int]) -> str | None:
        if len(nums) != 4:
            return "Type in exactly 4 digits"
        if len(set(nums)) != 4:
            return "Digits cannot repeat"
        if any(n < 0 or n > 9 for n in nums):
            return "Digits have to be in between 0-9."

        return None

class DigitInput(QLineEdit):
    backspace_pressed = pyqtSignal(int)

    def __init__(self, index, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.index = index

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Backspace:
            if not self.text() and self.index > 0:
                self.backspace_pressed.emit(self.index)
            else:
                super().keyPressEvent(event)
        else:
            super().keyPressEvent(event)

class AppWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("CODE by Michal Olecki")
        self.setFixedSize(800, 600)

        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        self.start_menu = StartMenu(self.stacked_widget)
        self.main_game = MainWindow(self.stacked_widget)
        self.single_game = SinglePlayerMode(self.stacked_widget)

        self.stacked_widget.addWidget(self.start_menu)  # index 0
        self.stacked_widget.addWidget(self.main_game)   # index 1
        self.stacked_widget.addWidget(self.single_game) # index 2

class StartMenu(QWidget):
    def __init__(self, stacked_widget):
        super().__init__()
        self.stacked_widget = stacked_widget

        self.setAutoFillBackground(True)

        palette = self.palette()
        palette.setColor(self.backgroundRole(), QColor('grey'))
        self.setPalette(palette)
        layout = QGridLayout()

        label = QLabel('CODE', self)
        label.setStyleSheet('font-size: 44px;')
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label, 0, 0, 1, 1)

        two_players_btn = QPushButton('2 players mode')
        two_players_btn.setStyleSheet('padding: 10px; font-size: 16px;')
        two_players_btn.clicked.connect(self.open_main_window)
        label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(two_players_btn, 1, 0, 2, 1)

        single_mode_btn = QPushButton('1 player mode')
        single_mode_btn.setStyleSheet('padding: 10px; font-size: 16px;')
        single_mode_btn.clicked.connect(self.open_single_mode)
        label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(single_mode_btn, 2, 0, 2, 1)

        self.setLayout(layout)

    def open_main_window(self):
        self.stacked_widget.setCurrentIndex(1)

    def open_single_mode(self):
        self.stacked_widget.setCurrentIndex(2)

class MainWindow(QWidget):
    # ----------- INITIALIZATION (title, background color etc.) ---------------------------
    def __init__(self, stacked_widget):
        super().__init__()
        self.stacked_widget = stacked_widget
        self.setAutoFillBackground(True)

        palette = self.palette()
        palette.setColor(self.backgroundRole(), QColor('light blue'))
        self.setPalette(palette)

        self.enemy = EnemyPlayer()
        self.guesser = GuessPlayer()
        self.build_ui()

    def build_ui(self):
        layout = QGridLayout()
        font = QFont(); font.setPointSize(44)
        self.color = 'white'

        self.inputs = []
        for i in range(4):
            self.le = DigitInput(i)
            self.le.setMaxLength(1)
            self.le.setFont(font)
            self.le.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.le.setFixedSize(100, 100)
            self.le.setStyleSheet(f'color: {self.color}; background-color: rgba(0, 0, 0, 180);')
            layout.addWidget(self.le, 0, i)
            self.inputs.append(self.le)
            self.le.textChanged.connect(lambda text, idx= i: self.move_focus(text, idx))
            self.le.backspace_pressed.connect(self.move_back)

        # ----------- BUTTONS ---------------------------
        self.btn_enemy = QPushButton("Enemy Accept")
        self.btn_enemy.setStyleSheet('color: white; background-color: rgba(0, 0, 0, 180);')
        self.btn_enemy.clicked.connect(self.enemy_accept)
        layout.addWidget(self.btn_enemy, 1, 0, 1, 4)

        self.btn_guesser = QPushButton("Guesser Accept")
        self.btn_guesser.setStyleSheet('color: white; background-color: rgba(0, 0, 0, 180);')
        self.btn_guesser.setEnabled(False)
        self.btn_guesser.clicked.connect(self.guesser_accept)
        layout.addWidget(self.btn_guesser, 2, 0, 1, 4)

        self.reset_btn = QPushButton('Reset Game')
        self.reset_btn.setStyleSheet('color: white; background-color: rgba(0, 0, 0, 180);')
        self.reset_btn.clicked.connect(self.reset_all)
        layout.addWidget(self.reset_btn, 6, 0, 1, 7)

        self.to_menu = QPushButton('Go to Menu')
        self.to_menu.setStyleSheet('color: white; background-color: rgba(0, 0, 0, 180);')
        self.to_menu.setEnabled(True)
        self.to_menu.clicked.connect(self.go_to_menu)
        layout.addWidget(self.to_menu, 8, 0, 1, 7)

        # ----------- LABELS AND LAYOUT ---------------------------
        self.guesser_msg = QLabel()
        self.guesser_msg.setStyleSheet('''
        color: #FF00BF;
        font-size: 28px;
        background-color: rgba(0, 0, 0, 180);
        padding 5px;
        border-radius: 5px;
        ''')
        self.guesser_msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.guesser_msg.setFixedHeight(100)
        layout.addWidget(self.guesser_msg, 5, 0, 1, 4)

        self.hint_label = QLabel('HINT')
        self.hint_label.setStyleSheet('color: white; font-size: 44px;')
        self.hint_label.setAlignment(Qt.AlignmentFlag.AlignBottom| Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(self.hint_label, 4, 1, 1, 2)

        self.notes = QTextEdit('Type your notes here')
        self.notes.setEnabled(True)
        self.notes.setStyleSheet('font-size: 22px')
        layout.addWidget(self.notes, 3, 0, 1, 4)
        self.notes.setAlignment(Qt.AlignmentFlag.AlignTop| Qt.AlignmentFlag.AlignHCenter)

        self.log_msg = QLabel()
        self.log_msg.setStyleSheet('''
        color: white; 
        font-size: 22px;
        background-color: rgba(0, 0, 0, 180);
        padding 5px;
        border-radius: 5px;
        ''')
        self.log_msg.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(self.log_msg, 1, 4, 5, 2)

        self.log_label = QLabel('LOGS')
        self.log_label.setStyleSheet('color: white; font-size: 22px;')
        self.log_label.setAlignment(Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(self.log_label, 0, 4, 1, 2)

        self.hint_log_msg = QLabel()
        self.hint_log_msg.setStyleSheet('''
        color: white; 
        font-size: 22px;
        background-color: rgba(0, 0, 0, 180);
        padding 5px;
        border-radius: 5px;
        ''')
        self.hint_log_msg.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(self.hint_log_msg, 1, 6, 5, 1)

        self.hint_log_label = QLabel('HINT LOG')
        self.hint_log_label.setStyleSheet('color: white; font-size: 22px;')
        self.hint_log_label.setAlignment(Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(self.hint_log_label, 0, 6, 1, 1)

        self.setLayout(layout)

# ---------------------ENEMY BUTTON SIGNAL--------------------------------
    def enemy_accept(self):
        try:
            nums = [int(le.text()) for le in self.inputs]
            self.enemy.enemy_code = nums

        except ValueError:
            self.guesser_msg.setText("All fields have \n to be filled with digits 0-9")
            return

        err = self.enemy.exceptions(nums)
        if err:
            self.guesser_msg.setText(err)
            return
        else:
            self.guesser_msg.setText(f"CODE SAVED: {''.join(map(str, nums))}")
            QTimer.singleShot(2000, lambda: self.guesser_msg.setText(''))

            log_event(f'started new game with 2 players, enemy code: {nums}')

        if len(nums) != 0:
            self.btn_guesser.setEnabled(True)

        self._clearing_inputs = True
        self.clear_inputs()
        self._clearing_inputs = False
        self.btn_enemy.setEnabled(False)

# ---------------------GUESSER BUTTON SIGNAL------------------------------
    def guesser_accept(self):
        att = len(self.guesser.guesser_code) + 1
        try:
            nums = [int(le.text()) for le in self.inputs]
        except ValueError:
            self.guesser_msg.setText("All fields have \n to be filled with digits 0-9")
            return

        err = self.guesser.exceptions(nums)
        if err:
            self.guesser_msg.setText(err)
        elif nums == self.enemy.enemy_code:
            self.log_printing()
            self.guesser.guesser_hints.append('CORRECT')
            log_event('correct code, game over')
            self.hint_logs_printing()
            self.btn_guesser.setEnabled(False)
            self.guesser_msg.setStyleSheet(self.guesser_msg.styleSheet() + 'color: green;')
            self.guesser_msg.setText('The code is correct')
            QTimer.singleShot(2000, lambda: self.guesser_msg.setText(f'win in {att} attempts'))
        else:
            log_event(f'attempt{att}, code: {nums}')
            self.verification(nums)
            self.hint_logs_printing()
            self.log_printing()

        self.clear_inputs()
        self.inputs[0].setFocus()

# ---------------------LOG PANEL---------------------------------------
    def log_printing(self):
        g_code = self.guesser.guesser_code
        nums = [int(le.text()) for le in self.inputs]
        g_code.append(nums)

        logs = [''.join(map(str, entry)) for entry in g_code]

        if len(logs) > 14:
            disp_logs = logs[-14:]
        else:
            disp_logs = logs

        self.log_msg.setText('\n'.join(disp_logs))

    def hint_logs_printing(self):
        g_hints = self.guesser.guesser_hints

        if len(g_hints) > 14:
            disp_h_logs = g_hints[-14:]
        else:
            disp_h_logs = g_hints

        self.hint_log_msg.setText('\n'.join(disp_h_logs))
        print(g_hints)

# ---------------------ADDITIONAL METHODS------------------------------
    def verification(self, guess_nums):
        right = 0
        right_place = 0

        if len(self.enemy.enemy_code) == 4:
            for i, val in enumerate(guess_nums):
                if val in self.enemy.enemy_code:
                    right += 1
                if val == self.enemy.enemy_code[i]:
                    right_place += 1

            self.guesser_msg.setText(f"{right} right digits {right_place} in a right place")
            self.guesser.guesser_hints.append(f'{right} R    {right_place} RP')

    def clear_inputs(self):
        self.disconnect_input_signals()
        for field in self.inputs:
            field.clear()
        self.connect_input_signals()

    def reset_all(self):

        self.clear_inputs()
        self.enemy.enemy_code = []
        self.guesser.guesser_code = []

        self.guesser_msg.clear()
        self.guesser_msg.setStyleSheet(self.guesser_msg.styleSheet() + 'color: #FF00BF;')

        self.log_msg.clear()

        self.hint_log_msg.clear()

        self.guesser = GuessPlayer()
        self.enemy = EnemyPlayer()
        self.btn_enemy.setEnabled(True)

    def go_to_menu(self):
        self.stacked_widget.setCurrentIndex(0)

    def move_focus(self, text, idx):
        if text and idx + 1 < len(self.inputs):
            self.inputs[idx+1].setFocus()

    def move_back(self, idx):
        if idx > 0:
            prev_input = self.inputs[idx - 1]
            prev_input.setFocus()
            prev_input.setText('')

    def resizeEvent(self, event):
        super().resizeEvent(event)

    def disconnect_input_signals(self):
        for i, field in enumerate(self.inputs):
            try:
                field.textChanged.disconnect()
                field.backspace_pressed.disconnect()
            except TypeError:
                # sygnał mógł już być odłączony – ignorujemy
                pass

    def connect_input_signals(self):
        for i, field in enumerate(self.inputs):
            field.textChanged.connect(lambda text, idx=i: self.move_focus(text, idx))
            field.backspace_pressed.connect(self.move_back)


def log_event(message, filename="log.json"):
    try:
        # Wczytaj dane, jeśli plik istnieje
        if os.path.exists(filename):
            with open(filename, "r") as f:
                try:
                    data = json.load(f)
                    if not isinstance(data, list):
                        data = []
                except json.JSONDecodeError:
                    data = []
        else:
            data = []

        # Dodaj nowy wpis
        data.append(message)

        # Zapisz nową zawartość
        with open(filename, "w") as f:
            json.dump(data, f, indent=4)

    except Exception as e:
        print(f"Logging error: {e}")

class SinglePlayerMode(MainWindow):
    def __init__(self, stacked_widget):
        super().__init__(stacked_widget)

        layout = self.layout() or QGridLayout()
        self.setLayout(layout)

        self.btn_enemy.hide()
        self.btn_guesser.hide()
        self.reset_btn.hide()
        for le in self.inputs:
            le.setEnabled(False)

        self.btn_gen_code = QPushButton('Generate Code')
        self.btn_gen_code.setStyleSheet('color: white; background-color: rgba(0, 0, 0, 180);')
        self.btn_gen_code.clicked.connect(self.gen_code)
        self.layout().addWidget(self.btn_gen_code, 1, 0, 1, 4)

        self.btn_accept = QPushButton('Accept')
        self.btn_accept.setStyleSheet('color: white; background-color: rgba(0, 0, 0, 180);')
        self.btn_accept.setEnabled(False)
        self.btn_accept.clicked.connect(self.accept)
        self.layout().addWidget(self.btn_accept, 2, 0, 1, 4)

        self.reset_btn_new = QPushButton('Reset Game')
        self.reset_btn_new.setStyleSheet('color: white; background-color: rgba(0, 0, 0, 180);')
        self.reset_btn_new.clicked.connect(self.reset_all_s_mode)
        layout.addWidget(self.reset_btn_new, 6, 0, 1, 7)

    def gen_code(self):
        self.enemy.enemy_code = random.sample(range(10), 4)
        self.btn_accept.setEnabled(True)
        self.btn_gen_code.setEnabled(False)
        for le in self.inputs:
            le.setEnabled(True)
        self.guesser_msg.setText('CODE HAS BEEN\n GENERATED')
        log_event(f'new game in singleplayer mode started, generated code: {self.enemy.enemy_code}')

    def accept(self):
        att = len(self.guesser.guesser_code) + 1
        try:
            nums = [int(le.text()) for le in self.inputs]
        except ValueError:
            self.guesser_msg.setText("All fields have \n to be filled with digits 0-9")
            return

        err = self.guesser.exceptions(nums)
        if err:
            self.guesser_msg.setText(err)
        elif nums == self.enemy.enemy_code:
            self.log_printing()
            self.guesser.guesser_hints.append('CORRECT')
            log_event('correct code, game over')
            self.hint_logs_printing()
            self.btn_gen_code.setEnabled(False)
            self.guesser_msg.setStyleSheet(self.guesser_msg.styleSheet() + 'color: green;')
            self.guesser_msg.setText('The code is correct')
            QTimer.singleShot(2000, lambda: self.guesser_msg.setText(f'win in {att} attempts'))
        else:
            self.verification(nums)
            self.hint_logs_printing()
            self.log_printing()

        self.clear_inputs()
        self.inputs[0].setFocus()

    def reset_all_s_mode(self):
        self.clear_inputs()
        self.enemy.enemy_code = []
        self.guesser.guesser_code = []

        self.guesser_msg.clear()
        self.guesser_msg.setStyleSheet(self.guesser_msg.styleSheet() + 'color: #FF00BF;')

        self.log_msg.clear()

        self.hint_log_msg.clear()

        self.guesser = GuessPlayer()
        self.enemy = EnemyPlayer()
        self.btn_gen_code.setEnabled(True)
        self.btn_accept.setEnabled(False)

        print(self.guesser.guesser_code)

if __name__ == '__main__':
    app = QApplication(sys.argv)

    window = AppWindow()
    window.show()

    sys.exit(app.exec())
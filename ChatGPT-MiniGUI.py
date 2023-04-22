import configparser
import os

from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QScrollArea, QTextEdit, QGridLayout, QLabel, QPushButton, QFrame, QLayout, \
    QGraphicsOpacityEffect
from PySide6.QtCore import QSize, Qt, QEvent, QObject, QRunnable, Signal, Slot, QTimer, QThreadPool, QPoint, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QPalette, QColor, QPixmap, QGuiApplication, QKeyEvent, QFont, QMovie
from PySide6 import QtGui, QtCore
from io import StringIO
import faulthandler
import openai
import sys


def read_config():
    config = configparser.ConfigParser()
    config.optionxform = str

    if not os.path.exists('config.ini'):
        config['API Keys'] = {'OpenAI': 'APIKeyHere'}

        with open('config.ini', 'w') as configfile:
            config.write(configfile)

    config.read('config.ini')
    return config


class Worker(QObject, QRunnable):
    result = Signal(str)

    def __init__(self, func=None, *args, **kwargs):
        QObject.__init__(self)
        QRunnable.__init__(self)

        self.func = func
        self.args = args
        self.kwargs = kwargs

        self.args = (self, *self.args)

    @Slot()
    def run(self):
        self.func(*self.args, **self.kwargs)


class CustomWindowFrame(QWidget):

    def __init__(self, title, icon=None, closable=True, maximizable=True, minimizable=True, movable=True):
        super().__init__()
        self.setFixedHeight(30)

        self.movable = movable

        self.mouse_offset = None
        self.grabbed = False

        # Structure
        self.title_body = QGridLayout()
        self.title_body.setContentsMargins(6, 0, 6, 0)

        self.title_container = QWidget()
        self.title_container.setFixedHeight(15)

        self.body = QVBoxLayout()
        self.body.setContentsMargins(0, 6, 0, 2)

        # Components
        if icon is not None:
            self.icon = QLabel()
            self.icon.setPixmap(QPixmap(icon).scaled(15, 15, mode=Qt.SmoothTransformation))
            self.icon.resize(QSize(15, 15))

        self.title = QLabel(title)
        self.title.setStyleSheet('font-size: 16px')

        self.minimize_btn = QPushButton('–')
        self.minimize_btn.setFixedWidth(12)
        self.minimize_btn.setFlat(True)
        self.minimize_btn.setStyleSheet('font-size: 16px')

        self.maximize_btn = QPushButton('❒')
        self.maximize_btn.setFixedWidth(12)
        self.maximize_btn.setFlat(True)
        self.maximize_btn.setStyleSheet('font-size: 16px')

        self.exit_btn = QPushButton('X')
        self.exit_btn.setFixedWidth(12)
        self.exit_btn.setFlat(True)
        self.exit_btn.setStyleSheet('font-size: 16px')

        self.separator = QFrame()
        self.separator.setFrameShape(QFrame.Shape.HLine)
        self.separator.setFrameShadow(QFrame.Shadow.Sunken)

        # Functionality
        self.minimize_btn.clicked.connect(self.minimize)
        self.maximize_btn.clicked.connect(self.maximize)
        self.exit_btn.clicked.connect(self.exit)

        # Assembly
        if icon is not None:
            self.title_body.addWidget(self.icon, 0, 0, alignment=Qt.AlignLeft)

        self.title_body.addWidget(self.title, 0, 1, alignment=Qt.AlignLeft)

        if minimizable:
            self.title_body.addWidget(self.minimize_btn, 0, 2, alignment=Qt.AlignRight)

        if maximizable:
            self.title_body.addWidget(self.maximize_btn, 0, 3, alignment=Qt.AlignRight)

        if closable:
            self.title_body.addWidget(self.exit_btn, 0, 4, alignment=Qt.AlignRight)

        self.title_body.setColumnStretch(1, 1)
        self.title_container.setLayout(self.title_body)

        self.body.addWidget(self.title_container)
        self.body.addWidget(self.separator)

        self.setLayout(self.body)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)

        if not self.movable:
            return

        self.mouse_offset = event.pos()

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent) -> None:
        super().mouseReleaseEvent(event)

        if not self.movable:
            return

        self.grabbed = False

    def mouseMoveEvent(self, event: QtGui.QMouseEvent) -> None:
        super().mouseMoveEvent(event)

        if not self.movable:
            return

        if not self.grabbed and event.y() < self.height() and self.mouse_offset.y() < self.height():
            self.grabbed = True

        if self.grabbed:
            x, y = event.globalX(), event.globalY()
            self.parent().move(x - self.mouse_offset.x(), y - self.mouse_offset.y())

    def minimize(self):
        self.parent().hide()

    def maximize(self):
        mw, mh = QGuiApplication.screens()[0].size().toTuple()

        if self.parent().size() == QSize(mw - 1, mh - 1):
            self.parent().resize(QSize(420, 510))
            self.parent().move(QGuiApplication.screens()[0].geometry().center() - self.parent().frameGeometry().center())

        else:
            self.parent().resize(QSize(mw - 1, mh - 1))
            self.parent().move(0, 0)

    def exit(self):
        app.quit()


class MessageBlock(QTextEdit):

    def __init__(self, text):
        super().__init__()
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setFixedWidth(800)
        self.setReadOnly(True)

        f = QFont('Calibri', 24)
        self.setFont(f)

        self.setHtml(text.replace('\n', '<br/>'))
        self.setStyleSheet('''QTextEdit{background-color: #353535; padding: 10px 10px 10px 10px}''')

        QTimer.singleShot(10, self.fit_to_contents)

    def fit_to_contents(self):
        height = self.document().size().height() + 32
        self.setFixedHeight(height)

        effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(effect)

        self.fading_anim = QPropertyAnimation(effect, b'opacity')
        self.fading_anim.setStartValue(0.0)
        self.fading_anim.setEndValue(1.0)
        self.fading_anim.setDuration(1000)
        self.fading_anim.setEasingCurve(QEasingCurve.Type.InOutCubic)

        self.fading_anim.start()


class ChatGPTGUI(QWidget):

    def __init__(self):
        super().__init__()
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.chatgpt_buffer = []

        # Structure
        self.chat_body = QVBoxLayout()
        self.chat_body.setContentsMargins(0, 0, 5, 0)
        self.chat_body.setSizeConstraint(QLayout.SetMinAndMaxSize)

        self.chat_container = QWidget()

        self.body = QVBoxLayout()
        self.body.setSpacing(18)

        self.container = QWidget()

        self.window_body = QVBoxLayout()
        self.window_body.setContentsMargins(0, 0, 0, 0)

        # Components
        self.chat_scroll = QScrollArea()
        self.chat_scroll.setWidgetResizable(True)
        self.chat_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.chat_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.chat_scroll.setStyleSheet('''QScrollArea{background-color: #2a2a2a; border: 6px solid #2a2a2a;}
                                          QWidget{background-color: #2a2a2a; border-radius: 10px;}''')

        self.chat_te = QTextEdit()
        self.chat_te.installEventFilter(self)

        self.thread_pool = QThreadPool()

        # Functionality
        self.chat_scroll.verticalScrollBar().rangeChanged.connect(lambda: self.chat_scroll.verticalScrollBar().setValue(
                                                                          self.chat_scroll.verticalScrollBar().maximum()))

        # Assembly
        self.chat_container.setLayout(self.chat_body)
        self.chat_scroll.setWidget(self.chat_container)

        self.body.addWidget(self.chat_scroll, stretch=4)
        self.body.addWidget(self.chat_te, stretch=1)
        self.container.setLayout(self.body)

        self.window_body.addWidget(CustomWindowFrame(title='ChatGPT MiniGUI', icon='Resources/Icon.jpg', minimizable=False, maximizable=False))
        self.window_body.addWidget(self.container)

        self.setLayout(self.window_body)

        self.no_messages_lb = QLabel(self)
        self.no_messages_lb.setFixedSize(QSize(432, 234))
        self.no_messages_lb.setPixmap(QPixmap('Resources/NoMessages.png'))
        self.no_messages_lb.move(410, 180)
        self.no_messages_lb.show()

        self.chat_te.setFocus()

    def eventFilter(self, watched: QtCore.QObject, event: QtCore.QEvent) -> bool:

        if event.type() == QEvent.KeyPress:
            event = QKeyEvent(event)

            shift = event.modifiers() == Qt.ShiftModifier
            enter = event.key() == Qt.Key_Return

            if not shift and enter:
                self.chat_te.setDisabled(True)

                message = self.chat_te.toPlainText()
                self.chat_body.addWidget(MessageBlock('<b style="color:green">You</b>\n' + message), alignment=Qt.AlignRight)
                self.no_messages_lb.hide()

                loading_lb = QLabel(self)
                loading_lb.move(QPoint(500, 220))
                loading_lb.setFixedSize(200, 200)

                loading_mv = QMovie('Resources/Loading Animations/Loading2.gif')
                loading_mv.start()

                loading_lb.setMovie(loading_mv)
                loading_lb.show()

                tc = self.chat_te.textCursor()
                tc.setPosition(0)
                self.chat_te.setTextCursor(tc)

                self.chat_te.clear()
                self.chat_te.setFocus()

                def thread(signals, message):
                    self.chatgpt_buffer.append({"role": 'user', "content": message})
                    completion = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=self.chatgpt_buffer)

                    response = completion.choices[0].message.content
                    self.chatgpt_buffer.append({"role": "assistant", "content": response})

                    signals.result.emit(response)

                worker = Worker(thread, message)
                worker.result.connect(self.respond)
                worker.result.connect(loading_mv.stop)
                worker.result.connect(loading_lb.hide)

                self.thread_pool.start(worker)
                return True

        return False

    def respond(self, response):
        self.chat_body.addWidget(MessageBlock('<b style="color:red">ChatGPT</b>\n' + response), alignment=Qt.AlignLeft)
        self.chat_te.setDisabled(False)
        self.chat_te.setFocus()


if '__main__' in __name__:

    if not getattr(sys, "frozen", False):
        faulthandler.enable()

    config = read_config()
    openai.api_key = config['API Keys']['OpenAI']

    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor("#353535"))
    palette.setColor(QPalette.ColorRole.Base, QColor("#2a2a2a"))
    palette.setColor(QPalette.ColorRole.Button, QColor("#353535"))

    app = QApplication()
    app.setStyle('Fusion')
    app.setPalette(palette)
    app.setStyleSheet('''QWidget {color: #ffffff; font-size: 24px; font-family: Calibri;}
                         QWidget:!enabled {color: #808080}
                         
                         QTextEdit {border: 6px solid #2a2a2a; border-radius: 10px}
    
                         QScrollBar:vertical {border: none;
                                              background: #2a2a2a;
                                              width: 15px;}
                                            
                         QScrollBar::handle:vertical {background-color: #666565;
                                                      min-height: 30px;
                                                      border-radius: 7px;} 
                         QScrollBar::sub-line:vertical {border: none}
                         QScrollBar::add-line:vertical {border: none}''')

    window = ChatGPTGUI()
    window.resize(QSize(1280, 720))
    window.show()

    app.exec()

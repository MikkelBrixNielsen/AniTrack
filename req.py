import sys
import json
import os
import time
import re
import webbrowser
from urllib.parse import quote
import json
import secrets

import requests
from PyQt5.QtCore import (
    QUrl,
    Qt,
    QPropertyAnimation,
    QThreadPool,
    QRunnable,
    pyqtSignal,
    QObject,
)
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtWidgets import (
    QWidget,
    QLineEdit,
    QApplication,
    QMainWindow,
    QDialog,
    QVBoxLayout,
    QLabel,
    QToolBar,
    QPushButton,
    QStackedWidget,
    QSizePolicy,
    QHBoxLayout,
    QScrollArea,
    QFrame,
    QMessageBox,
    QGraphicsOpacityEffect,
)
from PyQt5.QtWebEngineWidgets import QWebEngineView
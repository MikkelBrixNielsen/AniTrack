import random
import sys
import json
import os
import time
import re
import webbrowser
from urllib.parse import quote

import requests
from main import get_code_verifier, refresh_token, getClientId
from PyQt5.QtCore import QUrl, Qt, QPropertyAnimation, QThreadPool, QRunnable, pyqtSignal, QObject
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


screen_size = None
clientId = None
token = None
mal_folder = None

class AnimeListWidget(QWidget):
    def __init__(self, result):
        super(AnimeListWidget, self).__init__()

        font = QFont()
        font.setPointSize(18)  # Set the size
        font.setBold(True)  # Make it bold
        title = result["alternative_titles"]["en"] if "en" in result["alternative_titles"] and result["alternative_titles"]["en"] else result["title"]
        # Widgets
        title_label = QLabel(title)
        title_label.setFont(font)
        synopsis_label = QLabel(result["synopsis"][:500] + "...")
        synopsis_label.setWordWrap(True)
        synopsis_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        self.image_label = QLabel()

        self.threadpool = QThreadPool()
        image_loader = ImageLoader(result["main_picture"]["medium"])
        image_loader.signals.finished.connect(self.on_image_loaded)
        image_loader.signals.error.connect(self.on_image_error)
        self.threadpool.start(image_loader)


        open_button = QPushButton("Stream Here!")
        open_button.clicked.connect(
            lambda: webbrowser.open("crunchyroll.com/search?q=" + title.replace(" ", "%20"))
        )

        add_button = QPushButton("Browse Merch!")
        add_button.clicked.connect(lambda: webbrowser.open("google.com/search?q=" + title.replace(" ", "+") + "+merchandise"))

        # Layouts
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        main_layout.addWidget(title_label)

        h_layout = QHBoxLayout()
        main_layout.addLayout(h_layout)

        button_layout = QVBoxLayout()
        button_layout.addStretch(1)
        button_layout.addWidget(open_button)
        button_layout.addWidget(add_button)
        button_layout.addStretch(1)

        h_layout.addWidget(self.image_label)
        h_layout.addWidget(synopsis_label)
        h_layout.addLayout(button_layout)

        self.setStyleSheet(
            """
            QDialog {
                background-color: #333;
            }
            QLabel {
                color: #FFF;
                font-size: 16px;
                padding: 15px;
            }
            QPushButton {
                background-color: #007BFF;
                border: none;
                color: white;
                padding: 15px 32px;
                text-align: center;
                text-decoration: none;
                display: inline-block;
                font-size: 16px;
                margin: 4px 2px;
                cursor: pointer;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #0069D9;
            }
            """
        )
    def on_image_loaded(self, image_data):
        pixmap = QPixmap()
        pixmap.loadFromData(image_data)
        self.image_label.setPixmap(pixmap)

    def on_image_error(self, error_message):
        print("Error loading image:", error_message)
        # Handle the error (e.g., display a default image)

    # Method to start loading the image
    def load_image(self):
        image_loader = ImageLoader(self.image_url)
        image_loader.signals.finished.connect(self.on_image_loaded)
        image_loader.signals.error.connect(self.on_image_error)
        self.threadpool.start(image_loader)

class AnimeWidget(QWidget):
    def __init__(self, result):
        super(AnimeWidget, self).__init__()

        font = QFont()
        font.setPointSize(18)  # Set the size
        font.setBold(True)  # Make it bold

        # Widgets
        title_label = QLabel(
            result["alternative_titles"]["en"]
            if "en" in result["alternative_titles"]
            and result["alternative_titles"]["en"]
            else result["title"]
        )
        title_label.setFont(font)
        synopsis_label = QLabel(result["synopsis"][:500] + "...")
        synopsis_label.setWordWrap(True)
        synopsis_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        self.image_label = QLabel()

        self.threadpool = QThreadPool()
        image_loader = ImageLoader(result["main_picture"]["medium"])
        image_loader.signals.finished.connect(self.on_image_loaded)
        image_loader.signals.error.connect(self.on_image_error)
        self.threadpool.start(image_loader)


        open_button = QPushButton("Open in browser")
        open_button.clicked.connect(
            lambda: webbrowser.open(
                "https://myanimelist.net/anime/" + str(result["id"])
            )
        )

        add_button = QPushButton("Add to list")
        add_button.clicked.connect(lambda: add_anime(result["id"]))

        # Layouts
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        main_layout.addWidget(title_label)

        h_layout = QHBoxLayout()
        main_layout.addLayout(h_layout)

        button_layout = QVBoxLayout()
        button_layout.addStretch(1)
        button_layout.addWidget(open_button)
        button_layout.addWidget(add_button)
        button_layout.addStretch(1)

        h_layout.addWidget(self.image_label)
        h_layout.addWidget(synopsis_label)
        h_layout.addLayout(button_layout)

        self.setStyleSheet(
            """
            QDialog {
                background-color: #333;
            }
            QLabel {
                color: #FFF;
                font-size: 16px;
                padding: 15px;
            }
            QPushButton {
                background-color: #007BFF;
                border: none;
                color: white;
                padding: 15px 32px;
                text-align: center;
                text-decoration: none;
                display: inline-block;
                font-size: 16px;
                margin: 4px 2px;
                cursor: pointer;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #0069D9;
            }
            """
        )
    def on_image_loaded(self, image_data):
        pixmap = QPixmap()
        pixmap.loadFromData(image_data)
        self.image_label.setPixmap(pixmap)

    def on_image_error(self, error_message):
        print("Error loading image:", error_message)
        # Handle the error (e.g., display a default image)

    # Method to start loading the image
    def load_image(self):
        image_loader = ImageLoader(self.image_url)
        image_loader.signals.finished.connect(self.on_image_loaded)
        image_loader.signals.error.connect(self.on_image_error)
        self.threadpool.start(image_loader)

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.token_init()

        # Create the navigation bar
        self.nav_bar = QToolBar("Navigation")
        self.addToolBar(self.nav_bar)
        self.nav_bar.setMovable(False)

        nav_widget = QWidget()
        nav_layout = QHBoxLayout()
        nav_widget.setLayout(nav_layout)
        nav_layout.addStretch()

        # Add buttons to the navigation bar
        search_button = QPushButton("Search", nav_widget)
        anime_list_button = QPushButton("My Anime List", nav_widget)
        nav_layout.addWidget(search_button)
        nav_layout.addWidget(anime_list_button)

        nav_layout.addStretch()

        self.nav_bar.addWidget(nav_widget)

        # Initialize QStackedWidget
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        self.search_interface = SearchInterface()
        self.anime_list_interface = AnimeListInterface()

        self.stacked_widget.addWidget(self.search_interface)
        self.stacked_widget.addWidget(self.anime_list_interface)

        search_button.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        anime_list_button.clicked.connect(self.show_and_update_anime_list)

        

        self.window_size = (
            int(screen_size.width() * 0.35),
            int(screen_size.height() * 0.90),
        )
        self.window_position = (
            int((screen_size.width() - self.window_size[0]) * 0.5),
            int((screen_size.height() - self.window_size[1]) * 0.5),
        )
        self.setGeometry(
            self.window_position[0],
            self.window_position[1],
            self.window_size[0],
            self.window_size[1],
        )
        self.setWindowTitle("AniTrack")

        self.setStyleSheet(
            """
            QWidget, QScrollArea {
                background-color: #333;
            }
            QLabel, QLineEdit {
                color: #FFF;
                font-size: 16px;
                padding: 15px;
            }
            QPushButton {
                background-color: #808080;
                border: none;
                color: white;
                padding: 15px;
                text-align: center;
                text-decoration: none;
                display: inline-block;
                font-size: 16px;
                margin: 4px 2px;
                cursor: pointer;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #707070;
            }
            """
        )

        self.initUI()
    
    def show_and_update_anime_list(self):
        # Switch to the AnimeListInterface
        self.stacked_widget.setCurrentWidget(self.anime_list_interface)

        # Update the anime list
        self.update_anime_list()

    def update_anime_list(self):
        anime_list = get_mylist()  # Call your backend function to fetch the list
        self.anime_list_interface.display_anime_list(anime_list)


    def token_init(self):
        global clientId
        global token
        global mal_folder

        clientId = getClientId()
        home = os.path.expanduser("~")

        if os.name == "nt":  # Windows
            mal_folder = os.path.join(home, "MAL")
        else:  # other platforms
            mal_folder = os.path.join(home, ".config", "MAL")

        try:
            os.makedirs(mal_folder, exist_ok=True)
        except Exception as e:
            print("Error creating directories:", e)

        try:
            with open(os.path.join(mal_folder, "token.json"), "r") as file:
                token = json.load(file)
                print("Token loaded from file.")
                if self.is_token_expired():
                    print("Token is expired, trying refresh")
                    token = refresh_token()
        except json.JSONDecodeError:
            print("File is corrupted. Deleting file and getting new token.")
            os.remove(os.path.join(mal_folder, "token.json"))
            self.open_auth_window()
        except FileNotFoundError:
            print("Token file not found - Starting authentication process...")
            self.open_auth_window()
        except Exception as e:
            print("Error", e)
            print("Deleting file and getting new token.")
            os.remove(os.path.join(mal_folder, "token.json"))
            self.open_auth_window()

    def is_token_expired(self):
        global token
        return token["expiration_time"] - int(time.time()) < 1209600

    def open_auth_window(self):
        self.auth_window = AuthWindow()
        self.auth_window.show()

    def initUI(self):
        pass


class AnimeListInterface(QWidget):
    def __init__(self, parent=None):
        super(AnimeListInterface, self).__init__(parent)

        # Initialize the scroll area for displaying anime list
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)

        # Initialize a widget and a layout for the scroll area
        self.scroll_widget = QWidget()
        self.scroll_area.setWidget(self.scroll_widget)
        self.layout = QVBoxLayout()
        self.scroll_widget.setLayout(self.layout)
        # Set up the layout for this widget
        self.main_layout = QVBoxLayout(self)
        self.main_layout.addWidget(self.scroll_area)

    def display_anime_list(self, anime_list):
        # Clear the layout first
        for i in reversed(range(self.layout.count())):
            widget_to_remove = self.layout.itemAt(i).widget()
            if widget_to_remove:
                widget_to_remove.setParent(None)

        # Add an AnimeWidget for each anime in the list
        for anime in anime_list:
            try:
                anime_widget = AnimeListWidget(anime)
                self.layout.addWidget(anime_widget)
                self.layout.addWidget(horizontal_line())
                self.layout.update()
            except Exception as e:
                print("Error creating anime widget:", e)

class SearchInterface(QWidget):
    def __init__(self, parent=None):
        super(SearchInterface, self).__init__(parent)

        self.search_box = QLineEdit()
        self.search_box.returnPressed.connect(self.search)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)

        # Initialize a widget and a layout for the scroll area
        self.scroll_widget = QWidget()
        self.scroll_area.setWidget(self.scroll_widget)
        self.layout = QVBoxLayout()
        self.scroll_widget.setLayout(self.layout)

        self.main_layout = QVBoxLayout(self)
        #self.setCentralWidget(self.central_widget)

        self.toast_message = QLabel()
        self.toast_message.setStyleSheet("background-color: #333; color: #FFF;")
        self.toast_message.hide()  # Initially hidden

        self.toast_message_opacity = QGraphicsOpacityEffect(self.toast_message)
        self.toast_message.setGraphicsEffect(self.toast_message_opacity)

        self.toast_message_animation = QPropertyAnimation(
            self.toast_message_opacity, b"opacity"
        )

        self.main_layout.addWidget(self.search_box)
        self.main_layout.addWidget(self.scroll_area)
        self.main_layout.addWidget(self.toast_message)

    
    def display_toast_message(self, message, duration=3000):
        # Show the message and then hide it after 'duration' milliseconds
        self.toast_message.setText(message)
        self.toast_message.show()
        self.toast_message_animation.setDuration(duration)
        self.toast_message_animation.setStartValue(1.0)  # Fully opaque
        self.toast_message_animation.setEndValue(0.0)  # Fully transparent
        self.toast_message_animation.start()

    def add_anime_success(self, id_):
        self.display_toast_message(f"Anime with ID {id_} successfully added!")

    def search(self):
        query = self.search_box.text()
        results = self.search_mal(query)
        self.display_results(results)

    def search_mal(self, query):
        query = quote(query)
        url = f"https://api.myanimelist.net/v2/anime?q={query}&limit=10&fields=id,title,mean,main_picture,alternative_titles,popularity,synopsis&nsfw=true"
        headers = {
            "X-MAL-CLIENT-ID": clientId,
            "Content-Type": "application/x-www-form-urlencoded",
        }
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            reply = response.json()
            search_results = sorted(
                reply["data"], key=lambda x: x["node"]["popularity"]
            )
            indexed_nodes = []
            for i, item in enumerate(search_results, start=1):
                node_dict = {
                    "id": item["node"]["id"] if "id" in item["node"] else None,
                    "title": item["node"]["title"] if "title" in item["node"] else None,
                    "main_picture": item["node"]["main_picture"]
                    if "main_picture" in item["node"]
                    else None,
                    "alternative_titles": item["node"]["alternative_titles"]
                    if "alternative_titles" in item["node"]
                    else None,
                    "popularity": item["node"]["popularity"]
                    if "popularity" in item["node"]
                    else None,
                    "synopsis": item["node"]["synopsis"]
                    if "synopsis" in item["node"]
                    else None,
                    "mean": item["node"]["mean"] if "mean" in item["node"] else None,
                }

                indexed_nodes.append(node_dict)
            return indexed_nodes
        except requests.exceptions.RequestException as e:
            print("HTTP search error: ", e)
            return []

    def display_results(self, results):
        # Clear the layout first
        for i in reversed(range(self.layout.count())):
            self.layout.itemAt(i).widget().setParent(None)

        # Add an AnimeWidget for each result
        for result in results:
            anime_widget = AnimeWidget(result)
            self.layout.addWidget(anime_widget)
            self.layout.addWidget(horizontal_line())



class AuthWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.confirm_close = True
        self.setWindowTitle("Please Authenticate")
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)

        self.setStyleSheet(
            """
            QDialog {
                background-color: #333;
            }
            QLabel {
                color: #FFF;
                font-size: 16px;
                padding: 15px;
            }
            QPushButton {
                background-color: #007BFF;
                border: none;
                color: white;
                padding: 15px 32px;
                text-align: center;
                text-decoration: none;
                display: inline-block;
                font-size: 16px;
                margin: 4px 2px;
                cursor: pointer;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #0069D9;
            }
            """
        )

        self.instruction_label = QLabel(
            "Click the button below to authenticate with MyAnimeList."
        )
        self.auth_button = QPushButton("Authenticate")
        self.auth_button.clicked.connect(self.open_browser)
        self.quit_button = QPushButton("Quit")
        self.quit_button.clicked.connect(QApplication.instance().quit)

        layout = QVBoxLayout()
        layout.addWidget(self.instruction_label)
        layout.addWidget(self.auth_button)
        layout.addWidget(self.quit_button)
        self.setLayout(layout)

    def closeEvent(self, event):
        if self.confirm_close:
            reply = QMessageBox.question(
                self,
                "Confirm Exit",
                "Are you sure you want to exit the application?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )

            if reply == QMessageBox.Yes:
                QApplication.quit()
            else:
                event.ignore()  # Ignore the close event
        else:
            event.accept()

    def quit_without_confirmation(self):
        self.confirm_close = False  # Don't show confirmation
        self.close()  # Close the window

    def open_browser(self):
        self.code_verifier = get_code_verifier()
        url = f"https://myanimelist.net/v1/oauth2/authorize?response_type=code&client_id={clientId}&code_challenge={self.code_verifier}&state=RequestID"

        self.browser = BrowserWindow(url, self.code_verifier)
        self.browser.show()
        self.quit_without_confirmation()


class BrowserWindow(QWebEngineView):
    def __init__(self, url, code_verifier):
        super().__init__()
        self.confirm_close = True
        self.setWindowTitle("Please Authenticate")
        self.setFixedSize(600, 800)
        self.code_verifier = code_verifier
        self.load(QUrl(url))
        self.urlChanged.connect(self.on_url_changed)

    def on_url_changed(self, url):
        match = re.search(r"code=(.*?)&state=RequestID", url.toString())
        if match:
            code = match.group(1)
            self.getToken(code, self.code_verifier)
            self.quit_without_confirmation()

    def getToken(self, code, code_verifier):
        global mal_folder
        global token
        data = {
            "client_id": clientId,
            "code": code,
            "code_verifier": code_verifier,
            "grant_type": "authorization_code",
        }
        try:
            response = requests.post(
                "https://myanimelist.net/v1/oauth2/token", data=data
            )
            response.raise_for_status()
            token_data = json.loads(response.text)
            self.save_token(token_data)
            token = token_data
        except requests.exceptions.RequestException as e:
            print("Token http request error:", e)

    def save_token(self, token_data):
        token_data["expiration_time"] = int(time.time()) + token_data["expires_in"]
        with open(os.path.join(mal_folder, "token.json"), "w") as file:
            json.dump(token_data, file)

    def closeEvent(self, event):
        if self.confirm_close:
            reply = QMessageBox.question(
                self,
                "Confirm Exit",
                "Are you sure you want to exit the application?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )

            if reply == QMessageBox.Yes:
                QApplication.quit()
            else:
                event.ignore()  # Ignore the close event
        else:
            event.accept()

    def quit_without_confirmation(self):
        self.confirm_close = False  # Don't show confirmation
        self.close()  # Close the window

class ImageLoader(QRunnable):
    def __init__(self, url):
        super().__init__()
        self.url = url
        self.signals = ImageLoaderSignals()

    def run(self):
        try:
            response = requests.get(self.url)
            response.raise_for_status()
            self.signals.finished.emit(response.content)
        except Exception as e:
            self.signals.error.emit(str(e))

class ImageLoaderSignals(QObject):
    finished = pyqtSignal(bytes)
    error = pyqtSignal(str)

def get_mylist():
    url = "https://api.myanimelist.net/v2/users/@me/animelist?limit=500&fields=id,title,mean,main_picture,alternative_titles,popularity,synopsis&nsfw=true"
    headers = {"Authorization": f'Bearer {token["access_token"]}'}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        reply = response.json()

        anime_list = reply.get('data', [])
        random.shuffle(anime_list)
        indexed_nodes = []
        for i, item in enumerate(anime_list[:10], start=1):
            node_dict = {
                "id": item["node"]["id"] if "id" in item["node"] else None,
                "title": item["node"]["title"] if "title" in item["node"] else None,
                "main_picture": item["node"]["main_picture"]
                if "main_picture" in item["node"]
                else None,
                "alternative_titles": item["node"]["alternative_titles"]
                if "alternative_titles" in item["node"]
                else None,
                "popularity": item["node"]["popularity"]
                if "popularity" in item["node"]
                else None,
                "synopsis": item["node"]["synopsis"]
                if "synopsis" in item["node"]
                else None,
                "mean": item["node"]["mean"] if "mean" in item["node"] else None,
            }

            indexed_nodes.append(node_dict)
        return indexed_nodes
    except requests.exceptions.RequestException as e:
        print("HTTP search error: ", e)
        return []

def add_anime(id_):
    global window
    url = f"https://api.myanimelist.net/v2/anime/{id_}/my_list_status"
    data = {"status": "plan_to_watch"}
    headers = {"Authorization": f'Bearer {token["access_token"]}'}
    try:
        response = requests.put(url, data=data, headers=headers)
        response.raise_for_status()
        print(f"HTTP response code: {response.status_code}")  # Print HTTP response code
        print(
            f"Anime with ID {id_} successfully added to 'plan to watch' list."
        )  # Confirmation message
        window.add_anime_success(id_)
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
    except requests.exceptions.HTTPError as e:
        print(f"HTTP error occurred: {e}")
    except requests.exceptions.ConnectionError as e:
        print(f"Error connecting to the server: {e}")
    except requests.exceptions.Timeout as e:
        print(f"Timeout error occurred: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


def horizontal_line():
    line = QFrame()
    line.setFrameShape(QFrame.HLine)
    line.setFrameShadow(QFrame.Sunken)
    line.setFixedHeight(1)
    line.setStyleSheet("background-color: #003e80;")
    return line


def window():
    global screen_size
    global window
    app = QApplication(sys.argv + ["--no-sandbox"])
    screen_size = app.primaryScreen().size()
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


def main():
    window()


if __name__ == "__main__":
    main()

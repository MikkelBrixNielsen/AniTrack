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


screen_size = None
clientId = None
token = None
mal_folder = None

class ListWidget(QWidget):
    def __init__(self, result):
        super(ListWidget, self).__init__()

        font = QFont()
        font.setPointSize(18)  # Set the size
        font.setBold(True)  # Make it bold
        title = (
            result["alternative_titles"]["en"]
            if "en" in result["alternative_titles"]
            and result["alternative_titles"]["en"]
            else result["title"]
        ) + " - ("+ result["status"].replace("_", " ") +")"
        # Widgets
        title_label = QLabel(title)
        title_label.setFont(font)
        rating_label = QLabel("⭐ Rating: " + str(result["mean"]))
        rating_label.setFont(font)

        synopsis_label = QLabel(result["synopsis"][:500] + "...")
        synopsis_label.setWordWrap(True)
        synopsis_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        self.image_label = QLabel()

        self.threadpool = QThreadPool()
        image_loader = ImageLoader(result["main_picture"]["medium"])
        image_loader.signals.finished.connect(self.on_image_loaded)
        image_loader.signals.error.connect(self.on_image_error)
        self.threadpool.start(image_loader)

        open_button = QPushButton("View Here!")
        open_button.clicked.connect(
            lambda: webbrowser.open(
                "crunchyroll.com/search?q=" + title.replace(" ", "%20")
            )
        )

        add_button = QPushButton("Browse Merch!")
        add_button.clicked.connect(
            lambda: webbrowser.open(
                "google.com/search?q=" + title.replace(" ", "+") + "+merchandise"
            )
        )

        # Layouts
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        labels_layout = QHBoxLayout()
        # Add labels to the sub-layout
        labels_layout.addWidget(title_label)
        if str(result["mean"]) != "None":
            labels_layout.addStretch(1)  # Add stretchable space between labels
            labels_layout.addWidget(rating_label)

        # Add the sub-layout to the main layout
        main_layout.addLayout(labels_layout)

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


class Widget(QWidget):
    def __init__(self, caller, result, contentType):
        super(Widget, self).__init__()

        font = QFont()
        font.setPointSize(18)  # Set the size
        font.setBold(True)  # Make it bold

        # Widgets
        title = (result["alternative_titles"]["en"] 
                 if "en" in result["alternative_titles"] 
                 and result["alternative_titles"]["en"] 
                 else result["title"])
        title_label = QLabel(title)
        title_label.setFont(font)

        rating_label = QLabel("⭐ Rating: " + str(result["mean"]))
        rating_label.setFont(font)

        synopsis_label = QLabel(result["synopsis"][:500] + "...")
        synopsis_label.setWordWrap(True)
        synopsis_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        self.image_label = QLabel()

        self.threadpool = QThreadPool()
        image_loader = ImageLoader(result["main_picture"]["medium"])
        image_loader.signals.finished.connect(self.on_image_loaded)
        image_loader.signals.error.connect(self.on_image_error)
        self.threadpool.start(image_loader)

        self.contentType = quote(contentType)
        open_button = QPushButton("Open in browser")
        open_button.clicked.connect(
            lambda: webbrowser.open(
                "https://myanimelist.net/"+self.contentType+"/"+str(result["id"])
            )
        )

        add_button = QPushButton("Add to list")
        add_button.clicked.connect(lambda: caller.add_content(result["id"], self.contentType))

        # Layouts
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)


        labels_layout = QHBoxLayout()
        # Add labels to the sub-layout
        labels_layout.addWidget(title_label)
        
        if str(result["mean"]) != "None":
            labels_layout.addStretch(1)  # Add stretchable space between labels
            labels_layout.addWidget(rating_label)

        # Add the sub-layout to the main layout
        main_layout.addLayout(labels_layout)


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
        home_button = QPushButton("Home", nav_widget)
        search_anime_button = QPushButton("Search Anime", nav_widget)
        search_manga_button = QPushButton("Search Manga", nav_widget)
        anime_list_button = QPushButton("Anime List", nav_widget)
        manga_list_button = QPushButton("Manga List", nav_widget)

        nav_layout.addWidget(home_button)
        nav_layout.addWidget(search_anime_button)
        nav_layout.addWidget(search_manga_button)
        nav_layout.addWidget(anime_list_button)
        nav_layout.addWidget(manga_list_button)
        nav_layout.addStretch()
        self.nav_bar.addWidget(nav_widget)

        # Initialize QStackedWidget
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        self.home_interface = HomeInterface()
        self.search_anime_interface = SearchAnimeInterface()
        self.search_manga_interface = SearchMangaInterface()
        self.anime_list_interface = ListInterface()
        self.manga_list_interface = ListInterface()

        self.stacked_widget.addWidget(self.home_interface)
        self.stacked_widget.addWidget(self.search_anime_interface)
        self.stacked_widget.addWidget(self.search_manga_interface)
        self.stacked_widget.addWidget(self.anime_list_interface)
        self.stacked_widget.addWidget(self.manga_list_interface)

        home_button.clicked.connect(self.goto_home)
        search_anime_button.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(1))
        search_manga_button.clicked.connect(self.goto_manga_search)
        anime_list_button.clicked.connect(self.show_and_update_anime_list)
        manga_list_button.clicked.connect(self.show_and_update_manga_list)

        self.window_size = (
            int(screen_size.width() * 0.40),
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

    def goto_home(self):
        # Switch to the homeInterface
        self.stacked_widget.setCurrentWidget(self.home_interface)
        self.home_interface.load_image()

    def goto_manga_search(self):
        # Switch to the SearchMangaInterface
        self.stacked_widget.setCurrentWidget(self.search_manga_interface)

    def show_and_update_anime_list(self):
        # Switch to the ListInterface
        self.stacked_widget.setCurrentWidget(self.anime_list_interface)

        # Update the anime list
        self.update_list("anime")

    def show_and_update_manga_list(self):
        # Switch to the ListInterface
        self.stacked_widget.setCurrentWidget(self.manga_list_interface)

        # Update the manga list
        self.update_list("manga")
        
    def update_list(self, contentType):
        list = get_mylist(contentType)  # Call your backend function to fetch the list
        getattr(self, contentType+"_list_interface").display_list(list)

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

class ListInterface(QWidget):
    def __init__(self, parent=None):
        super(ListInterface, self).__init__(parent)

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

    def display_list(self, list):
        # Clear the layout first
        for i in reversed(range(self.layout.count())):
            widget_to_remove = self.layout.itemAt(i).widget()
            if widget_to_remove:
                widget_to_remove.setParent(None)

        # Add an Widget for each anime in the list
        for item in list:
            try:
                widget = ListWidget(item)
                self.layout.addWidget(widget)
                self.layout.addWidget(horizontal_line())
                self.layout.update()
            except Exception as e:
                print("Error creating anime widget:", e)


class SearchInterface(QWidget):
    def __init__(self, parent=None):
        super(SearchInterface, self).__init__(parent)

        self.search_box = QLineEdit()
        self.setPlaceholderText(self)
        self.search_box.returnPressed.connect(self.search)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)

        # Initialize a widget and a layout for the scroll area
        self.scroll_widget = QWidget()
        self.scroll_area.setWidget(self.scroll_widget)
        self.layout = QVBoxLayout()
        self.scroll_widget.setLayout(self.layout)

        self.main_layout = QVBoxLayout(self)

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

    def add_content_success(self, id_, contentType):
        self.display_toast_message(contentType+f" with ID {id_} successfully added!")

    def add_content(self, id_, contentType):
        status = "plan_to_watch" if contentType == "anime" else "plan_to_read"
        url = f"https://api.myanimelist.net/v2/{contentType}/{id_}/my_list_status"
        data = {"status": status}
        headers = {"Authorization": f'Bearer {token["access_token"]}'}
        try:
            response = requests.put(url, data=data, headers=headers)
            response.raise_for_status()
            print(f"HTTP response code: {response.status_code}")  # Print HTTP response code
            print(
                f"{contentType} with ID {id_} successfully added to '"+status+"' list."
            )  # Confirmation message
            self.add_content_success(id_, contentType)
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

    def search():
        # MUST be implemented in each interface that inherits this one
        pass

    def search_mal(self, query, contentType):
        contentType = quote(contentType)
        query = quote(query)
        url = f"https://api.myanimelist.net/v2/{contentType}?q={query}&limit=100&fields=id,title,mean,main_picture,alternative_titles,popularity,synopsis&nsfw=true"
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
            for i, item in enumerate(search_results[:15], start=1):
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
    
    def display_results(self, results, contentType):
        # Clear the layout first
        for i in reversed(range(self.layout.count())):
            self.layout.itemAt(i).widget().setParent(None)

        # Add a Widget for each result
        for result in results:
            widget = Widget(self, result, contentType)
            self.layout.addWidget(widget)
            self.layout.addWidget(horizontal_line())

class SearchAnimeInterface(SearchInterface):
    def search(self):
        results = self.search_mal(self.search_box.text(), "anime")
        self.display_results(results, "anime")
    
    def setPlaceholderText(self, caller):
        caller.search_box.setPlaceholderText("Search for anime here...")
    

class SearchMangaInterface(SearchInterface):
    def search(self):
        results = self.search_mal(self.search_box.text(), "manga")
        self.display_results(results, "manga")
        
    def setPlaceholderText(self, caller):
        caller.search_box.setPlaceholderText("Search for manga here...")


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

class HomeInterface(QWidget):
    def __init__(self, parent=None):
        super(HomeInterface, self).__init__(parent)
        self.main_layout = QVBoxLayout(self)

        # Create a QLabel to display the image
        self.image_label = QLabel(self)
        self.load_image()

        # Main layout
        self.main_layout.addWidget(self.image_label)

    def load_image(self, path="OPPERTUN.png"):
        # Load and display the image in the QLabel
        pixmap = QPixmap(path)
        pixmap = pixmap.scaled(2331//3, 3454//3)  # Resize the image while maintaining the aspect ratio
        self.image_label.setPixmap(pixmap)
        self.image_label.setScaledContents(True)



def get_mylist(contentType):
    contentType = quote(contentType)
    url = f"https://api.myanimelist.net/v2/users/@me/{contentType}list?limit=500&fields=id,title,mean,main_picture,alternative_titles,popularity,synopsis,my_list_status&nsfw=true"
    headers = {"Authorization": f'Bearer {token["access_token"]}'}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        reply = response.json()
        list = reply.get("data", [])
        indexed_nodes = []
        for i, item in enumerate(list[:15], start=1):
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
                "status": item["node"]["my_list_status"]["status"]
            }

            indexed_nodes.append(node_dict)
        return indexed_nodes
    except requests.exceptions.RequestException as e:
        print("HTTP search error: ", e)
        return []

def refresh_token():
    data = {
        "client_id": clientId,
        "grant_type": "refresh_token",
        "refresh_token": token["refresh_token"],
    }
    try:
        response = requests.post("https://myanimelist.net/v1/oauth2/token", data=data)
        response.raise_for_status()
        token_data = json.loads(response.text)
        save_token(token_data)
        print("Token refreshed")
        return token_data
    except requests.exceptions.RequestException as e:
        print("Token refresh error:", e)
        print("Trying new authentication")
        authenticator()

def getClientId():
    try:
        response = requests.get(
            "https://suiz.org/api/mal?client=MALadder", headers={"Client": "MALadder"}
        )
        response.raise_for_status()
        reply = json.loads(response.text)
        return reply["clientId"]
    except requests.exceptions.RequestException as e:
        print("HTTP request error: ", e)

def get_code_verifier() -> str:
    token = secrets.token_urlsafe(100)
    return token[:128]

def getToken(code, code_verifier):
    global mal_folder
    data = {
        "client_id": clientId,
        "code": code,
        "code_verifier": code_verifier,
        "grant_type": "authorization_code",
    }
    try:
        response = requests.post("https://myanimelist.net/v1/oauth2/token", data=data)
        response.raise_for_status()
        token_data = json.loads(response.text)
        save_token(token_data)
        return token_data
    except requests.exceptions.RequestException as e:
        print("Token http request error:", e)

def save_token(token_data):
    token_data["expiration_time"] = int(time.time()) + token_data["expires_in"]
    with open(os.path.join(mal_folder, "token.json"), "w") as file:
        json.dump(token_data, file)

def authenticator():
    code_verifier = code_challenge = get_code_verifier()
    print(
        "Go to the following URL to authorize the application: \n https://myanimelist.net/v1/oauth2/authorize?response_type=code&client_id="
        + clientId
        + "&code_challenge="
        + code_challenge
        + "&state=RequestID"
    )
    while True:
        code = input("Paste in the URL you are redirected to here: ")
        match = re.search(r"code=(.*?)&state=RequestID", code)
        if match:
            return getToken(match.group(1), code_verifier)
        else:
            print("Not valid, please try again.")

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
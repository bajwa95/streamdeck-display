from StreamDeck.DeviceManager import DeviceManager
import time
from StreamDeck.DeviceManager import DeviceManager
import time
import os
import threading
from PyQt5.QtWidgets import QApplication, QLabel
from PyQt5.QtGui import QMovie
from PyQt5.QtCore import Qt, QObject, pyqtSignal, QTimer
from PIL import Image, ImageDraw
from StreamDeck.ImageHelpers import PILHelper
qt_app = QApplication([])
decks = DeviceManager().enumerate()

if not decks:
    print("No Stream Deck found.")
    raise SystemExit

deck = decks[0]
MEDIA_FOLDER = os.path.expanduser("~/streamdeck-display/media")
SUPPORTED_MEDIA = (".gif", ".jpg", ".jpeg", ".png")

files = []

for filename in os.listdir(MEDIA_FOLDER):
    if filename.lower().endswith(SUPPORTED_MEDIA):
        files.append(filename)

files.sort()
files = files[:15]

MEDIA = {}

for key, filename in enumerate(files):
    MEDIA[key] = os.path.join(MEDIA_FOLDER, filename)

main_key = 0
press_times = {}
player = None
return_timer = None

SHORT_DISPLAY_TIME = 3
LONG_PRESS_TIME = 1.5
#print("Connected:", deck.get_serial_number())
print("Number of buttons:", deck.key_count())

class MediaDisplay(QObject):
    change_media = pyqtSignal(str)

    def __init__(self):
        super().__init__()

        self.label = QLabel()
        self.label.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint
        )

        self.label.setStyleSheet("background-color: black;")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.showFullScreen()

        self.movie = None

        self.change_media.connect(self.show_media)

    def show_media(self, filename):
        if self.movie:
            self.movie.stop()
            self.movie.deleteLater()
        self.movie = QMovie(filename)
        screen = QApplication.primaryScreen().geometry()
        self.movie.setScaledSize(screen.size())
        self.label.setGeometry(screen)
        self.label.setMovie(self.movie)
        self.movie.start()

deck.open()
deck.reset()

display = MediaDisplay()
def reload_media():
    global MEDIA, main_key

    files = []

    for filename in os.listdir(MEDIA_FOLDER):
        if filename.lower().endswith(SUPPORTED_MEDIA):
            files.append(filename)

    files.sort()
    files = files[:15]

    MEDIA = {}

    for key, filename in enumerate(files):
        MEDIA[key] = os.path.join(MEDIA_FOLDER, filename)

    # If current main no longer exists
    if main_key not in MEDIA:
        main_key = 0

    print("Media folder refreshed")

    refresh_thumbnails()
def set_button_thumbnail(deck, key, media_file):
    try:
        # Open GIF/image and use its first frame
        image = Image.open(media_file)
        image.seek(0)
        image = image.convert("RGB")

        # Create image at correct Stream Deck button size
        button_image = PILHelper.create_scaled_image(
            deck,
            image,
            margins=[0, 0, 0, 0]
        )
        # Highlight the current MAIN button
        if key == main_key:
            draw = ImageDraw.Draw(button_image)

            width, height = button_image.size
            border = 5

            draw.rectangle(
                [0, 0, width - 1, height - 1],
                outline="yellow",
                width=border
            )

            

        # Send it to the physical button
        deck.set_key_image(
            key,
            PILHelper.to_native_format(deck, button_image)
        )

    except Exception as e:
        print(f"Thumbnail error for Button {key + 1}: {e}")
def refresh_thumbnails():
    for key, media_file in MEDIA.items():
        set_button_thumbnail(deck, key, media_file)
def play_media(key):
    media_file = MEDIA.get(key)

    if not media_file:
        return

    display.change_media.emit(media_file)
def return_to_main():
    global return_timer
    return_timer = None
    play_media(main_key)
def button_pressed(deck, key, state):
    global main_key, return_timer

    # Ignore buttons that don't have media assigned
    if key not in MEDIA:
        return

    # Button pressed down
    if state:
        press_times[key] = time.time()
        return

    # Button released
    if key not in press_times:
        return

    duration = time.time() - press_times.pop(key)

    # Cancel previous return timer
    if return_timer:
        return_timer.cancel()
        return_timer = None

    # LONG PRESS
    if duration >= LONG_PRESS_TIME:
        main_key = key

        print(f"Button {key + 1} is now MAIN")

        play_media(main_key)
        refresh_thumbnails()

    # SHORT PRESS
    else:
        print(f"Button {key + 1} temporary")

        play_media(key)

        return_timer = threading.Timer(
            SHORT_DISPLAY_TIME,
            return_to_main
        )
        return_timer.start()

for key, media_file in MEDIA.items():
    set_button_thumbnail(deck, key, media_file)
deck.set_key_callback(button_pressed)
play_media(main_key)
last_media_state = None


def check_media_folder():
    global last_media_state

    current_state = tuple(
        sorted(
            (
                filename,
                os.path.getmtime(os.path.join(MEDIA_FOLDER, filename))
            )
            for filename in os.listdir(MEDIA_FOLDER)
            if filename.lower().endswith(SUPPORTED_MEDIA)
        )
    )

    if last_media_state is None:
        last_media_state = current_state
        return

    if current_state != last_media_state:
        last_media_state = current_state
        reload_media()


media_timer = QTimer()
media_timer.timeout.connect(check_media_folder)
media_timer.start(2000)
last_media_state = None


def check_media_folder():
    global last_media_state

    current_state = tuple(
        sorted(
            (
                filename,
                os.path.getmtime(os.path.join(MEDIA_FOLDER, filename))
            )
            for filename in os.listdir(MEDIA_FOLDER)
            if filename.lower().endswith(SUPPORTED_MEDIA)
        )
    )

    if last_media_state is None:
        last_media_state = current_state
        return

    if current_state != last_media_state:
        last_media_state = current_state
        reload_media()


media_timer = QTimer()
media_timer.timeout.connect(check_media_folder)
media_timer.start(2000)
print("Press Stream Deck buttons. Ctrl+C to exit.")

try:
    qt_app.exec_()

except KeyboardInterrupt:
    print("\nStopping...")

finally:
    deck.close()

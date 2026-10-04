from StreamDeck.DeviceManager import DeviceManager
import time
from StreamDeck.DeviceManager import DeviceManager
import time
import os
import threading
from PyQt5.QtWidgets import QApplication, QLabel
from PyQt5.QtGui import QMovie, QPixmap
from PyQt5.QtCore import Qt, QObject, pyqtSignal, QTimer
from PIL import Image, ImageDraw
from StreamDeck.ImageHelpers import PILHelper
import subprocess
import qrcode
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
files = files[:14]

MEDIA = {}

for key, filename in enumerate(files):
    MEDIA[key] = os.path.join(MEDIA_FOLDER, filename)

main_key = 0
press_times = {}
player = None
return_timer = None

SHORT_DISPLAY_TIME = 3
LONG_PRESS_TIME = 1.5
NETWORK_KEY = 14   # Stream Deck Button 15 (bottom-right)
#print("Connected:", deck.get_serial_number())
print("Number of buttons:", deck.key_count())

class MediaDisplay(QObject):
    change_media = pyqtSignal(str)
    show_qr_signal = pyqtSignal(str)
    show_hotspot_qr_signal = pyqtSignal(str)
    def __init__(self):
        super().__init__()

        self.label = QLabel()
        self.label.setWindowFlags(
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
        )

        self.label.setStyleSheet("background-color: black;")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.showFullScreen()

        self.movie = None

        self.change_media.connect(self.show_media)
        self.show_qr_signal.connect(self.show_qr)
        self.show_hotspot_qr_signal.connect(self.show_hotspot_qr)
    def show_hotspot_qr(self, url):
        if self.movie:
            self.movie.stop()
            self.movie = None

        qr = qrcode.make(url)
        qr_path = "/tmp/rearwave_hotspot_qr.png"
        qr.save(qr_path)

        screen = QApplication.primaryScreen().geometry()

        html = f"""
        <div style="color:white; text-align:center;">
            <h1>RearWave Hotspot</h1>

            <p style="font-size:28px;">
                1. Connect your phone to Wi-Fi
            </p>

            <p style="font-size:38px;">
                <b>RearWave</b>
            </p>

            <p style="font-size:28px;">
                2. Once connected, scan the QR code
            </p>

            <img src="{qr_path}" width="350" height="350">

            <p style="font-size:24px;">
                {url}
            </p>
        </div>
        """

        self.label.setMovie(None)
        self.label.setPixmap(QPixmap())
        self.label.setText(html)
        self.label.setGeometry(screen)
        self.label.setAlignment(Qt.AlignCenter)

        print(f"Hotspot QR displayed: {url}")
    def show_qr(self, url):
        if self.movie:
            self.movie.stop()
            self.movie = None
        qr = qrcode.make(url)
        qr_path = "/tmp/rearwave_qr.png"
        qr.save(qr_path)

        pixmap = QPixmap(qr_path)

        screen = QApplication.primaryScreen().geometry()

        qr_size = min(screen.width(), screen.height()) - 100

        pixmap = pixmap.scaled(
            qr_size,
            qr_size,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )

        self.label.setMovie(None)
        self.label.setPixmap(pixmap)
        self.label.setGeometry(screen)
        self.label.setAlignment(Qt.AlignCenter)

        print(f"QR displayed: {url}")
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
    files = files[:14]

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
def set_network_button(deck):
    image = Image.new("RGB", (100, 100), "black")
    draw = ImageDraw.Draw(image)

    draw.rectangle([3, 3, 96, 96], outline="white", width=3)

    draw.text(
        (50, 38),
        "NET",
        fill="white",
        anchor="mm"
    )

    draw.text(
        (50, 63),
        "QR",
        fill="white",
        anchor="mm"
    )

    button_image = PILHelper.create_scaled_image(
        deck,
        image,
        margins=[0, 0, 0, 0]
    )

    deck.set_key_image(
        NETWORK_KEY,
        PILHelper.to_native_format(deck, button_image)
    )
def refresh_thumbnails():
    for key, media_file in MEDIA.items():
        set_button_thumbnail(deck, key, media_file)
    set_network_button(deck)
def play_media(key):
    media_file = MEDIA.get(key)

    if not media_file:
        return

    display.change_media.emit(media_file)
def return_to_main():
    global return_timer
    return_timer = None
    play_media(main_key)
def network_button_pressed():
    try:
        connection = subprocess.check_output(
            [
                "nmcli", "-t",
                "-f", "GENERAL.CONNECTION",
                "device", "show", "wlan0"
            ],
            text=True
        ).strip()

        connection = connection.split(":", 1)[1]

        print(f"Network button: connection = {connection}")

        if connection and connection != "--":
            ip_output = subprocess.check_output(
                ["ip", "-4", "-o", "addr", "show", "dev", "wlan0"],
                text=True
            )

            ip_address = ip_output.split()[3].split("/")[0]

            print(f"WiFi connected: {connection}")
            print(f"Web Manager: http://{ip_address}:5000")
            url = f"http://{ip_address}:5000"
            display.show_qr_signal.emit(url)
        else:
            print("No WiFi connection - starting RearWave hotspot...")

            subprocess.run(
                ["nmcli", "connection", "up", "RearWave-Hotspot"],
                check=True
            )

            url = "http://192.168.50.1:5000"

            print("RearWave hotspot started")
            print(f"Web Manager: {url}")

            display.show_hotspot_qr_signal.emit(url)

    except Exception as e:
        print(f"Network detection error: {e}")
def stop_hotspot_if_active():
    try:
        connection = subprocess.check_output(
            [
                "nmcli", "-t",
                "-f", "GENERAL.CONNECTION",
                "device", "show", "wlan0"
            ],
            text=True
        ).strip()

        connection = connection.split(":", 1)[1]

        if connection == "RearWave-Hotspot":
            print("Stopping RearWave hotspot...")

            subprocess.run(
                ["nmcli", "connection", "down", "RearWave-Hotspot"],
                check=False
            )

            print("RearWave hotspot stopped")

    except Exception as e:
        print(f"Hotspot stop error: {e}")
def button_pressed(deck, key, state):
    global main_key, return_timer
        # Button 15 - Network / QR
    if key == NETWORK_KEY:
        if state:
            network_button_pressed()
        return
    
    # Any normal media button turns off the hotspot
    if state:
        stop_hotspot_if_active()# Any normal media button turns off the hotspot
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
set_network_button(deck)
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

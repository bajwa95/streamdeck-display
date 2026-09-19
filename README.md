# Stream Deck Media Display

Raspberry Pi based media display controlled using an Elgato Stream Deck.

The Stream Deck buttons display GIFs/images on a fullscreen HDMI display.

## Features

- Elgato Stream Deck Original V2 support
- 15 programmable media buttons
- GIF/image playback on HDMI display
- Fullscreen PyQt5 display
- Short press temporarily displays selected media
- Automatically returns to the main media after 3 seconds
- Long press sets a button as the new MAIN media
- MAIN button highlighted on Stream Deck
- Web interface for uploading and deleting media
- Automatic media-folder refresh
- Stream Deck application starts automatically after desktop login
- Flask web server starts automatically at boot

---

# Hardware

This project was developed using:

- Raspberry Pi 3
- Raspberry Pi OS Desktop
- Elgato Stream Deck Original V2
- HDMI display

---

# Project Structure

```text
streamdeck-display/
├── app.py
├── web.py
├── requirements.txt
├── README.md
├── .gitignore
├── media/
└── venv/
```

`media/` and `venv/` are excluded from Git.

---

# 1. System Packages

Update the Raspberry Pi:

```bash
sudo apt update
sudo apt upgrade -y
```

Install the required system packages:

```bash
sudo apt install -y \
    python3-full \
    python3-venv \
    python3-pyqt5 \
    libhidapi-libusb0 \
    libusb-1.0-0-dev \
    libudev-dev
```

---

# 2. Create Project Folder

```bash
mkdir -p ~/streamdeck-display
cd ~/streamdeck-display
```

---

# 3. Create Python Virtual Environment

PyQt5 is installed through Raspberry Pi OS, so create the virtual environment with access to system packages:

```bash
python3 -m venv --system-site-packages venv
```

Activate it:

```bash
source venv/bin/activate
```

When activated, the terminal should show:

```text
(venv)
```

---

# 4. Install Python Packages

If installing from the repository:

```bash
pip install -r requirements.txt
```

For a fresh manual installation, the main packages are:

```bash
pip install streamdeck pillow flask
```

---

# 5. Media Folder

Create the media directory:

```bash
mkdir -p ~/streamdeck-display/media
```

Supported media currently includes:

```text
.gif
.jpg
.jpeg
.png
```

The application loads up to 15 media files because the Stream Deck has 15 buttons.

Media files are intentionally excluded from Git.

---

# 6. Run the Stream Deck Application Manually

Activate the virtual environment:

```bash
cd ~/streamdeck-display
source venv/bin/activate
```

Run:

```bash
python app.py
```

Alternatively, run directly with the virtual environment Python:

```bash
/home/garry/streamdeck-display/venv/bin/python /home/garry/streamdeck-display/app.py
```

The second method does not require manually activating the virtual environment.

---

# 7. Run the Web Media Manager

Activate the environment if necessary:

```bash
cd ~/streamdeck-display
source venv/bin/activate
```

Run:

```bash
python web.py
```

The Flask server runs on:

```text
Port 5000
```

From another device on the same network, open the Raspberry Pi's IP address with port 5000.

Example:

```text
http://RASPBERRY_PI_IP:5000
```

The web interface allows media files to be uploaded and deleted.

---

# 8. Start Stream Deck Display Automatically

`app.py` uses PyQt5 and requires the graphical desktop session.

For this reason it should be started using Desktop Autostart rather than a normal systemd service.

Create the autostart directory:

```bash
mkdir -p ~/.config/autostart
```

Create:

```bash
nano ~/.config/autostart/streamdeck-display.desktop
```

Add:

```ini
[Desktop Entry]
Type=Application
Name=StreamDeck Display
Exec=/home/garry/streamdeck-display/venv/bin/python /home/garry/streamdeck-display/app.py
WorkingDirectory=/home/garry/streamdeck-display
Terminal=false
X-GNOME-Autostart-enabled=true
```

Save the file.

The application will start automatically when the Raspberry Pi desktop session starts.

There is no need to run:

```bash
source venv/bin/activate
```

inside the autostart file because the virtual environment's Python executable is called directly.

---

# 9. Start Flask Web Server Automatically

The Flask server does not require the graphical desktop, so it can run as a systemd service.

Create:

```bash
sudo nano /etc/systemd/system/streamdeck-web.service
```

Add:

```ini
[Unit]
Description=Stream Deck Web Manager
After=network.target

[Service]
User=garry
WorkingDirectory=/home/garry/streamdeck-display
ExecStart=/home/garry/streamdeck-display/venv/bin/python /home/garry/streamdeck-display/web.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

Reload systemd:

```bash
sudo systemctl daemon-reload
```

Enable the service at boot:

```bash
sudo systemctl enable streamdeck-web
```

Start it:

```bash
sudo systemctl start streamdeck-web
```

Check its status:

```bash
sudo systemctl status streamdeck-web
```

Restart it after changing `web.py`:

```bash
sudo systemctl restart streamdeck-web
```

Stop it:

```bash
sudo systemctl stop streamdeck-web
```

View its logs:

```bash
journalctl -u streamdeck-web -f
```

---

# 10. Stream Deck Controls

## Short Press

Press and release a Stream Deck button.

The selected media is displayed temporarily.

After approximately 3 seconds the display returns to the MAIN media.

## Long Press

Hold a Stream Deck button for approximately 1.5 seconds.

That button becomes the new MAIN media.

The MAIN button is highlighted on the Stream Deck.

---

# 11. Automatic Media Refresh

The application periodically checks the `media` directory.

When a media file is uploaded or removed using the web interface, the Stream Deck media list and thumbnails are refreshed without requiring the complete application to be restarted.

---

# 12. PyQt Display Notes

The display application uses PyQt5.

If this error appears:

```text
qt.qpa.xcb: could not connect to display
```

make sure the application is running from the Raspberry Pi graphical desktop session.

Do not normally run `app.py` with:

```bash
sudo python app.py
```

The application needs access to the active graphical display.

Check the display environment with:

```bash
echo $DISPLAY
```

---

# 13. Stream Deck HID Troubleshooting

If the application reports that it cannot open the Stream Deck, check whether another copy of `app.py` is already running:

```bash
ps aux | grep app.py
```

If an old process is still running, terminate it:

```bash
kill PID
```

Replace `PID` with the process ID shown by the previous command.

Then start `app.py` again.

---

# 14. Git Configuration

Initialize Git:

```bash
git init
```

Recommended `.gitignore`:

```text
venv/
media/
__pycache__/
*.pyc
.DS_Store
```

Set Git identity:

```bash
git config --global user.name "bajwa95"
git config --global user.email "YOUR_GITHUB_EMAIL"
```

Create a commit:

```bash
git add .
git commit -m "Initial Stream Deck display and web uploader"
```

---

# 15. GitHub SSH Authentication

Generate an SSH key:

```bash
ssh-keygen -t ed25519 -C "bajwa95"
```

Display the public key:

```bash
cat ~/.ssh/id_ed25519.pub
```

Add the public key to the GitHub account.

Test authentication:

```bash
ssh -T git@github.com
```

Configure this repository to use SSH:

```bash
git remote set-url origin git@github.com:bajwa95/streamdeck-display.git
```

Verify:

```bash
git remote -v
```

Push:

```bash
git push -u origin main
```

---

# 16. Updating GitHub After Changes

After modifying the project:

```bash
cd ~/streamdeck-display
git status
git add .
git commit -m "Describe the changes"
git push
```

---

# Security Note

The Flask media manager is intended for use on a trusted local network.

The current web interface should not be exposed directly to the public Internet without adding authentication and appropriate security controls.

# Stream Deck Media Display

A Raspberry Pi media display controlled with an Elgato Stream Deck.

Media is shown fullscreen on an HDMI display using PyQt5. The Stream Deck provides quick media selection, MAIN-media control, and a dedicated **NET / QR** button for opening the web-based Media Manager from a phone.

## Features

- Elgato Stream Deck Original V2 support
- 14 media buttons plus 1 dedicated **NET / QR** button
- GIF, JPG, JPEG, and PNG display
- Fullscreen PyQt5 output
- Short press displays selected media temporarily
- Automatically returns to MAIN media after approximately 3 seconds
- Long press sets a media button as the new MAIN
- MAIN button is highlighted on the Stream Deck
- Flask web interface for uploading and deleting media
- Automatic media-folder refresh
- Dynamic QR code for Media Manager access
- On-demand Wi-Fi hotspot when normal Wi-Fi is unavailable
- Hotspot automatically shuts down when a normal media button is pressed
- Stream Deck application can start automatically after desktop login
- Flask Media Manager can start automatically at boot

## Hardware

Developed and tested with:

- Raspberry Pi 3B+
- Raspberry Pi OS Desktop
- Elgato Stream Deck Original V2 (15 keys)
- HDMI display

## Project Structure

```text
streamdeck-display/
├── app.py
├── web.py
├── requirements.txt
├── README.md
├── LICENSE
├── .gitignore
├── media/
└── venv/
```

The virtual environment and personal media files should not be included in the project repository.

---

# Installation

## 1. Install System Packages

Update Raspberry Pi OS:

```bash
sudo apt update
sudo apt upgrade -y
```

Install the required packages:

```bash
sudo apt install -y \
    python3-full \
    python3-venv \
    python3-pyqt5 \
    libhidapi-libusb0 \
    libusb-1.0-0-dev \
    libudev-dev
```

## 2. Create the Project Folder

```bash
mkdir -p ~/streamdeck-display
cd ~/streamdeck-display
```

Place the project files in this directory.

## 3. Create the Python Virtual Environment

PyQt5 is provided by Raspberry Pi OS, so create the environment with access to system packages:

```bash
python3 -m venv --system-site-packages venv
source venv/bin/activate
```

## 4. Install Python Packages

Install the project requirements:

```bash
pip install -r requirements.txt
```

The application uses the Stream Deck library, Pillow, Flask, and `qrcode`.

If `qrcode` is not already present:

```bash
pip install "qrcode[pil]"
```

## 5. Create the Media Folder

```bash
mkdir -p ~/streamdeck-display/media
```

Supported media:

```text
.gif
.jpg
.jpeg
.png
```

The first **14 media slots** are mapped to Stream Deck buttons 1–14. Button 15 is reserved for **NET / QR**.

---

# Running the Applications

## Stream Deck Display

From the Raspberry Pi graphical desktop session:

```bash
cd ~/streamdeck-display
source venv/bin/activate
python app.py
```

When starting through SSH while the Raspberry Pi desktop is already running, the display may need to be specified:

```bash
DISPLAY=:0 python app.py
```

`app.py` requires access to the graphical desktop and should not normally be run with `sudo`.

## Web Media Manager

Run:

```bash
cd ~/streamdeck-display
source venv/bin/activate
python web.py
```

The Media Manager listens on port `5000`.

From another device on the same network:

```text
http://RASPBERRY_PI_IP:5000
```

The web interface allows supported media files to be uploaded and deleted.

---

# Stream Deck Controls

## Buttons 1–14

### Short Press

Press and release a media button.

The selected media is displayed temporarily. After approximately 3 seconds, the display returns to the current MAIN media.

### Long Press

Hold a media button for approximately 1.5 seconds.

That media becomes the new MAIN media and its Stream Deck thumbnail is highlighted.

## Button 15 — NET / QR

The bottom-right key is reserved for network access.

### When Normal Wi-Fi Is Connected

Pressing **NET / QR**:

1. Detects the active Wi-Fi connection.
2. Reads the Raspberry Pi's current IPv4 address.
3. Builds the Media Manager address using port `5000`.
4. Generates a QR code.
5. Displays the QR code fullscreen on the HDMI display.

Example:

```text
http://192.168.x.x:5000
```

A phone connected to the same Wi-Fi network can scan the QR code to open the Media Manager.

### When Normal Wi-Fi Is Not Connected

Pressing **NET / QR** starts the configured `RearWave-Hotspot` connection.

The HDMI display instructs the user to:

1. Connect the phone to Wi-Fi network `RearWave`.
2. Wait until the phone is connected.
3. Scan the displayed Media Manager QR code.

The hotspot Media Manager address is:

```text
http://192.168.50.1:5000
```

The hotspot is **on demand**. It is not intended to run continuously or automatically at boot.

When a normal media button (1–14) is pressed while `RearWave-Hotspot` is active, the application shuts down the hotspot so NetworkManager can reconnect to a known Wi-Fi network.

---

# Configure the On-Demand Hotspot

The hotspot uses NetworkManager and the Raspberry Pi's `wlan0` interface.

## 1. Create the Hotspot Profile

```bash
sudo nmcli connection add \
    type wifi \
    ifname wlan0 \
    con-name RearWave-Hotspot \
    autoconnect no \
    ssid RearWave
```

Configure access-point mode and the fixed hotspot address:

```bash
sudo nmcli connection modify RearWave-Hotspot \
    802-11-wireless.mode ap \
    802-11-wireless.band bg \
    ipv4.method shared \
    ipv4.addresses 192.168.50.1/24 \
    ipv6.method disabled
```

Configure WPA security:

```bash
sudo nmcli connection modify RearWave-Hotspot \
    wifi-sec.key-mgmt wpa-psk \
    wifi-sec.psk "YOUR_HOTSPOT_PASSWORD"
```

Replace `YOUR_HOTSPOT_PASSWORD` with your own secure password.

Do **not** place the real hotspot password in source code, README files, or public configuration examples.

Ensure the hotspot does not automatically start:

```bash
sudo nmcli connection modify RearWave-Hotspot connection.autoconnect no
```

Verify:

```bash
nmcli connection show RearWave-Hotspot
```

## 2. Allow the Display App to Control the Hotspot

`app.py` runs as the normal desktop user. NetworkManager may otherwise request interactive authorization when the application tries to start or stop the hotspot.

Create a PolicyKit rule:

```bash
sudo nano /etc/polkit-1/rules.d/49-rearwave-network.rules
```

Add:

```javascript
polkit.addRule(function(action, subject) {
    if (
        subject.user == "YOUR_USERNAME" &&
        (
            action.id == "org.freedesktop.NetworkManager.network-control" ||
            action.id == "org.freedesktop.NetworkManager.wifi.share.protected"
        )
    ) {
        return polkit.Result.YES;
    }
});
```

Replace `YOUR_USERNAME` with the Raspberry Pi account that runs `app.py`.

Verify:

```bash
nmcli general permissions | grep -E "network-control|wifi.share.protected"
```

Both required permissions should report `yes`.

## 3. Normal Wi-Fi Recovery

The normal Wi-Fi profile should have autoconnect enabled:

```bash
nmcli -f connection.id,connection.autoconnect connection show "YOUR_WIFI_CONNECTION"
```

If necessary:

```bash
sudo nmcli connection modify "YOUR_WIFI_CONNECTION" connection.autoconnect yes
```

The hotspot profile should remain:

```text
connection.autoconnect: no
```

This allows the Raspberry Pi to return to its normal saved Wi-Fi connection after the hotspot is stopped or after a reboot.

---

# Automatic Media Refresh

The application periodically checks the `media` directory.

When supported media is uploaded or removed through the web interface, the Stream Deck thumbnails and media mapping refresh without requiring a complete application restart.

---

# Start the Stream Deck Display Automatically

`app.py` uses PyQt5 and requires the graphical desktop session, so desktop autostart is recommended.

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
Exec=/home/YOUR_USERNAME/streamdeck-display/venv/bin/python /home/YOUR_USERNAME/streamdeck-display/app.py
WorkingDirectory=/home/YOUR_USERNAME/streamdeck-display
Terminal=false
X-GNOME-Autostart-enabled=true
```

Replace `YOUR_USERNAME` with the Raspberry Pi username.

The Stream Deck display will start after the graphical desktop session starts.

---

# Start the Web Media Manager Automatically

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
User=YOUR_USERNAME
WorkingDirectory=/home/YOUR_USERNAME/streamdeck-display
ExecStart=/home/YOUR_USERNAME/streamdeck-display/venv/bin/python /home/YOUR_USERNAME/streamdeck-display/web.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

Replace `YOUR_USERNAME` with the Raspberry Pi username.

Reload systemd and enable the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable streamdeck-web
sudo systemctl start streamdeck-web
```

Check status:

```bash
sudo systemctl status streamdeck-web
```

Useful commands:

```bash
sudo systemctl restart streamdeck-web
sudo systemctl stop streamdeck-web
journalctl -u streamdeck-web -f
```

---

# Troubleshooting

## PyQt Cannot Connect to the Display

If you see:

```text
qt.qpa.xcb: could not connect to display
```

make sure the Raspberry Pi graphical desktop session is running.

Check:

```bash
echo $DISPLAY
```

When starting remotely while the local desktop is active, try:

```bash
DISPLAY=:0 python app.py
```

Do not normally run the graphical application with:

```bash
sudo python app.py
```

## Stream Deck Cannot Be Opened

Check whether another `app.py` process is already using the Stream Deck:

```bash
ps aux | grep "[a]pp.py"
```

If necessary, terminate the old process:

```bash
kill PID
```

If a stopped process does not exit:

```bash
kill -9 PID
```

Then start `app.py` again.

## Hotspot Does Not Start

Check NetworkManager permissions:

```bash
nmcli general permissions | grep -E "network-control|wifi.share.protected"
```

Check that the hotspot profile exists:

```bash
nmcli connection show RearWave-Hotspot
```

Check the current Wi-Fi device state:

```bash
nmcli device status
```

---

# Security

The Flask Media Manager is designed for use on a trusted local network or the local `RearWave` hotspot.

It currently does not provide public-Internet-grade authentication or access control. Do not expose port `5000` directly to the public Internet.

Use a strong hotspot password and keep credentials out of the source code and documentation.

---

# License

This project is licensed under the MIT License. See `LICENSE` for details.

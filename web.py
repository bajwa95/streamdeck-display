from flask import Flask, request, redirect, url_for, send_from_directory
import os

app = Flask(__name__)

MEDIA_FOLDER = os.path.expanduser("~/streamdeck-display/media")
ALLOWED_EXTENSIONS = {".gif", ".jpg", ".jpeg", ".png"}

os.makedirs(MEDIA_FOLDER, exist_ok=True)


def allowed_file(filename):
    return os.path.splitext(filename)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/")
def index():
    files = sorted([
        f for f in os.listdir(MEDIA_FOLDER)
        if allowed_file(f)
    ])

    cards = ""

    for filename in files:
        cards += f"""
        <div class="card">
            <img src="/media/{filename}">
            <div class="filename">{filename}</div>

            <form action="/delete/{filename}" method="post"
                  onsubmit="return confirm('Delete {filename}?');">
                <button class="delete">Delete</button>
            </form>
        </div>
        """

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta name="viewport"
              content="width=device-width, initial-scale=1">

        <title>Stream Deck Media</title>

        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 30px;
                background: #111;
                color: white;
            }}

            h1 {{
                margin-bottom: 25px;
            }}

            .upload {{
                background: #222;
                padding: 20px;
                border-radius: 10px;
                margin-bottom: 30px;
            }}

            button {{
                padding: 10px 16px;
                border: 0;
                border-radius: 6px;
                cursor: pointer;
            }}

            .upload-button {{
                background: #2d8cff;
                color: white;
            }}

            .delete {{
                background: #d93636;
                color: white;
                width: 100%;
            }}

            .grid {{
                display: grid;
                grid-template-columns:
                    repeat(auto-fill, minmax(150px, 1fr));
                gap: 20px;
            }}

            .card {{
                background: #222;
                padding: 10px;
                border-radius: 10px;
            }}

            .card img {{
                width: 100%;
                height: 130px;
                object-fit: cover;
                border-radius: 6px;
            }}

            .filename {{
                padding: 10px 0;
                word-break: break-all;
            }}
        </style>
    </head>

    <body>

        <h1>Stream Deck Media</h1>

        <div class="upload">

            <form action="/upload"
                  method="post"
                  enctype="multipart/form-data">

                <input type="file"
                       name="files"
                       multiple
                       accept=".gif,.jpg,.jpeg,.png">

                <button class="upload-button">
                    Upload
                </button>

            </form>

        </div>

        <div class="grid">
            {cards}
        </div>

    </body>
    </html>
    """


@app.route("/upload", methods=["POST"])
def upload():
    files = request.files.getlist("files")

    for file in files:

        if file.filename and allowed_file(file.filename):

            filename = os.path.basename(file.filename)

            file.save(
                os.path.join(MEDIA_FOLDER, filename)
            )

    return redirect(url_for("index"))


@app.route("/delete/<filename>", methods=["POST"])
def delete(filename):

    filename = os.path.basename(filename)
    path = os.path.join(MEDIA_FOLDER, filename)

    if os.path.isfile(path):
        os.remove(path)

    return redirect(url_for("index"))


@app.route("/media/<filename>")
def media(filename):
    return send_from_directory(MEDIA_FOLDER, filename)


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )

from flask import Flask, render_template, request, redirect, url_for
import threading
import webbrowser
import time

from auth import authenticate  # s'il est dans le même dossier que app.py


app = Flask(__name__)   # <<< ICI : __name_ (deux underscores)


@app.route("/")
def index():
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    message = None
    status = None
    username_value = ""

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        username_value = username

        if not username or not password:
            status = "FAIL"
            message = "Veuillez remplir tous les champs."
        else:
            status, message, reason = authenticate(username, password)

        return render_template(
            "login.html",
            message=message,
            status=status,
            username=username_value,
        )

    return render_template(
        "login.html",
        message=message,
        status=status,
        username=username_value,
    )


def open_browser():
    time.sleep(1)
    webbrowser.open("http://127.0.0.1:5000/login")


if __name__ == "__main__":   # <<< ICI AUSSI : __name__
    threading.Thread(target=open_browser).start()
    app.run(debug=True)

import json
import os
from flask import Flask, render_template, request, jsonify
import sys

# Add the parent folder to sys.path
sys.path.insert(0, os.path.abspath(".."))
from backend.main import assistant_loop

# Set the correct template and static folder paths
template_dir = os.path.abspath("./templates")
app = Flask(__name__, template_folder=template_dir)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/execute_assistant", methods=["POST"])
def execute_assistant():
    data = request.get_json()
    lang = data["language"]
    speed_multiplier = float(data["speed_multiplier"])
    assistant_name = data["assistant_name"].lower()
    credentials = json.loads(data['credentials'])

    try:
        assistant_loop(lang=lang, speed_multiplier=speed_multiplier, assistant_name=assistant_name, credentials=credentials)
        response = jsonify(success=True)
    except Exception as e:
        response = jsonify(success=False, error=str(e))

    return response

if __name__ == "__main__":
    app.run(debug=True)
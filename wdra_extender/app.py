from flask import Flask, render_template, request


app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/extract', methods=['POST'])
def request_extract():
    return request.form


@app.route('/extract/<uuid:extract_id>')
def download_extract(extract_id):
    raise NotImplementedError

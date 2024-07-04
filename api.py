import os
from flask import Flask,jsonify,request
from anthropic_vision_script import get_ramq

app = Flask(__name__)

@app.before_request
def check_token():
    if request.path == '/extract_json_from_image':
        token = request.headers.get('RAMQ-Billr-API-Key')
        headerToken = os.environ.get('HEADER_TOKEN')
        if token is None or token != headerToken:
            return jsonify({"error": "Invalid or missing token"}), 401


@app.route('/')
def hello():
    return jsonify(alive='true')

@app.route('/extract_json_from_image',methods=['POST'])
def extract_json_from_image():
    request_data = request.get_json()
    image_url =  request_data['image_url'] 
    try:
        ramq, last_name, first_name, dob, gender = get_ramq(image_url)
        return jsonify({
            "ramq": ramq,
            "last_name":last_name,
            "first_name":first_name,
            "dob": dob,
            "gender":gender
        })

    except ValueError as e:
        print(e)
        return "", 500

if __name__ == '__main__':
    app.run(debug=True, port = 9000)

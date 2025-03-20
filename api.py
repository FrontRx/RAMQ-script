import os
from flask import Flask,jsonify,request
from anthropic_vision_script import get_ramq, validate_ramq

app = Flask(__name__)

@app.before_request
def check_token():
    if request.path == "/":
        return
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
    is_image = request_data['is_image']
    image_url =  request_data['image_url'] 
    text = request_data['text']

    input_data = text
    if is_image:
        input_data = image_url

    try:
        ramq, last_name, first_name, dob, gender, valid_ramq, mrn = get_ramq(input_data, is_image)
        return jsonify({
            "ramq": ramq,
            "last_name":last_name,
            "first_name":first_name,
            "dob": dob.strftime("%Y-%m-%d"),
            "gender": gender,
            "valid_ramq": valid_ramq,
            "mrn": mrn
        })

    except ValueError as e:
        print(e, flush=True)
        return jsonify({"error": str(e)}), 500


@app.route('/validate_ramq', methods=['GET'])
def ramq_validation():
    ramq = request.args.get('ramq')
    if ramq is None:
        return jsonify({"error": "Missing ramq query parameter"}), 400
    try:
        valid_ramq = validate_ramq(ramq)
        return jsonify({"valid": valid_ramq})
    except Exception as e:
        print(e, flush=True)
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, port = 9000)

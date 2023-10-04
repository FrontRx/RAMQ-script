from flask import Flask,jsonify,request
from azure_vision_script import get_ramq

app = Flask(__name__)

@app.before_request
def check_token():
    token = request.headers.get('RAMQ-FrontRx-Billr')
    if token is None or token != 'sampleToken':
        return jsonify({"error": "Invalid or missing token"}), 401


@app.route('/')
def hello():
    return jsonify(message='Alive')

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


if __name__ == '__main__':
    app.run(debug=True, port = 9000)
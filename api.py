import os
import re
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
    try:
        request_data = request.get_json()
        if not request_data:
            return jsonify({"error": "Invalid or missing JSON in request body"}), 400
            
        is_image = request_data.get('is_image')
        image_url = request_data.get('image_url')
        text = request_data.get('text')
        
        if is_image is None:
            return jsonify({"error": "Missing 'is_image' field in request"}), 400
        
        if is_image and not image_url:
            return jsonify({"error": "Missing 'image_url' field for image processing"}), 400
            
        if not is_image and not text:
            return jsonify({"error": "Missing 'text' field for text processing"}), 400

        input_data = text
        if is_image:
            input_data = image_url

        try:
            ramq, last_name, first_name, dob, gender, valid_ramq, mrn = get_ramq(input_data, is_image)
            
            # Format date correctly
            formatted_date = dob.strftime("%Y-%m-%d") if dob else None
            
            return jsonify({
                "ramq": ramq,
                "last_name": last_name,
                "first_name": first_name,
                "dob": formatted_date,
                "gender": gender,
                "valid_ramq": valid_ramq,
                "mrn": mrn
            })

        except ValueError as e:
            print(f"Error processing data: {str(e)}", flush=True)
            return jsonify({"error": str(e)}), 500
        except Exception as e:
            print(f"Unexpected error: {str(e)}", flush=True)
            return jsonify({"error": "An unexpected error occurred during processing"}), 500
            
    except Exception as e:
        print(f"API error: {str(e)}", flush=True)
        return jsonify({"error": "An error occurred while processing the request"}), 500


@app.route('/validate_ramq', methods=['GET'])
def ramq_validation():
    try:
        ramq = request.args.get('ramq')
        if ramq is None:
            return jsonify({"error": "Missing ramq query parameter"}), 400
            
        # Validate RAMQ format first
        if not re.match(r"^[A-Z]{4}\d{8}$", ramq):
            return jsonify({"error": "Invalid RAMQ format. Must be 4 letters followed by 8 digits", "valid": False}), 400
            
        try:
            valid_ramq = validate_ramq(ramq)
            return jsonify({"valid": valid_ramq})
        except Exception as e:
            print(f"RAMQ validation error: {str(e)}", flush=True)
            return jsonify({"error": str(e), "valid": False}), 500
            
    except Exception as e:
        print(f"API error: {str(e)}", flush=True)
        return jsonify({"error": "An error occurred while processing the request"}), 500


if __name__ == '__main__':
    app.run(debug=True, port = 9000)

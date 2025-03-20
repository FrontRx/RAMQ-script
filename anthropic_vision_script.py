import os
import re
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from PIL import Image  # Importing PIL library for image resizing
from io import BytesIO  # Importing BytesIO from io

from dotenv import load_dotenv
import base64
import json
import anthropic
import httpx
from typing import List
# Load environment variables from the .env file in the current directory
load_dotenv()
anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY")

# Configure httpx client with timeouts
http_client = httpx.Client(timeout=httpx.Timeout(30.0, connect=30.0))

class PersonInfo(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: datetime
    gender: Optional[str] = None
    ramq: str = Field(
        ...,
        pattern=r"^[A-Z]{4}\d{8}$",
        description="RAMQ number should have 4 letters followed by 8 digits",
    )
    mrn: Optional[str] = Field(None, description="Medical Record Number (MRN) can contain digits or alphanumeric characters. If MRN is not present, return None.")


class PatientInfo(BaseModel):
    first_name: str
    last_name: str
    patient_number: Optional[str] = None
    room_number: Optional[str] = None


class PatientList(BaseModel):
    patients: List[PatientInfo]


def validate_ramq(ramq: str) -> bool:
    # Character to decimal value mapping
    char_to_decimal = {
        "A": 193,
        "B": 194,
        "C": 195,
        "D": 196,
        "E": 197,
        "F": 198,
        "G": 199,
        "H": 200,
        "I": 201,
        "J": 209,
        "K": 210,
        "L": 211,
        "M": 212,
        "N": 213,
        "O": 214,
        "P": 215,
        "Q": 216,
        "R": 217,
        "S": 226,
        "T": 227,
        "U": 228,
        "V": 229,
        "W": 230,
        "X": 231,
        "Y": 232,
        "Z": 233,
        "0": 240,
        "1": 241,
        "2": 242,
        "3": 243,
        "4": 244,
        "5": 245,
        "6": 246,
        "7": 247,
        "8": 248,
        "9": 249,
    }
 

    # Updated multipliers for all 14 characters before the check digit
    # Based on the example provided (NOMI-AAAA-SxMM-JJ-S gives 14 chars):
    multipliers = [1, 3, 7, 9, 1, 7, 1, 3, 4, 5, 7, 6, 9, 1]

    def calculate_check_digit(nam_decomposed: str) -> int:
        total = 0
        for char, mult in zip(nam_decomposed, multipliers):
            total += char_to_decimal[char] * mult
        return total % 10

    if len(ramq) != 12:
        return False

    # Extract components
    name = ramq[:4]
    year = ramq[4:6]
    month = ramq[6:8]
    day = ramq[8:10]
    sequence = ramq[10]
    check_digit = int(ramq[11])

    # Determine full year
    current_year = datetime.now().year
    if int(year) > 50:
        full_year = f"19{year}"
    else:
        full_year = f"20{year}"
    if int(full_year) > current_year:
        # If year surpasses current year, subtract a century
        full_year = str(int(full_year) - 100)

    # Adjust month and determine sex
    month_num = int(month)
    if month_num > 50:
        month_num -= 50
        sex = "F"
    else:
        sex = "M"

    # Construct the full string for validation (no check digit at this point)
    nam_decomposed = (
        name  # NOMI (4 chars)
        + full_year  # AAAA (4 chars)
        + sex  # Sx (1 char for sex)
        + f"{month_num:02d}"  # MM (2 chars)
        + day  # JJ (2 chars)
        + sequence  # S (1 char)
    )

    # Calculate check digit with current assumption
    calculated_check = calculate_check_digit(nam_decomposed)

    # If check fails, try previous century if we haven't already
    if calculated_check != check_digit and full_year.startswith("20"):
        full_year = str(int(full_year) - 100)
        nam_decomposed = name + full_year + sex + f"{month_num:02d}" + day + sequence
        calculated_check = calculate_check_digit(nam_decomposed)

    return calculated_check == check_digit

def resize_image(image_data: bytes, max_size_mb: float = 5.0) -> bytes:
    image = Image.open(BytesIO(image_data))
    while len(image_data) > max_size_mb * 1024 * 1024:
        width, height = image.size
        new_width = int(width * 0.9)
        new_height = int(height * 0.9)
        image = image.resize((new_width, new_height), Image.ANTIALIAS)
        buffer = BytesIO()
        image.save(buffer, format="JPEG")
        image_data = buffer.getvalue()
    return image_data

def get_ramq(input_data, is_image=True):
    if is_image:
        try:
            # Download image and convert to base64
            image_response = http_client.get(input_data)
            image_data = image_response.content

            # Resize image if it exceeds 5 MB
            if len(image_data) > 5 * 1024 * 1024:
                image_data = resize_image(image_data)

            image_data = base64.standard_b64encode(image_data).decode("utf-8")

            # Determine media type based on content
            content_type = image_response.headers.get('content-type', 'image/jpeg')

            prompt = "Perform OCR. Extract the RAMQ number, which MUST have exactly 4 letters followed by exactly 8 digits, totaling 12 characters. Remove all spaces from RAMQ. The first 3 letters of RAMQ are the person's last name use that to look up the last name in the text. First name starts with the 4th letter of the RAMQ AND Should be a name! Extract the person's first name, last name, date of birth, and RAMQ number. Output as JSON with keys: 'first_name', 'last_name', and 'ramq'. Ensure the RAMQ is exactly 12 characters (4 letters + 8 digits). Also extract the MRN number if it is present in the image. Output as JSON with keys: 'first_name', 'last_name', 'ramq', and 'mrn'. Double-check your output before responding. Do not be VERBOSE and DO NOT include any text outside the JSON object."

            message = anthropic.Anthropic().messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1024,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": content_type,
                                    "data": image_data,
                                },
                            }
                        ],
                    }
                ],
            )
            print(message)
            response = message.content[0].text
            print(response)
        except Exception as e:
            raise ValueError(f"Error processing image: {str(e)}")
    else:
        prompt = f"From this text locate and extract the RAMQ number, which MUST have exactly 4 letters followed by exactly 8 digits, totaling 12 characters. Remove all spaces from RAMQ. The first 3 letters of RAMQ are the person's last name use that to look up the last name in the text. First name starts with the 4th letter of the RAMQ AND Should be a name! Extract the person's first name, last name, and RAMQ number. For the date of birth, convert any 2-digit year to a 4-digit year (if year > 50, add 1900, else add 2000). Format the date as YYYY-MM-DD and double check that the date is valid (i.e. DD is <= 31, YYYY < current year and MM <= 12). Output as JSON with keys: 'first_name', 'last_name', 'ramq', 'mrn', 'date_of_birth'. Ensure the RAMQ is exactly 12 characters (4 letters + 8 digits). Double-check your output before responding. Do not be VERBOSE and DO NOT include any text outside the JSON object. Here is the text: {input_data}"

        message = anthropic.Anthropic().messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
        )
        response = message.content[0].text

    # Parse the JSON response
    data = json.loads(response)

    # Extract and validate date of birth from RAMQ
    ramq = data["ramq"]
    # Remove any spaces from the RAMQ number
    ramq = ramq.replace(" ", "")
    year = int(ramq[4:6])
    month = int(ramq[6:8])
    day = int(ramq[8:10])

    # Adjust year for century and ensure it is <= current year
    current_year = datetime.now().year
    if year > 50:
        year += 1900
    else:
        year += 2000

    if year > current_year:
        year -= 100

    # Adjust month for gender
    gender = None
    gender_digit = int(ramq[6])

    if gender_digit in [0, 1]:
        gender = "male"
    else:
        gender = 'female'
        month -= 50


    dob_str = f"{year}-{month:02d}-{day:02d}"

    # Validate dob
    try:
        dob = datetime.strptime(dob_str, "%Y-%m-%d")
    except ValueError:
        print(f"Unsupported date format: {dob_str}")
        dob = datetime.now()

    person_info = PersonInfo(
        first_name=data["first_name"],
        last_name=data["last_name"],
        date_of_birth=dob,
        gender=gender,
        ramq=data["ramq"],
        mrn=data.get("mrn")
    )

    is_valid = validate_ramq(data["ramq"])

    return (
        person_info.ramq,
        person_info.last_name,
        person_info.first_name,
        person_info.date_of_birth,
        person_info.gender,
        is_valid,
        person_info.mrn
    )
def get_patient_list(input_data: str, is_image: bool = True, additional_prompt: str = ""):
    base_prompt = "Extract a list of patients from the image or text. For each patient, provide their first name and last name. If available, also include their patient number and room number. Output as JSON with a 'patients' key containing a list of patient objects. Each patient object should have keys: first_name, last_name, and optionally patient_number and room_number. "
    prompt = base_prompt + additional_prompt

    if is_image:
        try:
            # Get image data
            image_response = httpx.get(input_data)
            image_data = base64.b64encode(image_response.content).decode("utf-8")
            image_media_type = "image/jpeg"  # Assuming JPEG, could be made dynamic

            # Create message with image
            message = anthropic.Anthropic().messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=1024,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": image_media_type,
                                    "data": image_data,
                                }
                            }
                        ]
                    }
                ]
            )
            response = message.content[0].text

        except Exception as e:
            raise ValueError(f"Error processing image: {str(e)}")
    else:
        # Text-only message
        message = anthropic.Anthropic().messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": f"{prompt} Here is the text: {input_data}"
                }
            ]
        )
        response = message.content[0].text
    # Parse the JSON response
    try:
        # Remove any leading/trailing whitespace and ensure we have valid JSON
        cleaned_response = response.strip()
        if not cleaned_response.startswith('{'):
            # Extract JSON from the response if it's embedded in text
            start_idx = cleaned_response.find('{')
            end_idx = cleaned_response.rfind('}') + 1
            if (start_idx != -1 and end_idx != 0):
                cleaned_response = cleaned_response[start_idx:end_idx]
            else:
                raise ValueError("No valid JSON found in response")
                
        data = json.loads(cleaned_response)
        
        patients = []
        for patient_data in data["patients"]:
            # Only include room_number if it exists and is not empty/None
            room_number = patient_data.get("room_number")
            if room_number and str(room_number).strip():
                room_number = str(room_number).strip()
            else:
                room_number = None
                
            patient = PatientInfo(
                first_name=patient_data["first_name"],
                last_name=patient_data["last_name"],
                patient_number=patient_data.get("patient_number"),
                room_number=room_number
            )
            patients.append(patient)

        return PatientList(patients=patients)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse response as JSON: {str(e)}\nResponse was: {response}")

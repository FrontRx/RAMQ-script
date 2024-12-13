import os
import re
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

from dotenv import load_dotenv
from llama_index.multi_modal_llms.anthropic import AnthropicMultiModal

from llama_index.core.multi_modal_llms.generic_utils import load_image_urls
from llama_index.core.schema import ImageDocument

import requests
from io import BytesIO

from PIL import Image
import tempfile

from typing import List, Optional


# Load environment variables from the .env file in the current directory
load_dotenv()
anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY")


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


class PatientInfo(BaseModel):
    first_name: str
    last_name: str
    patient_number: Optional[str] = None
    room_number: Optional[str] = None


class PatientList(BaseModel):
    patients: List[PatientInfo]


# Initiated Anthropic MultiModal class
anthropic_mm_llm = AnthropicMultiModal(
    max_tokens=300,
    model="claude-3-opus-20240229",
    anthropic_api_key=anthropic_api_key,
)


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


def get_ramq(input_data, is_image=True):
    if is_image:
        # Load image documents from URLs
        try:
            # Download the image from the URL
            response = requests.get(input_data)
            img = Image.open(BytesIO(response.content))

            # Create a temporary directory to save the image
            with tempfile.TemporaryDirectory() as temp_dir:
                width_percent = (600 / float(img.size[0]))
                height_size = int((float(img.size[1]) * float(width_percent)))
                img = img.resize((600, height_size), Image.LANCZOS)

                image_file = os.path.join(temp_dir, "temp_image.png")
                img.save(image_file)

                # Load the image as an ImageDocument
                image_documents = [ImageDocument(image_path=image_file)]
                prompt = "Perform OCR. Extract the RAMQ number, which MUST have exactly 4 letters followed by exactly 8 digits, totaling 12 characters. Remove all spaces from RAMQ. The first 3 letters of RAMQ are the person's last name use that to look up the last name in the text. First name starts with the 4th letter of the RAMQ AND Should be a name! Extract the person's first name, last name, date of birth, and RAMQ number. Output as JSON with keys: 'first_name', 'last_name', and 'ramq'. Ensure the RAMQ is exactly 12 characters (4 letters + 8 digits). Double-check your output before responding. Do not be VERBOSE and DO NOT include any text outside the JSON object."
                response = anthropic_mm_llm.complete(
                    prompt=prompt,
                    image_documents=image_documents,
                )
        except Exception as e:
            raise ValueError(f"Error loading image: {str(e)}")
    else:
        prompt = f"From this text locate and extract the RAMQ number, which MUST have exactly 4 letters followed by exactly 8 digits, totaling 12 characters. Remove all spaces from RAMQ. The first 3 letters of RAMQ are the person's last name use that to look up the last name in the text. First name starts with the 4th letter of the RAMQ AND Should be a name! Extract the person's first name, last name, date of birth, and RAMQ number. Output as JSON with keys: 'first_name', 'last_name', and 'ramq'. Ensure the RAMQ is exactly 12 characters (4 letters + 8 digits). Double-check your output before responding. Do not be VERBOSE and DO NOT include any text outside the JSON object. Here is the text: {input_data}"
        response = anthropic_mm_llm.complete(
            prompt=prompt,
            image_documents=None,
        )

    # Parse the JSON response
    import json
    data = json.loads(response.text)

    # Extract and validate date of birth from RAMQ
    ramq = data["ramq"]
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
    if gender_digit in [5, 6]:
        gender = "female"
        month -= 50
    elif gender_digit in [0, 1]:
        gender = "male"

    dob_str = f"{year}-{month:02d}-{day:02d}"
    
    # Validate dob
    try:
        dob = datetime.strptime(dob_str, "%Y-%m-%d")
    except ValueError:
        raise ValueError(f"Unsupported date format: {dob_str}")

    person_info = PersonInfo(
        first_name=data["first_name"],
        last_name=data["last_name"],
        date_of_birth=dob,
        gender=gender,
        ramq=data["ramq"]
    )

    is_valid = validate_ramq(data["ramq"])

    return (
        person_info.ramq,
        person_info.last_name,
        person_info.first_name,
        person_info.date_of_birth,
        person_info.gender,
        is_valid
    )

def get_patient_list(input_data: str, is_image: bool = True, additional_prompt: str = ""):
    base_prompt = "Extract a list of patients from the image or text. For each patient, provide their first name and last name. If available, also include their patient number and room number. Output as JSON with a 'patients' key containing a list of patient objects. Each patient object should have keys: first_name, last_name, and optionally patient_number and room_number. "
    prompt = base_prompt + additional_prompt

    if is_image:
        try:
            response = requests.get(input_data)
            img = Image.open(BytesIO(response.content))

            with tempfile.TemporaryDirectory() as temp_dir:
                image_file = os.path.join(temp_dir, "temp_image.png")
                img.save(image_file)
                image_documents = [ImageDocument(image_path=image_file)]
                response = anthropic_mm_llm.complete(
                    prompt=prompt,
                    image_documents=image_documents,
                )
        except Exception as e:
            raise ValueError(f"Error loading image: {str(e)}")
    else:
        response = anthropic_mm_llm.complete(
            prompt=f"{prompt} Here is the text: {input_data}",
            image_documents=None,
        )

    # Parse the JSON response
    data = json.loads(response.text)
    
    patients = []
    for patient_data in data["patients"]:
        patient = PatientInfo(
            first_name=patient_data["first_name"],
            last_name=patient_data["last_name"],
            patient_number=patient_data.get("patient_number"),
            room_number=patient_data.get("room_number")
        )
        patients.append(patient)

    return PatientList(patients=patients)

import os
import re
from datetime import datetime, date as date_type
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
    date_of_birth: date_type
    gender: Optional[str] = None
    ramq: str = Field(..., pattern=r"^[A-Z]{4}\d{8}$", description="RAMQ number in format AAAA00000000")


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
                prompt = "Perform OCR. Extract the RAMQ number, which MUST have exactly 4 letters followed by exactly 8 digits, totaling 12 characters. Remove all spaces from RAMQ. The first 3 letters of RAMQ are the person's last name use that to look up the last name in the text. Extract the person's first name, last name, date of birth, and RAMQ number. Output as JSON with keys: 'first_name', 'last_name', 'date_of_birth' (in %Y/%m/%d format), and 'ramq'. Ensure the RAMQ is exactly 12 characters (4 letters + 8 digits). Double-check your output before responding. Do not be VERBOSE and DO NOT include any text outside the JSON object."
                response = anthropic_mm_llm.complete(
                    prompt=prompt,
                    image_documents=image_documents,
                )
        except Exception as e:
            raise ValueError(f"Error loading image: {str(e)}")

    else:
        # Process free text input
        prompt = f"From this text locate and extract the RAMQ number, which MUST have exactly 4 letters followed by exactly 8 digits, totaling 12 characters. Remove all spaces from RAMQ. The first 3 letters of RAMQ are the person's last name use that to look up the last name in the text. Extract the person's first name, last name, date of birth, and RAMQ number. Output as JSON with keys: 'first_name', 'last_name', 'date_of_birth' (in %Y/%m/%d format), and 'ramq'. Ensure the RAMQ is exactly 12 characters (4 letters + 8 digits). Double-check your output before responding. Do not be VERBOSE and DO NOT include any text outside the JSON object. Here is the text: {input_data}"
        response = anthropic_mm_llm.complete(
            prompt=prompt,
            image_documents=None,
        )

    # Parse the JSON response
    import json
    data = json.loads(response.text)
    # Extract date of birth
    dob_str = data["date_of_birth"]
    print(dob_str)
    try:
        dob = datetime.strptime(dob_str, "%Y/%m/%d").date()
    except ValueError:
        try:
            dob = datetime.strptime(dob_str, "%Y-%m-%d").date()
        except ValueError:
            try:
                dob = datetime.strptime(dob_str, "%Y-%m-%d %H:%M:%S").date()
            except ValueError:
                raise ValueError(f"Unsupported date format: {dob_str}")

    # Extract gender based on RAMQ
    gender = None
    if "ramq" in data:
        gender_digit = int(data["ramq"][6])
        if gender_digit in [5, 6]:
            gender = "female"
        elif gender_digit in [0, 1]:
            gender = "male"

    person_info = PersonInfo(
        first_name=data["first_name"],
        last_name=data["last_name"],
        date_of_birth=dob,
        gender=gender,
        ramq=data["ramq"]
    )

    return person_info.ramq, person_info.last_name, person_info.first_name, person_info.date_of_birth, person_info.gender

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

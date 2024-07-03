import os
import re
from datetime import datetime
from typing import Optional
import re
from pydantic import BaseModel, Field

from dotenv import load_dotenv
from llama_index.multi_modal_llms.anthropic import AnthropicMultiModal

from llama_index.core.multi_modal_llms.generic_utils import load_image_urls
from llama_index.core.schema import ImageDocument

import requests
from io import BytesIO

from PIL import Image
import tempfile

class PersonInfo(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: datetime
    gender: Optional[str] = None
    ramq: str = Field(..., pattern=r"^[A-Z]{4}\d{8}$", description="RAMQ number in format AAAA00000000")

# Load environment variables from the .env file in the current directory
load_dotenv()
anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY")

# Initiated Anthropic MultiModal class
anthropic_mm_llm = AnthropicMultiModal(
    max_tokens=300,
    model="claude-3-haiku-20240307",
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
                image_file = os.path.join(temp_dir, "temp_image.png")
                img.save(image_file)

                # Load the image as an ImageDocument
                image_documents = [ImageDocument(image_path=image_file)]
                prompt = f"Extract the person's full name, date of birth, gender, and RAMQ number from the image and output as JSON using keys first_name, last_name, date_of_birth in %Y/%m/%d format and ramq which should have 4 letters and 8 digits. Make sure you get the right answer in JSON. Do not be verbose."
                response = anthropic_mm_llm.complete(
                    prompt=prompt,
                    image_documents=image_documents,
                )
        except Exception as e:
            raise ValueError(f"Error loading image: {str(e)}")

    else:
        # Process free text input
        prompt = f"Extract the person's full name, date of birth, gender, and RAMQ number from the text and output as JSON using keys first_name, last_name, date_of_birth in %Y/%m/%d format and ramq which should have 4 letters and 8 digits. Make sure you get the right answer in JSON. Do not be verbose. Here is the text: {input_data}"
        response = anthropic_mm_llm.complete(
            prompt=prompt,
            image_documents=None,
        )

    # Parse the JSON response
    import json
    data = json.loads(response.text)
    # Extract date of birth
    dob_str = data["date_of_birth"]
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

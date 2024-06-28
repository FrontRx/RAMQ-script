import os
import re
from datetime import datetime
from typing import Optional
import re
from pydantic import BaseModel, Field


class PersonInfo(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: datetime
    gender: Optional[str] = None
    ramq: str = Field(
        ...,
        pattern=r"^[A-Z]{4}\d{8}$",
        description="RAMQ number in format AAAA00000000",
    )


from dotenv import load_dotenv
from llama_index.multi_modal_llms.anthropic import AnthropicMultiModal

from llama_index.core.multi_modal_llms.generic_utils import load_image_urls
from llama_index.core import SimpleDirectoryReader


# Load environment variables from the .env file in the current directory
load_dotenv()
anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY")

# Initiated Anthropic MultiModal class
anthropic_mm_llm = AnthropicMultiModal(
    max_tokens=300,
    model="claude-3-sonnet-20240229",
    anthropic_api_key=anthropic_api_key,
)


class PersonInfo(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: datetime
    gender: Optional[str] = None
    ramq: str = Field(
        ...,
        pattern=r"^[A-Z]{4}\d{8}$",
        description="RAMQ number in format AAAA00000000",
    )


def get_ramq(input_data, is_image=False):
    if is_image:
        # Load image documents from URLs
        image_documents = load_image_urls([input_data])
        prompt = f"Extract the person's full name, date of birth, gender, and RAMQ number from the image and output as JSON using keys first_name, last_name, date_of_birth in %Y/%m/%d format and ramq which should have 4 letters and 8 digits. Make sure you get the right answer in JSON. Do not be verbose."
        response = anthropic_mm_llm.complete(
            prompt=prompt,
            image_documents=image_documents,
        )
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
    dob = datetime.strptime(data["date_of_birth"], "%Y/%m/%d")

    # Extract gender based on RAMQ
    gender = None
    if "ramq" in data:
        gender_digit = int(data["ramq"][6])
        if gender_digit in [5, 6]:
            gender = "female"
        elif gender_digit in [0, 1]:
            gender = "male"

    return PersonInfo(
        first_name=data["first_name"],
        last_name=data["last_name"],
        date_of_birth=dob,
        gender=gender,
        ramq=data["ramq"],
    )

# Remove the duplicate return statement
# return ramq, last_name, first_name, dob, gender
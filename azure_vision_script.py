import re
from datetime import datetime
from llama_hub.tools.azure_cv.base import AzureCVToolSpec
# Setup OpenAI Agent
import openai
from llama_index.agent import OpenAIAgent
from dotenv import load_dotenv
import os

# Load environment variables from the .env file in the current directory
load_dotenv()

openai.api_key = os.environ.get("OPEN_AI_API_KEY")


def get_ramq(image_url):
    cv_tool = AzureCVToolSpec(
        api_key= os.environ.get("AZURE_API_KEY"),
        resource='frontrx'
    )

    agent = OpenAIAgent.from_tools(
        cv_tool.to_tool_list(),
        verbose=True,
    )

    #Get caption and text from image
    prompt = f"caption this image and read any text {image_url}"
    result = agent.chat(prompt)
    output_text = result.response

    # Regex to extract RAMQ using both patterns
    ramq_patterns = [
        r"([\w]{4}(?:\s[\d]{4}){2})",
        r"([A-Z]{4}\d{8})",
        r"([A-Z]{4})\s*([\d]{8})",
        r"([\w]{4})\s*([\d]{4})\s*([\d]{4})"
    ]
    ramq = None
    for pattern in ramq_patterns:
        ramq_match = re.search(pattern, output_text)
        if ramq_match:
            ramq = ''.join(ramq_match.groups())  # Join all matched groups to form the complete RAMQ
            break
    
    if not ramq:
        raise ValueError("RAMQ not found in the provided image")
    
    # Removing whitespaces from RAMQ
    ramq = ramq.replace(' ', '') if ramq else None

    # Extracting last name and first name from RAMQ
    last_name_prefix = ramq[:3] if ramq else None
    first_name_initial = ramq[3] if ramq else None

    # Split the text into words
    words = re.findall(r'\b\w+\b', output_text)
    # Filter words based on the prefix (case-insensitive) and length criteria
    filtered_words = [word for word in words if word.lower().startswith(last_name_prefix.lower()) and len(word) >= 5]

    # Exclude the RAMQ from the matches
    filtered_words = [word for word in filtered_words if word != ramq]

    # Extract last name if match found
    if len(filtered_words) > 0:
        last_name = filtered_words[0]
        last_name_index = output_text.find(last_name)
    else:
        last_name = None

    # Search for first name
    # Search within 2 words before and after last name
    if (last_name != None):
        first_name_search_text = output_text[max(0,last_name_index-20):last_name_index+20]
        print(first_name_search_text)
        # Find first name starting with first letter 
        first_name_pattern = rf"\b{first_name_initial}[A-Z-]+\w+\b"
        first_name_match = re.search(first_name_pattern, first_name_search_text)
        if first_name_match:
            first_name = first_name_match.group(0)
        else:
            first_name = None
    else:
        first_name = None

    # Extracting the gender using the third number of the RAMQ
    gender_digit = int(ramq[6]) if ramq else None
    if gender_digit in [5, 6]:
        gender = 'female'
        birth_month_first_digit = str(gender_digit - 5)
    elif gender_digit in [0, 1]:
        gender = 'male'
        birth_month_first_digit = str(gender_digit)
    else:
        gender = 'other'
        birth_month_first_digit = '0'

    # Extracting birth year, month, and day from RAMQ
    birth_year_suffix = ramq[4:6]

    birth_month_second_digit = ramq[7] if ramq else '0'  # The original second digit of the birth month
    birth_month = int(birth_month_first_digit + birth_month_second_digit)

    birth_day = int(ramq[8:10])  # Convert to integer to remove leading zero

    # Assuming the 20th century unless the patient is 90 years of age or older
    current_year = datetime.today().year
    century_prefix = '19' if (current_year - int('19' + birth_year_suffix)) < 90 else '20'

    birth_year = century_prefix + birth_year_suffix
    dob = f"{birth_year}-{birth_month}-{birth_day}"

    return ramq, last_name, first_name, dob, gender

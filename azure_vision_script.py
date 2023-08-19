import re
from datetime import datetime
from llama_hub.tools.azure_cv.base import AzureCVToolSpec
# Setup OpenAI Agent
import openai
openai.api_key = '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'
from llama_index.agent import OpenAIAgent

def get_ramq(image_url):
    cv_tool = AzureCVToolSpec(
        api_key='72223d70f92e45a2a7579a123f244587',
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
        r"([A-Z]{4}\d{8})"
    ]
    ramq = None
    for pattern in ramq_patterns:
        ramq_match = re.search(pattern, output_text)
        if ramq_match:
            ramq = ramq_match.group(1)
            break
    
    if not ramq:
        raise ValueError("RAMQ not found in the provided image")
    
    # Removing whitespaces from RAMQ
    ramq = ramq.replace(' ', '') if ramq else None

    # Extracting last name and first name from RAMQ
    last_name_prefix = ramq[:3] if ramq else None
    first_name_initial = ramq[3] if ramq else None


    # Find the full last name in the output text starting with the last_name_prefix
    last_name_pattern = rf"\b{last_name_prefix}[A-Z-]+\b"
    last_name_match = re.search(last_name_pattern, output_text)
    last_name = last_name_match.group(0) if last_name_match else None

     # Finding the index after the last name appears in the output text
    last_name_index = output_text.find(last_name) + len(last_name)

    # Extracting the first character of the first name from RAMQ
    first_name_prefix = ramq[3] if ramq else None

    # Finding the first occurrence of a name after the last name index, starting with the first_name_prefix
    first_name_pattern = rf"\b{first_name_prefix}[A-Z-]+\b"
    first_name_match = re.search(first_name_pattern, output_text[last_name_index:])
    first_name = first_name_match.group(0) if first_name_match else None

    # Extracting the gender using the third number of the RAMQ
    gender_digit = int(ramq[6]) if ramq else None
    if gender_digit in [5, 6]:
        gender = 'Female'
        birth_month_first_digit = str(gender_digit - 5)
    elif gender_digit in [0, 1]:
        gender = 'Male'
        birth_month_first_digit = str(gender_digit)
    else:
        gender = 'Unknown'
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

# Usage
image_url = "https://i.ibb.co/4VyHrkV/Screenshot-2023-08-15-at-10-52-28-PM.png"
try:
    ramq, last_name, first_name, dob, gender = get_ramq(image_url)
    print(f"RAMQ: {ramq}")
    print(f"Last Name: {last_name}")
    print(f"First Name: {first_name}")
    print(f"Date of Birth: {dob}")
    print(f"Date of Birth: {gender}")
except ValueError as e:
    print(e)

# In case the RAMQ is not found, it will print the error message


import argparse

def main():
    parser = argparse.ArgumentParser(description='Get RAMQ details from an image URL.')
    parser.add_argument('image_url', type=str, help='The URL of the image to process.')
    args = parser.parse_args()

    try:
        ramq, last_name, first_name, dob, gender = get_ramq(args.image_url)
        print(f"RAMQ: {ramq}")
        print(f"Last Name: {last_name}")
        print(f"First Name: {first_name}")
        print(f"Date of Birth: {dob}")
        print(f"Gender: {gender}")
    except ValueError as e:
        print(e)

if __name__ == "__main__":
    main()

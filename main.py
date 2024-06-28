from anthropic_vision_script import get_ramq
import argparse

def main():
    parser = argparse.ArgumentParser(description='Get RAMQ details from an image URL or text.')
    parser.add_argument('input', type=str, help='The URL of the image or text to process.')
    parser.add_argument('--is_image', type=str, required=False, help='Specify if the input is an image URL (True/False).')
    args = parser.parse_args()
    # Determine if input_data is an image URL or a string
    if args.is_image is None:
        import re
        url_pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
        is_image = bool(url_pattern.match(args.input))
    else:
        is_image = args.is_image.lower() == 'true'

    try:
        is_image = args.is_image.lower() == 'true'
        person_info = get_ramq(args.input, is_image)
        print(f"RAMQ: {person_info.ramq}")
        print(f"Last Name: {person_info.last_name}")
        print(f"First Name: {person_info.first_name}")
        print(f"Date of Birth: {person_info.date_of_birth}")
        print(f"Gender: {person_info.gender}")
    except ValueError as e:
        print(e)

if __name__ == "__main__":
    main()
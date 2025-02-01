from anthropic_vision_script import get_ramq, get_patient_list
import argparse

def main():
    parser = argparse.ArgumentParser(description='Get RAMQ details or patient list from an image URL or text.')
    parser.add_argument('input', type=str, help='The URL of the image or text to process.')
    parser.add_argument('--is_image', type=str, required=False, help='Specify if the input is an image URL (True/False).')
    parser.add_argument('--mode', type=str, choices=['ramq', 'list'], default='ramq',
                      help='Mode of operation: ramq (get RAMQ details) or list (get patient list)')
    args = parser.parse_args()

    # Determine if input_data is an image URL or a string
    if args.is_image is None:
        import re
        url_pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
        is_image = bool(url_pattern.match(args.input))
    else:
        is_image = args.is_image.lower() == 'true'

    try:
        if args.mode == 'ramq':
            ramq, last_name, first_name, dob, gender, is_valid = get_ramq(args.input, is_image)
            print(f"RAMQ: {ramq}")
            print(f"Last Name: {last_name}")
            print(f"First Name: {first_name}")
            print(f"Date of Birth: {dob}")
            print(f"Gender: {gender}")
            print(f"Valid: {is_valid}")
        else:
            patients = get_patient_list(args.input, is_image)
            print("\nPatient List:")
            for patient in patients:
                print(f"\nName: {patient.get('first_name')} {patient.get('last_name')}")
                if patient.get('patient_number'):
                    print(f"Patient Number: {patient['patient_number']}")
                if patient.get('room_number'):
                    print(f"Room Number: {patient['room_number']}")
    except ValueError as e:
        print(e)

if __name__ == "__main__":
    main()
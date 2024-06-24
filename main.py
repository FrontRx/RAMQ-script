from anthropic_vision_script import get_ramq
import argparse

# Usage
# image_url = "https://i.ibb.co/4VyHrkV/Screenshot-2023-08-15-at-10-52-28-PM.png"
# try:
#     ramq, last_name, first_name, dob, gender = get_ramq(image_url)
#     print(f"RAMQ: {ramq}")
#     print(f"Last Name: {last_name}")
#     print(f"First Name: {first_name}")
#     print(f"Date of Birth: {dob}")
#     print(f"Gender: {gender}")
# except ValueError as e:
#     print(e)

# # In case the RAMQ is not found, it will print the error message

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
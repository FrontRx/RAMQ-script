
# Azure Vision RAMQ Extractor

This script extracts RAMQ (Régie de l'assurance maladie du Québec) details from an image URL using Anthropic Claude SONNET v3.0.

## Requirements

- Python 3.x
- LlamaIndex
- LlamaIndex MultiModal Anthropic

## Installation

1. Clone the repository or download the script.
2. Install the required dependencies:

   ```bash
   pip install -r requirements.txt
   ```

   **Note:** You may need to create a `requirements.txt` file listing all necessary packages or install them manually.

## Usage

Run the script with the image URL as a command-line argument:

```bash

python3 main.py "https://example.com/path/to/image.png"
```

Replace the URL with the actual image URL you want to process.

## Data

The script will print the following details:

- RAMQ
- Last Name
- First Name
- Date of Birth
- Gender
- Is RAMQ vlaid (true or false)

## Deployment as REST API

- pip3 install virtualenv
- python3 -m venv env
- . env/bin/activate
- pip3 install Flask
- pip3 install -r requirements.txt
- export FLASK_APP=api.py
- export FLASK_ENV=development
- flask run
- . env/bin/deactivate

## Troubleshooting

If you encounter any issues, please check the dependencies and ensure you are using a valid image URL.

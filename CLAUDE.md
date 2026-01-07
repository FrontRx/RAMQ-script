# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

RAMQ (Régie de l'assurance maladie du Québec) health card information extractor. Uses Google Gemini AI for OCR to extract patient information from Quebec health card images.

## Commands

### Install dependencies
```bash
pip install -r requirements.txt
```

### Run tests
```bash
python -m pytest test_ramq_github.py -v
```

### Run tests with coverage
```bash
python -m pytest test_ramq_github.py -v --cov=./ --cov-report=xml
```

### Run Flask API server
```bash
flask run
# Or directly:
python api.py  # Runs on port 9000
```

### Run CLI
```bash
python main.py "https://example.com/image.jpg"           # RAMQ extraction from image URL
python main.py "text with RAMQ" --is_image False         # RAMQ extraction from text
python main.py "https://example.com/image.jpg" --mode list  # Patient list extraction
```

## Architecture

- **anthropic_vision_script.py** - Core extraction logic (name is historical; uses Gemini API, not Anthropic)
  - `get_ramq(input_data, is_image)` - Extract RAMQ from image URL or text, returns tuple: (ramq, last_name, first_name, dob, gender, is_valid)
  - `validate_ramq(ramq)` - Validate RAMQ check digit using EBCDIC character mapping and weighted sum algorithm
  - `get_patient_list(input_data, is_image)` - Extract list of patients from image/text
  - `resize_image(image_data)` - Resize images exceeding 5MB limit

- **api.py** - Flask REST API with token-based auth (`RAMQ-Billr-API-Key` header)
  - `POST /extract_json_from_image` - Extract RAMQ from image URL or text
  - `GET /validate_ramq?ramq=` - Validate RAMQ number

- **main.py** - CLI entry point with argparse

## Environment Variables

Copy `.env.example` to `.env` and configure:
- `GEMINI_API_KEY` - Google Gemini API key (required)
- `HEADER_TOKEN` - API authentication token for Flask endpoints

## RAMQ Format

RAMQ numbers are 12 characters: 4 letters + 8 digits (e.g., `ABCD12345678`)
- First 3 letters: Last name prefix
- 4th letter: First name initial
- Digits 5-6: Birth year (YY)
- Digits 7-8: Birth month (MM; add 50 for females)
- Digits 9-10: Birth day (DD)
- Digit 11: Sequence number
- Digit 12: Check digit (validated via `validate_ramq()`)

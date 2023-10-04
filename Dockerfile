# Use the official Python image as the base image
FROM python:3.11.5

# Set the working directory in the container
WORKDIR /app

# Create a virtual environment and activate it
RUN python3 -m venv env
RUN . env/bin/activate

# Install Flask and any other dependencies
RUN pip3 install Flask
COPY requirements.txt /app
RUN pip3 install -r requirements.txt

# Set environment variables
ENV FLASK_APP=api.py
ENV FLASK_ENV=development

# Expose port 9000 for Flask
EXPOSE 9000

# Copy your application code into the container
COPY . /app

# Start the Flask app
CMD ["flask", "run","--host=0.0.0.0","--port=9000"]

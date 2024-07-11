# Use the official Python image as the base image
FROM python:3.11.5

# Set the working directory in the container
WORKDIR /app/build

# Create a virtual environment and activate it
RUN python3 -m venv env
RUN . env/bin/activate

# Install Flask and any other dependencies
RUN pip3 install Flask
COPY requirements_docker.txt /app/build
RUN pip3 install -r requirements_docker.txt

# Expose port 10000 for Flask
EXPOSE 10000

# Copy your application code into the container
COPY . /app/build

# Start the Flask app
CMD ["flask", "run","--host=0.0.0.0","--port=10000"]

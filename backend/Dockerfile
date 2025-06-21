# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Create a virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the backend application code
COPY . .

# The container will listen on this port
EXPOSE 5001

# Run the web server using Gunicorn
# Use sh -c to allow environment variable expansion for $PORT
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT:-5001} --timeout 300 'main:create_app()'"] 
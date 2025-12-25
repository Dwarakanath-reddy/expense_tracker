# Use an official Python runtime as a parent image
FROM PYTHON:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all source files
COPY . .

# Expose the port your Flask app runs on
EXPOSE 5000

# Run the app
CMD ["python", "app.py"]

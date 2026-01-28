# Use Python base image
FROM python:3.11-slim

# Set work directory
WORKDIR /app

# Copy dependency list
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your code
COPY . .

# Create logs directory
RUN mkdir -p /app/logs

# Expose port
EXPOSE 8000

# Start app with proper user permissions
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

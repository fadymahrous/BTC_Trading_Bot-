# Base image
FROM python:3.11

# Set working directory
WORKDIR /app

# Copy all relevant files/folders
COPY Config/ Config/
COPY Core_Trade/ Core_Trade/
COPY Data/ Data/
COPY Helper/ Helper/
COPY Infrastructure/ Infrastructure/
COPY logs/ logs/
COPY main.py ./
COPY Requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r Requirements.txt

# Default command (can be overridden)
CMD ["python", "main.py"]


#When you run a container from this image be sure to use -e db_endpoint=<AWS database endpoint> as the script use this environmental variable
#docker build --build-arg DB_HOST=<DNS> -t my-image .

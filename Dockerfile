FROM python:3.10

# Set working directory
WORKDIR /usr/src/app

# Install dependencies
COPY requirements.txt /usr/src/app/requirements.txt
RUN ["pip3", "install", "--no-cache-dir", "-r", "requirements.txt"]

# Copy all bot code over
COPY . .

# Run the bot when container is run
CMD ["python3", "-u", "bot.py"]

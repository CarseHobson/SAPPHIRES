import time
import RPi.GPIO as GPIO
import json
import os
from sps30 import SPS30  # Import the proper library

# Initialize GPIO for relay control
RELAY_PIN = 19
GPIO.setmode(GPIO.BCM)
GPIO.setup(RELAY_PIN, GPIO.OUT)

# Initialize SPS30 sensor
sps = SPS30(1)  # I2C interface, address 0x69

# Define constants
BASELINE_DURATION = 30 * 60  # 30 minutes for baseline
WINDOW_DURATION = 10 * 60  # 10 minutes for each window
BASELINE_THRESHOLD = 0.1  # 10% of baseline value

# File path for JSON data log
LOG_FILE_PATH = "sps30_data.json"

# Function to create the JSON file if it doesn't exist
def create_json_file():
    if not os.path.exists(LOG_FILE_PATH):
        with open(LOG_FILE_PATH, "w") as json_file:
            json_file.write("[]")  # Create an empty JSON array

# Function to generate a random 8-character alphanumeric key for each entry
def generate_random_key():
    import string
    import secrets
    characters = string.ascii_letters + string.digits
    return ''.join(secrets.choice(characters) for _ in range(8))

# Function to log data (including relay state) to the JSON file
def log_data(data, relay_state):
    try:
        with open(LOG_FILE_PATH, "a") as json_file:
            for entry in data:
                entry_with_timestamp_and_key = {
                    "timestamp": int(time.time()),  # Add UNIX timestamp
                    "key": generate_random_key(),  # Generate a new random key for each entry
                    "pm2_5": entry['pm2_5'],
                    "relay_state": relay_state
                }
                json_file.write(json.dumps(entry_with_timestamp_and_key) + "\n")
    except Exception as e:
        print(f"Error writing to JSON file: {str(e)}")

# Function to check for rising edges
def check_rising_edge():
    baseline_data = []
    start_time = time.time()
    baseline_finished = False
    relay_state = GPIO.LOW  # Initialize relay state to off

    while True:
        if time.time() - start_time < BASELINE_DURATION:
            # Collect baseline data
            sps.start_measurement()
            time.sleep(2.5)  # Wait for the measurement to complete
            data = sps.query()
            if data:
                baseline_data.append(data)
        else:
            if not baseline_finished:
                # Calculate the baseline value as the average
                baseline_pm2_5 = sum([entry['pm2_5'] for entry in baseline_data]) / len(baseline_data)
                print(f"Baseline PM2.5: {baseline_pm2_5} µg/m³")
                baseline_finished = True

            # Start monitoring for rising edges
            window_start_time = time.time()
            window_data = []

            while time.time() - window_start_time < WINDOW_DURATION:
                sps.start_measurement()
                time.sleep(2.5)  # Wait for the measurement to complete
                data = sps.query()
                if data:
                    window_data.append(data)

                # Calculate the average PM2.5 for the current window
                window_pm2_5 = sum([entry['pm2_5'] for entry in window_data]) / len(window_data)

                # Check if the average exceeds the threshold
                if window_pm2_5 > baseline_pm2_5 * (1 + BASELINE_THRESHOLD):
                    print(f"Rising edge detected! PM2.5: {window_pm2_5} µg/m³")
                    GPIO.output(RELAY_PIN, GPIO.HIGH)  # Turn on the relay
                    relay_state = GPIO.HIGH
                else:
                    GPIO.output(RELAY_PIN, GPIO.LOW)  # Turn off the relay
                    relay_state = GPIO.LOW

                # Log the data (including relay state) to the JSON file
                log_data(window_data, relay_state)

            # Wait for a while before starting the next window
            time.sleep(10)

# Start monitoring for rising edges
if __name__ == "__main__":
    create_json_file()  # Create the JSON file if it doesn't exist
    check_rising_edge()

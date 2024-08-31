import os
import csv
import requests
import bittensor as bt


# Base URL for downloading images (replace with actual base URL)
BASE_URL = "http://localhost:8001/"
API_GET_IMAGES = "dataset/skin/melanoma?amount=10"

# Create the images directory
os.makedirs("images", exist_ok=True)

# Open the CSV file for writing
with open("labels.csv", mode="w", newline="") as csv_file:
    csv_writer = csv.writer(csv_file)
    # Write the header row
    csv_writer.writerow(["path", "is_melanoma"])
    data = requests.get(BASE_URL + API_GET_IMAGES).json()
    # Process each entry in the JSON data
    for entry in data["entries"]:
        image_id = entry["id"]
        image_url = BASE_URL + entry["image_url"]
        is_melanoma = entry["label"]["melanoma"]

        # Define the local file path
        image_filename = f"images/{image_id}.jpg"

        # Download the image
        response = requests.get(image_url)
        if response.status_code == 200:
            with open(image_filename, "wb") as image_file:
                image_file.write(response.content)
            bt.logging.info(f"Downloaded {image_filename}")
        else:
            bt.logging.info(f"Failed to download {image_filename}")

        # Write the image path and label to the CSV file
        csv_writer.writerow([image_filename, is_melanoma])

print("Process completed.")

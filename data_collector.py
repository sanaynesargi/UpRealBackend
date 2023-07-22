import requests
import os
import json
import pandas as pd
import time

# ATTOM API base URLs
property_url = "https://api.gateway.attomdata.com/propertyapi/v1.0.0/property/address"
avm_url = "https://api.gateway.attomdata.com/propertyapi/v1.0.0/avm/detail"

# Replace with your ATTOM API key
api_key = "2b1e86b638620bf2404521e6e9e1b19e"

# List of ZIP codes in the DFW area
dfw_zip_codes = [75201, 75202, 75203, 75204, 75205, 75206, 75207, 75208, 75209, 75210, 75211, 75212, 75214, 75215, 75216, 75217, 75218, 75219, 75220, 75221, 75222, 75223, 75224, 75225, 75226, 75227, 75228, 75229, 75230, 75231, 75232, 75233, 75234, 75235, 75236, 75237, 75238, 75239, 75240, 75241, 75242, 75243, 75244, 75245, 75246, 75247, 75248, 75249, 75250, 75251, 75252, 75253, 75258, 75260, 75261, 75262, 75263, 75264, 75265,
                 75266, 75267, 75270, 75275, 75277, 75283, 75284, 75285, 75286, 75287, 75294, 75295, 75301, 75303, 75310, 75312, 75313, 75315, 75320, 75323, 75326, 75336, 75339, 75342, 75346, 75350, 75353, 75354, 75355, 75356, 75357, 75359, 75360, 75363, 75364, 75367, 75368, 75370, 75371, 75372, 75373, 75374, 75376, 75378, 75379, 75380, 75381, 75382, 75386, 75387, 75388, 75389, 75390, 75391, 75392, 75393, 75394, 75395, 75396, 75397, 75398]

# Function to fetch properties from a given ZIP code


def fetch_properties_by_zip(zip_code):
    headers = {
        "accept": "application/json",
        "apikey": api_key
    }
    params = {
        "postalcode": zip_code
    }
    response = requests.get(property_url, headers=headers, params=params)

    if response.status_code == 200:
        return response.json()
    else:
        print(
            f"Error fetching properties for ZIP code {zip_code}: {response.status_code}")
        return None

# Function to fetch AVM data for a property using its ATTOM ID


def fetch_avm_data(attom_id):
    headers = {
        "accept": "application/json",
        "apikey": api_key
    }
    params = {
        "attomId": attom_id
    }
    response = requests.get(avm_url, headers=headers, params=params)

    if response.status_code == 200:
        return response.json()
    else:
        print(
            f"Error fetching AVM data for ATTOM ID {attom_id}: {response.status_code}")
        return None


# Create a directory to store JSON files
output_directory = "property_data"
if not os.path.exists(output_directory):
    os.makedirs(output_directory)

# Loop through each ZIP code and store the property data in JSON files
for zip_code in dfw_zip_codes:
    properties_data = fetch_properties_by_zip(zip_code)
    if properties_data:
        for property_info in properties_data["property"]:
            attom_id = property_info["identifier"]["attomId"]
            avm_data = fetch_avm_data(attom_id)
            # print(avm_data["property"][0]["summary"].keys())
            if avm_data:
                property_info = [avm_data, property_info]
            else:
                continue
            file_path = os.path.join(output_directory, f"{attom_id}.json")
            print(property_info)
            with open(file_path, "w") as json_file:
                json.dump(property_info, json_file, indent=2)
            # Sleep for 0.1 seconds to stay below 10 hits per second
            time.sleep(0.1 * 60)

print("Data retrieval and storage complete.")

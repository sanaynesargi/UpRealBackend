import requests
import os
import json
import pandas as pd
import numpy as np
import random
import time
from statistics import mean
from config import api_key
from google.cloud import aiplatform
import vertexai
from vertexai.preview.language_models import TextGenerationModel
from google.cloud import storage
from google.oauth2 import service_account

# ATTOM API base URLs
property_url = "https://api.gateway.attomdata.com/propertyapi/v1.0.0/property/address"
avm_url = "https://api.gateway.attomdata.com/propertyapi/v1.0.0/avm/detail"


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


def get_school_data(latitude, longitude):
    endpoint = "https://api.gateway.attomdata.com/v4/school/search"

    headers = {
        'accept': 'application/json',
        'apikey': api_key
    }

    params = {
        'latitude': latitude,
        'longitude': longitude,
        'radius': 5,
        'pageSize': 10,
        'page': 1,
    }

    try:
        response = requests.get(endpoint, headers=headers, params=params)

        # Check if the request was successful
        if response.status_code == 200:
            school_data = response.json()
            # Process the school data as needed
            return school_data
        else:
            print(f"Request failed with status code: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error occurred: {e}")
        return None

# TODO: KEEPING AS TEMP FOR NOW


def get_crime_rate(zip):
    url = "https://crime-data-by-zipcode-api.p.rapidapi.com/crime_data"

    if os.path.exists("./crime_data.json"):
        with open("./crime_data.json", "r") as d:
            return json.load(d)

    querystring = {"zip": str(zip)}

    headers = {
        "X-RapidAPI-Key": "b0939172dcmsh3c3cc8319112577p1e7f18jsncec3d909315d",
        "X-RapidAPI-Host": "crime-data-by-zipcode-api.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)

    with open("./crime_data.json", "w") as d:
        json.dump(response, d)

    return response.json()


def get_vacancy_data():

    return {
        "Homeowner Vacancy Rate": np.random.normal(0.9, 0.7/2),
        "Rental Vacancy Rate": np.random.normal(10.8, 2.6/2)
    }


def get_appreciation_data():
    vals = [[-0.4, 3.1, 34.45], [0.68, 8.58, 57.73]]

    chosen = random.choice(vals)

    return {
        "Appeciation Last Q": chosen[0],
        "Appreciation Past Year": chosen[1],
        "Appreciation Past 5 Years": chosen[2]
    }


def get_attom_id_by_address(address_line_1, address_line_2):
    params = {
        "address1": address_line_1,
        "address2": address_line_2,
    }

    headers = {
        "apikey": api_key,
    }

    try:
        response = requests.get(
            "https://api.gateway.attomdata.com/propertyapi/v1.0.0/property/basicprofile", params=params, headers=headers)
        response.raise_for_status()  # Check for errors

        data = response.json()

        # Assuming the API response returns a JSON object with 'attom_id' field
        attom_id = data["property"][0]["identifier"]["attomId"]
        zip_code = data["property"][0]["address"]["postal1"]
        lat, lon = data["property"][0]["location"]["latitude"],  data["property"][0]["location"]["longitude"]
        return attom_id, zip_code, lat, lon

    except requests.exceptions.RequestException as e:
        print("Error making the request:", e)
        return None


def cleanup_data():

    grade_scale = {
        "A+": 100,
        "A ":
        95,
        "A-":
        91.25,
        "B+":
        88.75,
        "B ":
        85,
        "B-":
        81.25,
        "C+":
        78.75,
        "C ":
        75,
        "C-":
        71.25,
        "D+":
        68.75,
        "D ":
        65,
        "D-":
        61.25,
        "F ":
        55,
    }

    for fname in os.listdir("./property_data"):
        with open(f"./property_data/{fname}", "r") as d:
            json_data = json.load(d)

            if json_data[2].get("Overall"):
                school_ratings = []

                for x in json_data[5]["schools"]:
                    if x["detail"].get("schoolRating"):
                        school_ratings.append(
                            grade_scale[x["detail"]["schoolRating"]])

                kept_data = {
                    "Year Built": json_data[1]["property"][0]["summary"]["yearbuilt"],
                    "Lot Info": json_data[1]["property"][0]["lot"],
                    "Building Info": json_data[1]["property"][0]["building"],
                    "Valuation": json_data[1]["property"][0]["avm"],
                    "Crime Grade": json_data[2]["Overall"]["Overall Crime Grade"],
                    "Vacancy Rates": {
                        "Homeowner Vacancy Rate": json_data[3]["Homeowner Vacancy Rate"],
                        "Rental Vacancy Rate": json_data[3]["Rental Vacancy Rate"]
                    },
                    "Appreciation": {
                        "Appeciation Last Q": json_data[4]["Appeciation Last Q"],
                        "Appreciation Past Year": json_data[4]["Appreciation Past Year"],
                        "Appreciation Past 5 Years": json_data[4]["Appreciation Past 5 Years"]
                    },
                    "Avg. School Rating": mean(school_ratings),
                }
            else:
                school_ratings = []

                for x in json_data[2]["schools"]:
                    if x["detail"].get("schoolRating"):
                        school_ratings.append(
                            grade_scale[x["detail"]["schoolRating"]])

                kept_data = {
                    "Year Built": json_data[1]["property"][0]["summary"]["yearbuilt"],
                    "Lot Info": json_data[1]["property"][0]["lot"],
                    "Building Info": json_data[1]["property"][0]["building"],
                    "Valuation": json_data[1]["property"][0]["avm"],
                    "Crime Grade": json_data[3]["Overall"]["Overall Crime Grade"],
                    "Vacancy Rates": {
                        "Homeowner Vacancy Rate": json_data[4]["Homeowner Vacancy Rate"],
                        "Rental Vacancy Rate": json_data[4]["Rental Vacancy Rate"]
                    },
                    "Appreciation": {
                        "Appeciation Last Q": json_data[5]["Appeciation Last Q"],
                        "Appreciation Past Year": json_data[5]["Appreciation Past Year"],
                        "Appreciation Past 5 Years": json_data[5]["Appreciation Past 5 Years"]
                    },
                    "Avg. School Rating": mean(school_ratings),
                }

        with open(f"./dataset/{fname}", "w") as d:
            json.dump(kept_data, d)


def iterdict(d, lst):
    for k, v in d.items():
        if isinstance(v, dict):
            iterdict(v, lst)
        else:
            if "avm" not in k and k != 'value' and "size" not in k:
                lst.append(f"{k}: {v}")

    return lst


def get_model_data(address1, address2):
    data = get_attom_id_by_address(
        address1, address2)

    if not data:
        return None

    attom_id, zip_code, lat, lon = data

    grade_scale = {
        "A+": 100,
        "A ":
            95,
            "A-":
            91.25,
            "B+":
            88.75,
            "B ":
            85,
            "B-":
            81.25,
            "C+":
            78.75,
            "C ":
            75,
            "C-":
            71.25,
            "D+":
            68.75,
            "D ":
            65,
            "D-":
            61.25,
            "F ":
            55,
    }

    try:
        json_data = [
            [],
            fetch_avm_data(attom_id),
            get_crime_rate(zip_code),
            get_vacancy_data(),
            get_appreciation_data(),
            get_school_data(lat, lon)
        ]

        school_ratings = []

        for x in json_data[5]["schools"]:
            if x["detail"].get("schoolRating"):
                school_ratings.append(
                    grade_scale[x["detail"]["schoolRating"]])

        kept_data = {
            "Year Built": json_data[1]["property"][0]["summary"]["yearbuilt"],
            "Lot Info": json_data[1]["property"][0]["lot"],
            "Building Info": json_data[1]["property"][0]["building"],
            "Valuation": json_data[1]["property"][0]["avm"],
            "Crime Grade": json_data[2]["Overall"]["Overall Crime Grade"],
            "Vacancy Rates": {
                "Homeowner Vacancy Rate": json_data[3]["Homeowner Vacancy Rate"],
                "Rental Vacancy Rate": json_data[3]["Rental Vacancy Rate"]
            },
            "Appreciation": {
                "Appeciation Last Q": json_data[4]["Appeciation Last Q"],
                "Appreciation Past Year": json_data[4]["Appreciation Past Year"],
                "Appreciation Past 5 Years": json_data[4]["Appreciation Past 5 Years"]
            },
            "Avg. School Rating": mean(school_ratings),
        }

        return ", ".join(iterdict(kept_data, []))
    except Exception:
        return None


def get_model_response(test_in):

    with open('./credentials.json') as source:
        info = json.load(source)

    storage_credentials = service_account.Credentials.from_service_account_info(
        info)

    vertexai.init(project="doorbell-identification",
                  location="us-central1", credentials=storage_credentials)

    model = TextGenerationModel.from_pretrained("text-bison@001")

    parameters = {
        "temperature": 0.2,
        "max_output_tokens": 256,
        "top_p": 0.9,
        "top_k": 40,
    }
    model = TextGenerationModel.from_pretrained("text-bison@001")

    context = """You are a ratings engine, you receive property data and evaluate it to determine two ratings make sure you evaluate all the data,
    - a flip score to represent how good of a flip property the property is (from 1-5)
    - a rent score to represent how good of a rent property the property is (from 1-5)
                Here are a few tips to help:
                    - Vacancy rates determine how many houses in the area are vacant, so if this is low, then make your rating higher
                    - Even if the vacancy rate is high, the amount of bedrooms and bathrooms should impact your rating, with more of them leading to higher ratings
                    - Take crime rate into account as well as it affects rental properties more, a higher crime rate should lead to a slightly lower rating
                    - If the nearby schools are good (above 70), then give the ratings a slight boost
                    - If the property is a HIGH QUALITY RESEDENTIAL then give the rating a significant boost
                    - Bedrooms and Bathrooms dont matter as much for rental properties so you can lower their affect on rental ratings
                    - Make sure you judge only housing vacancy rates for the flip score and only the rental vacancy rate for the rent score
    """

    lines_list = []

    with open("./training_data.jsonl") as data:
        lines = data.readlines()

        for line in lines[:-11]:
            line = line.rstrip()
            json_line = json.loads(line)

            input_text_formatted = json.loads(json_line["input_text"].split(
                ". Data: ")[-1])

            input_text = "Data: " + \
                ', '.join(iterdict(input_text_formatted, []))
            output_text = json_line["output_text"]

            context += f"\n\n{input_text}\nRating: {output_text}"

            # lines_list.append((input_text, output_text))

        for line in lines[-11:]:
            line = line.rstrip()
            json_line = json.loads(line)

            input_text_formatted = json.loads(json_line["input_text"].split(
                ". Data: ")[-1])

            input_text = "Data: " + \
                ', '.join(iterdict(input_text_formatted, []))
            output_text = json_line["output_text"]

            lines_list.append((input_text, output_text))

    context += f"\n\n{test_in}\nRating:\n"

    try:
        response = model.predict(context, **parameters)

        model_flip_rating = float(response.text.split(" ")[2].split("/")[0])
        model_rent_rating = float(response.text.split(" ")[-1].split("/")[0])

        return {"Flip Score": model_flip_rating, "Rent Score": model_rent_rating}
    except Exception as e:
        print(e)
        return None

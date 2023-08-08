import json
import os
import requests
from tables.profiles.FixFlipProfile import FixFlipProfile
from tables.profiles.RentProfile import RentProfile
from statistics import mean
from random import randint


def percentage_maxmin(max, min, value):
    return ((value - min) * 100) / (max - min)


def make_prop_request():
    if not os.path.exists("cache_response.json"):
        url = "https://realty-in-us.p.rapidapi.com/properties/v3/list"

        payload = {
            "limit": 200,
            "offset": 0,
            "postal_code": "75077",  # zip,
            "status": ["for_sale"],
            "sort": {
                "direction": "desc",
                "field": "list_date"
            }
        }
        headers = {
            "content-type": "application/json",
            "X-RapidAPI-Key": "b0939172dcmsh3c3cc8319112577p1e7f18jsncec3d909315d",
            "X-RapidAPI-Host": "realty-in-us.p.rapidapi.com"
        }

        response = requests.post(url, json=payload, headers=headers)
        response = response.json()

        with open("cache_response.json", "w") as js:
            json.dump(response, js)
    else:
        with open("cache_response.json", "r") as js:
            response = json.load(js)

    results = response["data"]["home_search"]["results"]
    listing_data = {}

    for result in results:
        property_id = result["property_id"]
        listing_data[property_id] = {}

        advertising_info = result["advertisers"]
        property_description = result["description"]
        estimate_data = result["estimate"]
        location_data = result["location"]

        listing_data[property_id]["seller_info"] = []
        listing_data[property_id]["property_description"] = {}
        listing_data[property_id]["current_estimate"] = None
        listing_data[property_id]["listing_information"] = {}
        listing_data[property_id]["location"] = {}
        listing_data[property_id]["photo"] = None
        listing_data[property_id]["virtual_tours"] = []
        listing_data[property_id]["mls_listing"] = result["href"]

        if not advertising_info:
            continue

        for advertiser in advertising_info:
            seller_name = advertiser["name"]
            seller_link = advertiser["href"]
            seller_email = advertiser["email"]

            listing_data[property_id]["seller_info"].append({
                "name": seller_name,
                "link": seller_link,
                "email": seller_email,
            })

        listing_data[property_id]["property_description"] = {
            "baths": property_description["baths"],
            "beds": property_description["beds"],
            "type": property_description["type"],
            "lot_sqft": property_description["lot_sqft"],
            "prop_sqft": property_description["sqft"],
        }

        if estimate_data:
            listing_data[property_id]["current_estimate"] = estimate_data["estimate"]

        listing_data[property_id]["listing_information"] = {
            "list_date": result["list_date"],
            "list_price": result["list_price"],
            "last_sold": result["last_sold_date"],
            "last_sold_price": result["last_sold_price"],
            "flags": {f: flag for f, flag in result["flags"].items() if f != "__typename"},
        }

        if location_data:
            listing_data[property_id]["location"] = {
                "city": location_data["address"]["city"],
                "zip_code": location_data["address"]["postal_code"],
                "state": location_data["address"]["state"],
                "state_code": location_data["address"]["state_code"],
                "line": location_data["address"]["line"],
                "street_name": location_data["address"]["street_name"],
                "street_number": location_data["address"]["street_number"]
            }

            if location_data["address"]["coordinate"]:
                listing_data[property_id]["location"]["coordinates"] = {
                    "lat": location_data["address"]["coordinate"]["lat"],
                    "lon": location_data["address"]["coordinate"]["lon"]
                },

        if result["primary_photo"]:
            photo_url_encoded = result["primary_photo"]["href"]
            photo_url_body = photo_url_encoded.split(".jpg")[0]
            photo_url_lg = photo_url_body[:-1] + "od"
            photo_url_decoded = photo_url_lg + ".jpg"

            listing_data[property_id]["photo"] = photo_url_decoded

        if result["virtual_tours"]:
            listing_data[property_id]["virtual_tours"] = [
                tour["href"] for tour in result["virtual_tours"]
            ]

    return listing_data


def profile_fit_rank_test(profile):
    return randint(1, 100)


def profile_fit_rank_rent(profile: RentProfile, listing_price, app_rate, cash_flow, coc, maintentance_spend, rent_score):

    rank_factors = [
        percentage_maxmin(profile.budget_high,
                          profile.budget_low, listing_price),
        percentage_maxmin(profile.appreciation_high,
                          profile.appreciation_low, app_rate),
        percentage_maxmin(profile.cashflow_high,
                          profile.cashflow_low, cash_flow),
        percentage_maxmin(profile.coc_high, profile.coc_low, coc),
        percentage_maxmin(profile.main_high,
                          profile.main_low, maintentance_spend),
    ]

    avg = mean(rank_factors)

    return avg * (percentage_maxmin(5, 1, rent_score)/100)


def profile_fit_rank_flip(profile: FixFlipProfile, listing_price, repair_costs, coc, market_value, flip_score):

    rank_factors = [
        percentage_maxmin(profile.budget_high,
                          profile.budget_low, listing_price),
        percentage_maxmin(profile.repair_cost_high,
                          profile.repair_cost_low, repair_costs),
        percentage_maxmin(profile.coc_high, profile.coc_low, coc),
        percentage_maxmin(profile.after_repair_high,
                          profile.after_repair_low, market_value)
    ]

    avg = mean(rank_factors)

    return avg * (percentage_maxmin(5, 1, flip_score) / 100)

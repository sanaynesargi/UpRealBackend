from flask import Flask, request, make_response
from flask_cors import CORS, cross_origin
from logged_in import logged_in
from tables.User import User
from db_manager import db
from pyargon2 import hash
from bcrypt import gensalt
import requests
import os
import json
from datetime import date
from dateutil.relativedelta import relativedelta


app = Flask(__name__)
cors = CORS(app, origins=["http://localhost:5000"])
app.config['CORS_HEADERS'] = 'Content-Type'

app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://postgres:WeCry4U2@upreal-db.c1kuejyqkvci.us-west-2.rds.amazonaws.com:5432/postgres"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    "pool_pre_ping": True,
    "pool_recycle": 300,
}

db.init_app(app)


@app.route("/getUserInfo", methods=['GET'])
@cross_origin(supports_credentials=True)
def get_user_info():

    token = logged_in(request.cookies)

    if not logged_in:
        return {"error": "Not Authorized"}

    user = User.query.filter_by(token=token).first()

    if not user:
        return {"error": "Invalid Token"}

    return {
        "firstName": user.firstname,
        "lastName": user.lastname,
        "email": user.email,
        "username": user.username,
        "company": user.company,
        "createdAt": user.created_at.strftime("%B %d, %Y")
    }


@app.route('/property', methods=['GET'])
@cross_origin()
def get_property_data_realtor():

    # get property listings from MLS via Realtor
    if not os.path.exists("cache_response.json"):
        url = "https://realty-in-us.p.rapidapi.com/properties/v3/list"

        payload = {
            "limit": 200,
            "offset": 0,
            "postal_code": "75077",
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
    count = response["data"]["home_search"]["count"]
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


@app.route('/property2', methods=['GET'])
@cross_origin()
def get_property_data_mash():

    # get property listings from MLS via Realtor
    if not os.path.exists("cache_response.json"):
        url = "https://realty-in-us.p.rapidapi.com/properties/v3/list"

        payload = {
            "limit": 200,
            "offset": 0,
            "postal_code": "75077",
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
    count = response["data"]["home_search"]["count"]
    listing_data = {}

    for result in results:
        property_id = result["id"]
        listing_data[property_id] = {}

        advertising_info = result["agents"]
        property_description = result["description"]

        listing_data[property_id]["seller_info"] = []
        listing_data[property_id]["property_description"] = {}
        listing_data[property_id]["current_estimate"] = None
        listing_data[property_id]["listing_information"] = {}
        listing_data[property_id]["location"] = {}
        listing_data[property_id]["photo"] = None
        listing_data[property_id]["virtual_tours"] = []
        listing_data[property_id]["mls_listing"] = result["url"]

        # if not advertising_info:
        #     continue

        for advertiser in advertising_info:
            listing_data[property_id]["seller_info"].append({
                "id": advertiser["id"],

            })

        listing_data[property_id]["property_description"] = {
            "baths": result["baths"],
            "beds": result["beds"],
            "type": result["homeType"] + " " + result["propertyType"],
            "lot_sqft": property_description["lot_sqft"],
            "prop_sqft": property_description["sqft"],
        }

        if result["listPrice"]:
            listing_data[property_id]["current_estimate"] = result["listPrice"]

        listing_data[property_id]["listing_information"] = {
            "list_date": result["listing_date"],
            "list_price": result["listPrice"],
            "last_sold": result["lastSaleDate"],
            "last_sold_price": result["lastSalePrice"],
        }

        listing_data[property_id]["location"] = {
            "city": result["city"],
            "zip_code": result["zip"],
            "state": result["state"],
            "state_code": result["state"],
            "line": result["address"],
        }

        listing_data[property_id]["location"]["coordinates"] = {
            "lat": result["latitude"],
            "lon": result["longitude"],
        }

        if result["image"]:
            listing_data[property_id]["photo"] = result["image"]["url"]

        if result["virtual_tours"]:
            listing_data[property_id]["virtual_tours"] = [
                tour for tour in result["virtual_tours"]
            ]

    return listing_data


@app.route("/signup", methods=["POST"])
@cross_origin(supports_credentials=True)
def signup():
    form_data = request.form

    if not form_data:
        return {"error": "Invalid Request Body"}

    firstname = form_data.get("firstname")
    lastname = form_data.get("lastname")
    username = form_data.get("username")
    company = form_data.get("company")
    email = form_data.get("email")
    password = form_data.get("password")

    if not (firstname and lastname and username and email and password):
        return {"error": "Required Fields Missing"}

    passwd_salt = str(gensalt())
    passwd_hash = str(hash(password, passwd_salt))

    email_taken = User.query.filter_by(email=email).first() is not None
    username_taken = User.query.filter_by(
        username=username).first() is not None
    login_token = str(os.urandom(16))

    if username_taken:
        return {"error": "Username taken"}

    if email_taken:
        return {"error": "Email Taken, if this is you, then log in"}

    user = User(firstname=firstname, lastname=lastname, username=username,
                company=company, email=email, password=passwd_hash, salt=passwd_salt, token=login_token)

    db.session.add(user)
    db.session.commit()

    resp = make_response({"error": None, "success": True, "id": user.id})

    resp.set_cookie("login_token", login_token, 31 * 24 *
                    60 * 60, date.today() + relativedelta(months=+1), domain='127.0.0.1')
    resp.set_cookie("email", user.email, 31 * 24 *
                    60 * 60, date.today() + relativedelta(months=+1), domain='127.0.0.1')
    resp.set_cookie("username", user.username, 31 * 24 *
                    60 * 60, date.today() + relativedelta(months=+1), domain='127.0.0.1')

    return resp


@app.route("/verifyLogin", methods=["POST"])
@cross_origin(supports_credentials=True)
def verifyLogin():

    form_data = request.form

    if not form_data:
        return {"error": "Invalid Request"}

    token = form_data.get("token")
    if not token:
        return {"error": "Token Needed"}

    user_exists = User.query.filter_by(token=token).first() is None

    if not user_exists:
        return {"error": "Invalid User"}
    else:
        return {"error": None, "success": True}


@app.route("/login", methods=["POST"])
@cross_origin(supports_credentials=True)
def login():

    form_data = request.form

    if not form_data:
        return {"error": "Invalid Request"}

    username_or_email = form_data.get("usernameOrEmail")
    password = form_data.get("password")

    username_user = User.query.filter_by(
        username=username_or_email).first()
    email_user = User.query.filter_by(
        email=username_or_email).first()

    username_match = username_user is not None
    email_match = email_user is not None

    if (not username_match and not email_match):
        return {"error": "Invalid Username or Email"}

    user = username_user if username_match else email_user

    db_pass = user.password
    salt = user.salt
    inp_pass_hash = hash(password, salt)

    if db_pass == inp_pass_hash:
        resp = make_response({"success": True})
        login_token = user.token

        resp.set_cookie("login_token", login_token, 31 * 24 *
                        60 * 60, date.today() + relativedelta(months=+1))
        resp.set_cookie("email", user.email, 31 * 24 *
                        60 * 60, date.today() + relativedelta(months=+1))
        resp.set_cookie("username", user.username, 31 * 24 *
                        60 * 60, date.today() + relativedelta(months=+1))

        return resp

    else:
        return {"success": False, "error": "Invalid password"}


@app.route("/")
@cross_origin()
def index():
    db.create_all()
    return "Server Home"


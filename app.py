from flask import Flask, request, make_response
from flask_cors import CORS, cross_origin
from tables.LikedProperties import LikedPropertiesv2 as LikedProperties
from model_data import get_model_response
from model_data import get_model_data
from logged_in import logged_in
from tables.User import User
from tables.profiles.FixFlipProfile import FixFlipProfile
from tables.profiles.RentProfile import RentProfile
from db_manager import db
from pyargon2 import hash
from bcrypt import gensalt
import requests
import os
import json
from datetime import date
from dateutil.relativedelta import relativedelta


app = Flask(__name__)
cors = CORS(app, origins=["https://seashell-app-dxi4j.ondigitalocean.app"])
app.config['CORS_HEADERS'] = 'Content-Type'

app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://postgres:WeCry4U2@upreal-db.c1kuejyqkvci.us-west-2.rds.amazonaws.com:5432/postgres"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    "pool_pre_ping": True,
    "pool_recycle": 300,
}

db.init_app(app)


@app.route("/getUserInfo", methods=['GET'])
@cross_origin()
@cross_origin(supports_credentials=True)
def get_user_info():

    token = logged_in(request.cookies)

    if not token:
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

    zip = request.args.get("zip_code")

    # if not zip:
    #     return {"error": "Invalid Request"}

    # get property listings from MLS via Realtor
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


@app.route("/propertyInfo", methods=['GET'])
@cross_origin(supports_credentials=True)
def get_property_scores():
    token = logged_in(request.cookies)

    if not token:
        return {"error": "Not Authorized"}

    user = User.query.filter_by(token=token).first()

    if not user:
        return {"error": "Invalid Token"}

    address1 = request.args.get("address1")
    address2 = request.args.get("address2")

    if not address1 or not address2:
        return {"error": "Invalid Request"}

    property_data = get_model_data(address1, address2)

    if not property_data:
        return {"error": "Error fetching property data"}

    scores = get_model_response(property_data)

    if not scores:
        return {"error": "Error making request to GCP"}

    return scores


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
                company=company, email=email, password=passwd_hash, salt=passwd_salt, token=login_token, profile_ids="")

    db.session.add(user)
    db.session.commit()

    resp = make_response({"error": None, "success": True, "id": user.id,
                         "initals": user.firstname[0] + user.lastname[0], "fullName": f"{user.firstname} {user.lastname}"})

    resp.set_cookie("login_token", login_token, 31 * 24 *
                    60 * 60, date.today() + relativedelta(months=+1), secure=True, samesite="None")
    resp.set_cookie("email", user.email, 31 * 24 *
                    60 * 60, date.today() + relativedelta(months=+1), secure=True, samesite="None")
    resp.set_cookie("username", user.username, 31 * 24 *
                    60 * 60, date.today() + relativedelta(months=+1), secure=True, samesite="None")

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
        resp = make_response(
            {"success": True, "initals": user.firstname[0] + user.lastname[0], "fullName": f"{user.firstname} {user.lastname}"})

        login_token = user.token

        resp.set_cookie("login_token", login_token, 31 * 24 *
                        60 * 60, date.today() + relativedelta(months=+1), secure=True, samesite="None")
        resp.set_cookie("email", user.email, 31 * 24 *
                        60 * 60, date.today() + relativedelta(months=+1),  secure=True, samesite="None")
        resp.set_cookie("username", user.username, 31 * 24 *
                        60 * 60, date.today() + relativedelta(months=+1),  secure=True, samesite="None")

        return resp

    else:
        return {"success": False, "error": "Invalid Password"}


@app.route("/setProfile", methods=["POST"])
@cross_origin(supports_credentials=True)
def set_profile():
    token = logged_in(request.cookies)

    if not token:
        return {"error": "Not Authorized"}

    user = User.query.filter_by(token=token).first()

    if not user:
        return {"error": "Invalid Token"}

    form = request.form

    if not request.form.get("profile_type"):
        return {"error": "Invalid Request"}

    if form["profile_type"] == "Rental":
        name = request.form.get("name")
        metro_area = request.form.get("location")
        risk = request.form.get("risk")
        budget_high = request.form.get("budgetHigh")
        budget_low = request.form.get("budgetLow")
        appreciation_high = request.form.get("appHigh")
        appreciation_low = request.form.get("appLow")
        cashflow_high = request.form.get("cashflowHigh")
        cashflow_low = request.form.get("cashflowLow")
        coc_high = request.form.get("cocHigh")
        coc_low = request.form.get("cocLow")
        main_high = request.form.get("mainHigh")
        main_low = request.form.get("mainLow")
        hold_high = request.form.get("holdHigh")
        hold_low = request.form.get("holdLow")

        if not hold_high or not hold_low or not name or not metro_area or not risk or not budget_high or not budget_low or not appreciation_high or not appreciation_low or not cashflow_high or not cashflow_low or not coc_high or not coc_low or not main_high or not main_low:
            return {"error": "Invalid Request"}

        existing_profile = RentProfile.query.filter_by(
            name=name).first() is not None

        if existing_profile:
            return {"error": "Name Exists"}

        profile = RentProfile(name=name, location=metro_area, risk=risk, budget_high=budget_high, budget_low=budget_low, appreciation_high=appreciation_high,
                              appreciation_low=appreciation_low, cashflow_high=cashflow_high, cashflow_low=cashflow_low, coc_high=coc_high, coc_low=coc_low,
                              main_high=main_high, main_low=main_low, hold_low=hold_low, hold_high=hold_high)
        db.session.add(profile)
        db.session.commit()

        if len(user.profile_ids) == 0:
            user.profile_ids = f"R{profile.id}"
        else:
            split_ids = user.profile_ids.split("|")

            if len(split_ids) == 20:
                return {"error": "Max profiles reached"}

            new_ids = f"{user.profile_ids}|R{profile.id}"
            user.profile_ids = new_ids

        db.session.add(user)
        db.session.commit()

        return {"success": True}

    elif form["profile_type"] == "Fix and Flip":
        name = request.form.get("name")
        metro_area = request.form.get("location")
        risk = request.form.get("risk")
        budget_high = request.form.get("budgetHigh")
        budget_low = request.form.get("budgetLow")
        after_repair_high = request.form.get("afterRepairHigh")
        after_repair_low = request.form.get("afterRepairLow")
        repair_cost_high = request.form.get("repairCostHigh")
        repair_cost_low = request.form.get("repairCostLow")
        coc_high = request.form.get("cocHigh")
        coc_low = request.form.get("cocLow")

        if not name or not metro_area or not risk or not budget_high or not budget_low or not after_repair_high or not after_repair_low or not repair_cost_high or not repair_cost_low or not coc_high or not coc_low:
            return {"error": "Invalid Request"}

        existing_profile = FixFlipProfile.query.filter_by(
            name=name).first() is not None

        if existing_profile:
            return {"error": "Name Exists"}

        profile = FixFlipProfile(name=name, location=metro_area, risk=risk,
                                 budget_high=budget_high, budget_low=budget_low, after_repair_high=after_repair_high, after_repair_low=after_repair_low, repair_cost_high=repair_cost_high, repair_cost_low=repair_cost_low, coc_high=coc_high, coc_low=coc_low)
        db.session.add(profile)
        db.session.commit()

        db.session.add(user)
        db.session.commit()

        if len(user.profile_ids) == 0:
            user.profile_ids = f"F{profile.id}"
        else:
            split_ids = user.profile_ids.split("|")

            if len(split_ids) == 20:
                return {"error": "Max profiles reached"}

            new_ids = f"{user.profile_ids}|F{profile.id}"
            user.profile_ids = new_ids

        db.session.add(user)
        db.session.commit()

        return {"success": True}


@app.route("/getProfileList", methods=["GET"])
@cross_origin(supports_credentials=True)
def get_profile_list():
    token = logged_in(request.cookies)

    if not token:
        return {"error": "Not Authorized"}

    user = User.query.filter_by(token=token).first()

    if not user:
        return {"error": "Invalid Token"}

    if user.profile_ids == "":
        return {"error": "No Profiles Found"}

    split_profiles = user.profile_ids.split("|")

    json_data = []

    for type, id in split_profiles:
        if type == "R":
            profile = RentProfile.query.filter_by(id=id).first()

            if profile.deleted:
                continue

            entry = {
                "profile_type": {
                    "title": "Profile Type",
                    "value": "Rental"
                },
                "profile_name": {
                    "title": "Profile Name",
                    "value": profile.name,
                },
                "creation_date": {
                    "title": "Created On",
                    "value": profile.created_at.strftime("%B %d, %Y"),
                },
                "metro_location": {
                    "title": "Metro Location",
                    "value": profile.location,
                },
                "risk_appetite": {
                    "title": "Risk Appetite",
                    "value": profile.risk,
                },
                "purchase_budget": {
                    "title": "Purchase Budget",
                    "value_low": profile.budget_low,
                    "value_high": profile.budget_high,
                    "currency": "USD",
                },
                "appreciation_target": {
                    "title": "Target Appreciation for Sale",
                    "value_low": profile.appreciation_low,
                    "value_high": profile.appreciation_high,
                    "currency": "USD",
                },
                "hold_period": {
                    "title": "Hold Period",
                    "value_low": profile.hold_low,
                    "value_high": profile.hold_high,
                    "time_unit": "years"
                },
                "cash_flow_target": {
                    "title": "Target Cash Flow",
                    "value_low": profile.cashflow_low,
                    "value_high": profile.cashflow_high,
                    "time_unit": "Monthly"
                },
                "cash_on_cash_target": {
                    "title": "Cash-on-Cash Target",
                    "value_low": profile.coc_low,
                    "value_high": profile.coc_high,
                    "unit": "Percent",
                    "time_unit": "Annual",
                },
                "maintenance_spend": {
                    "title": "Maintenance Spend",
                    "value_low": profile.main_low,
                    "value_high": profile.main_high,
                    "time_unit": "Annual",
                }
            }

        elif type == "F":
            profile = FixFlipProfile.query.filter_by(id=id).first()

            if profile.deleted:
                continue

            entry = {
                "profile_type": {
                    "title": "Profile Type",
                    "value": "Fix and Flip"
                },
                "profile_name": {
                    "title": "Profile Name",
                    "value": profile.name,
                },
                "creation_date": {
                    "title": "Created On",
                    "value": profile.created_at.strftime("%B %d, %Y"),
                },
                "metro_location": {
                    "title": "Metro Location",
                    "value": profile.location,
                },
                "risk_appetite": {
                    "title": "Risk Appetite",
                    "value": profile.risk,
                },
                "purchase_budget": {
                    "title": "Purchase Budget",
                    "value_low": profile.budget_low,
                    "value_high": profile.budget_high,
                    "currency": "USD",
                },
                "after_repair_value_target": {
                    "title": "After Repair Value Target",
                    "value_low": profile.after_repair_low,
                    "value_high": profile.after_repair_high,
                    "currency": "USD"
                },
                "repair_costs_target": {
                    "title": "Target Repair Costs",
                    "value_low": profile.repair_cost_low,
                    "value_high": profile.repair_cost_high,
                    "unit": "Percent",
                },
                "cash_on_cash_target": {
                    "title": "Cash-on-Cash Target",
                    "value_low": profile.coc_low,
                    "value_high": profile.coc_high,
                    "unit": "Percent",
                    "time_unit": "Annual",
                },
            }

        json_data.append(entry)

    return {"profiles": json_data}


@app.route("/getProfileNames", methods=["GET"])
@cross_origin(supports_credentials=True)
def get_profile_names():
    token = logged_in(request.cookies)

    if not token:
        return {"error": "Not Authorized"}

    user = User.query.filter_by(token=token).first()

    if not user:
        return {"error": "Invalid Token"}

    if user.profile_ids == "":
        return {"error": "No Profiles Found"}

    split_profiles = user.profile_ids.split("|")

    json_data = []

    for type, id in split_profiles:
        if type == "R":
            profile = RentProfile.query.filter_by(id=id).first()

            if profile.deleted:
                continue

        elif type == "F":
            profile = FixFlipProfile.query.filter_by(id=id).first()

            if profile.deleted:
                continue

        json_data.append(profile.name)

    return {"profileNames": json_data}


@app.route("/getProfile", methods=["GET"])
@cross_origin(supports_credentials=True)
def get_profile():
    token = logged_in(request.cookies)

    if not token:
        return {"error": "Not Authorized"}

    user = User.query.filter_by(token=token).first()

    if not user:
        return {"error": "Invalid Token"}

    name = request.args.get("name")

    if user.profile_ids == "":
        return {"error": "No Profiles Found"}

    split_profiles = user.profile_ids.split("|")

    for type, id in split_profiles:
        if type == "F":
            profile = RentProfile.query.filter_by(id=id).first()
            if profile.deleted:
                continue
            if profile.name == name:
                return {"profile": {
                    "profile_type": {
                        "title": "Profile Type",
                        "value": "Rental"
                    },
                    "profile_name": {
                        "title": "Profile Name",
                        "value": profile.name,
                    },
                    "creation_date": {
                        "title": "Created On",
                        "value": profile.created_at.strftime("%B %d, %Y"),
                    },
                    "metro_location": {
                        "title": "Metro Location",
                        "value": profile.location,
                    },
                    "risk_appetite": {
                        "title": "Risk Appetite",
                        "value": profile.risk,
                    },
                    "purchase_budget": {
                        "title": "Purchase Budget",
                        "value_low": profile.budget_low,
                        "value_high": profile.budget_high,
                        "currency": "USD",
                    },
                    "appreciation_target": {
                        "title": "Target Appreciation for Sale",
                        "value_low": profile.appreciation_low,
                        "value_high": profile.appreciation_high,
                        "currency": "USD",
                    },
                    "hold_period": {
                        "title": "Hold Period",
                        "value_low": profile.hold_low,
                        "value_high": profile.hold_high,
                        "time_unit": "years"
                    },
                    "cash_flow_target": {
                        "title": "Target Cash Flow",
                        "value_low": profile.cashflow_low,
                        "value_high": profile.cashflow_high,
                        "time_unit": "Monthly"
                    },
                    "cash_on_cash_target": {
                        "title": "Cash-on-Cash Target",
                        "value_low": profile.coc_low,
                        "value_high": profile.coc_high,
                        "unit": "Percent",
                        "time_unit": "Annual",
                    },
                    "maintenance_spend": {
                        "title": "Maintenance Spend",
                        "value_low": profile.main_low,
                        "value_high": profile.main_high,
                        "time_unit": "Annual",
                    }
                }}
        elif type == "F":
            profile = FixFlipProfile.query.filter_by(id=id).first()
            if profile.deleted:
                continue
            if profile.name == name:
                return {"profile": {
                    "profile_type": {
                        "title": "Profile Type",
                        "value": "Rental"
                    },
                    "profile_name": {
                        "title": "Profile Name",
                        "value": profile.name,
                    },
                    "creation_date": {
                        "title": "Created On",
                        "value": profile.created_at.strftime("%B %d, %Y"),
                    },
                    "metro_location": {
                        "title": "Metro Location",
                        "value": profile.location,
                    },
                    "risk_appetite": {
                        "title": "Risk Appetite",
                        "value": profile.risk,
                    },
                    "purchase_budget": {
                        "title": "Purchase Budget",
                        "value_low": profile.budget_low,
                        "value_high": profile.budget_high,
                        "currency": "USD",
                    },
                    "after_repair_value_target": {
                        "title": "After Repair Value Target",
                        "value_low": profile.after_repair_low,
                        "value_high": profile.after_repair_high,
                        "currency": "USD"
                    },
                    "repair_costs_target": {
                        "title": "Target Repair Costs",
                        "value_low": profile.repair_cost_low,
                        "value_high": profile.repair_cost_high,
                        "unit": "Percent",
                    },
                    "cash_on_cash_target": {
                        "title": "Cash-on-Cash Target",
                        "value_low": profile.coc_low,
                        "value_high": profile.coc_high,
                        "unit": "Percent",
                        "time_unit": "Annual",
                    },
                }}

    return {"error": "No Matching Profiles Found"}


@app.route("/deleteProfile", methods=["GET"])
@cross_origin(supports_credentials=True)
def delete_profile():
    token = logged_in(request.cookies)

    if not token:
        return {"error": "Not Authorized"}

    user = User.query.filter_by(token=token).first()

    if not user:
        return {"error": "Invalid Token"}

    name = request.args.get("name")

    split_profiles = user.profile_ids.split("|")

    for type, id in split_profiles:

        if type == "F":
            profile = RentProfile.query.filter_by(id=id).first()

            if profile.name != name:
                continue

            profile.deleted = True

            db.session.add(profile)
            db.session.commit()

            return {"success": True, "deleted": profile.deleted}

        elif type == "F":
            profile = FixFlipProfile.query.filter_by(id=id).first()

            if profile.name != name:
                continue

            profile.deleted = True

            db.session.add(profile)
            db.session.commit()

            return {"success": True, "deleted": profile.deleted}

    return {"error": "No Matching Profiles Found"}


@app.route("/setLike", methods=["POST"])
@cross_origin(supports_credentials=True)
def setLike():
    token = logged_in(request.cookies)

    if not token:
        return {"error": "Not Authorized"}

    user = User.query.filter_by(token=token).first()

    if not user:
        return {"error": "Invalid Token"}

    prop_id = request.form.get("propId")
    profile_name = request.form.get("profileName")
    imageUrl = request.form.get("imageUrl")
    beds = request.form.get("beds")
    baths = request.form.get("baths")
    title = request.form.get("title")
    formattedPrice = request.form.get("formattedPrice")
    type = request.form.get("type")
    apiInfo = request.form.get("apiInfo")
    city = request.form.get("city")

    if not profile_name or not prop_id or not imageUrl or not beds or not baths or not title or not formattedPrice or not type or not apiInfo or not city:
        return {"error": "Invalid Request"}

    existing_prop = LikedProperties.query.filter_by(
        title=title, profile_name=profile_name).first()

    if existing_prop is not None:
        db.session.delete(existing_prop)
        db.session.commit()

        return {"success": True}

    property = LikedProperties(user_id=user.id, prop_id=prop_id, imageUrl=imageUrl,
                               beds=beds, baths=baths, title=title, type=type, apiInfo=apiInfo, city=city, formattedPrice=formattedPrice, profile_name=profile_name)

    db.session.add(property)
    db.session.commit()

    return {"success": True, "id": property.id}


@app.route("/getLikedProperties", methods=["GET"])
@cross_origin(supports_credentials=True)
def getLikes():
    token = logged_in(request.cookies)

    if not token:
        return {"error": "Not Authorized"}

    user = User.query.filter_by(token=token).first()

    if not user:
        return {"error": "Invalid Token"}

    props = LikedProperties.query.filter_by(
        user_id=user.id).all()

    prop_info = []

    for prop in props:
        prop_info.append({
            "imageUrl": prop.imageUrl,
            "beds":  prop.beds,
            "baths": prop.baths,
            "title": prop.title,
            "formattedPrice": prop.formattedPrice,
            "type":  prop.type,
            "apiInfo":  prop.apiInfo,
            "city": prop.city,
            "propId": prop.prop_id,
            "profile": prop.profile_name,
        })

    return {"props": prop_info}


@app.route("/")
@cross_origin()
def index():
    # db.drop_all()
    # db.create_all()

    return "Server Home"

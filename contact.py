import flask_login
from sqlalchemy.sql.functions import user
from flask_security import current_user

from app.errors.customs import MissingParameterException
import datetime, requests
import json
from flask import request
from app import Config
from app.api import bp
from app.utils import get_request_json, OK_RESPONSE


@bp.route("/contact/sales", methods=["POST"])
def sales():
    """
    Create a new ticket in ClickUp CRM with the given sales information
    ---
    responses:
        200:
    """
    business_name = (
        get_request_json(request, "business_name", optional=True) or "Unknown"
    )
    contact_name = get_request_json(request, "contact_name")
    contact_title = get_request_json(request, "contact_title", optional=True)
    phone = get_request_json(request, "phone", optional=True)
    if phone:
        phone = (
            "+"
            + phone["country_code"]
            + " "
            + phone["area_code"]
            + " "
            + phone["phone_number"][:3]
            + " "
            + phone["phone_number"][3:]
        )
    email = get_request_json(request, "email", optional=True)
    website = get_request_json(request, "website", optional=True)
    num_managers = get_request_json(request, "num_managers", optional=True)
    num_contractors = get_request_json(request, "num_contractors", optional=True)
    notes = get_request_json(request, "notes", optional=True)

    if not (phone or email):
        raise (MissingParameterException(f"No contact information provided."))
    create_ticket(
        business_name,
        contact_name,
        contact_title,
        phone,
        email,
        website,
        num_managers,
        num_contractors,
        notes,
    )
    return OK_RESPONSE, 201


def create_ticket(
    business_name,
    contact_name,
    contact_title,
    phone,
    email,
    website,
    num_managers,
    num_contractors,
    notes,
):
    values = {
        "name": business_name,
        "description": notes,
        "status": "qualified prospect",
        "start_date": int(datetime.datetime.now().timestamp()),
        "notify_all": True,
        "check_required_custom_fields": True,
        "custom_fields": [
            {"id": "1f5b9606-293f-4abc-8bdc-15a4d3739749", "value": contact_name},
            {"id": "fd844e04-66de-4387-bc0e-4d51c499526b", "value": phone},
            {"id": "ea4abe15-0e7e-40b4-b7a2-7b37cf4cf6b7", "value": contact_title},
            {"id": "861d4136-1c80-4735-8fb6-d4a95e5ce1c2", "value": num_contractors},
            {"id": "f8cb7b25-f05b-468e-a043-3972c1307d42", "value": num_managers},
            {"id": "3dbe29b4-02ec-41ff-83dd-7e2b0b6d9dff", "value": email},
            {"id": "c2917630-b938-45de-99d1-6369c0690ee3", "value": website},
        ],
    }
    headers = {"Authorization": Config.CLICKUP_KEY, "Content-Type": "application/json"}
    requests.post(
        "https://api.clickup.com/api/v2/list/81940859/task",
        data=json.dumps(values),
        headers=headers,
    )
    return


@bp.route("/contact/support", methods=["POST"])
def support():
    """
    Create a new ticket in ClickUp CRM with the given information
    and append to the support list . Does not require name or email
    if user logged in.
    ---
    responses:
        200:
    """

    phone = get_request_json(request, "phone", optional=True)
    if phone:
        phone = (
            "+"
            + phone["country_code"]
            + " "
            + phone["area_code"]
            + " "
            + phone["phone_number"][:3]
            + " "
            + phone["phone_number"][3:]
        )
    email = get_request_json(request, "email", optional=True)
    description = get_request_json(request, "description", optional=True)
    user_agent = get_request_json(request, "ua", optional=True)
    browser = get_request_json(request, "browser", optional=True)
    if browser:
        browser = browser["name"] + " " + browser["version"] + " " + browser["major"]

    os = get_request_json(request, "os", optional=True)

    if os:
        os = os["name"] + " " + os["version"]

    the_user = current_user
    device = get_request_json(request, "device", optional=True)
    cpu = get_request_json(request, "cpu", optional=True)
    if cpu:
        cpu = cpu["architecture"]
    engine = get_request_json(request, "engine", optional=True)

    if engine:
        engine = engine["name"] + " " + engine["version"]
    if current_user.is_authenticated:
        user_id = the_user.id
        name = the_user.first_name + " " + the_user.last_name
        email = the_user.email

    else:
        user_id = "Not logged in"
        name = get_request_json(request, "name", optional=True) or "Unknown"

    create_support_ticket(
        name,
        phone,
        email,
        description,
        user_agent,
        browser,
        engine,
        os,
        device,
        cpu,
        user_id,
    )

    if not description:
        raise (MissingParameterException(f"Include a Description For Your Problem"))
    return OK_RESPONSE, 201


def create_support_ticket(
    name,
    phone,
    email,
    description,
    user_agent,
    browser,
    engine,
    os,
    device,
    cpu,
    user_id,
):
    values = {
        "name": name,
        "phone": phone,
        "email": email,
        "description": description,
        "ua": user_agent,
        "browser": browser,
        "engine": engine,
        "os": os,
        "device": device,
        "cpu": cpu,
        "user_id": user_id,

        "custom_fields": [

            {"id": "1f5b9606-293f-4abc-8bdc-15a4d3739749", "value":name},
            {"id": "fd844e04-66de-4387-bc0e-4d51c499526b", "value": phone},
            {"id": "3dbe29b4-02ec-41ff-83dd-7e2b0b6d9dff", "value": email},
            {"id": "8cafe79d-6b05-43f6-8be3-bd8291e18ba9", "value": description},
            {"id": "7b61b15e-7ab0-47a3-b9c0-a0e209e888ed", "value": user_agent},
            {"id": "c2891b23-0a2d-4a53-8feb-c77171d3df99", "value": browser},
            {"id": "d7d4ceec-22e0-4bca-a962-f18a937c507e", "value": engine},
            {"id": "55c2e4e1-b127-4e57-9835-93fd3c9e8a1a", "value": os},
            {"id": "df2c9793-df47-432a-9d51-c8c2bfad9da7", "value": device},
            {"id": "17d2e246-df8e-4a66-a86b-8578d46eae53", "value": cpu},
            {"id": "5f3010d7-19a0-4be6-a69d-06e1c09d1ca1", "value": user_id},

],
    }
    headers = {"Authorization": Config.CLICKUP_KEY, "Content-Type": "application/json"}
    requests.post(
        "https://api.clickup.com/api/v2/list/84083345/task",
        data=json.dumps(values),
        headers=headers,
    )
    return

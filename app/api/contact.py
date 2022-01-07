from flask_security import current_user

from app.errors.customs import MissingParameterException
import datetime, requests
import json
from flask import request
from app import Config
from app.api import bp
from app.utils import get_request_json, OK_RESPONSE


CLICKUP_BASE_URL = "https://api.clickup.com/api/v2/"
SALES_LIST_ID = "81940859"
SUPPORT_LIST_ID = "84083345"
HEADERS = {
    "Authorization": Config.CLICKUP_KEY,
    "Content-Type": "application/json"
}


# Format phone number as +X (XXX) XXX-XXXX
def format_phone_number(phone_number):
    if phone_number is None:
        return None
    if len(phone_number) == 10:
        return "+1 (" + phone_number[:3] + ") " + phone_number[3:6] + "-" + phone_number[6:]
    if len(phone_number) == 11:
        return "+" + phone_number[:1] + " (" + phone_number[1:4] + ") " + phone_number[4:7] + "-" + phone_number[7:]
    return phone_number

# Return phone number string from dictionary
def build_phone_number(phone_dict):
    return format_phone_number(
        phone["country_code"]
        + phone["area_code"]
        + phone["phone_number"]
    )

@bp.route("/contact/sales", methods=["POST"])
def sales():
    """
    Create a new ticket in ClickUp CRM with the given sales information
    ---
    responses:
        200:
    """
    business_name   = get_request_json(request, "business_name",    optional=True) or "Unknown"
    contact_name    = get_request_json(request, "contact_name")
    contact_title   = get_request_json(request, "contact_title",    optional=True)
    phone           = get_request_json(request, "phone",            optional=True)
    email           = get_request_json(request, "email",            optional=True)
    website         = get_request_json(request, "website",          optional=True)
    num_managers    = get_request_json(request, "num_managers",     optional=True)
    num_contractors = get_request_json(request, "num_contractors",  optional=True)
    notes           = get_request_json(request, "notes",            optional=True)

    if phone:
        phone = build_phone_number(phone)

    if not (phone or email):
        raise (MissingParameterException(f"No contact information provided."))

    ticket = create_ticket(
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
    # TODO: Return ticket data
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
    payload = {
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

    return requests.post(
        CLICKUP_BASE_URL + "list/" + SALES_LIST_ID + "/task",
        data=json.dumps(payload),
        headers=HEADERS,
    )


@bp.route("/contact/support", methods=["POST"])
def support():
    """
    Create a new ticket in ClickUp CRM with the given staff information
    ---
    responses:
        200:
    """

    if (current_user):
        name = current_user.first_name + " " + current_user.last_name
        email = current_user.email
        phone = format_phone_number(current_user.phone)
        user_id = str(current_user.id)
    else:
        name    = get_request_json(request, "name",         optional=True) or "Unknown"
        phone   = build_phone_number(get_request_json(request, "phone", optional=True)) or "Unknown"
        email   = get_request_json(request, "email",        optional=True) or "Unknown"

    # Retreive fields
    description = get_request_json(request, "description",  optional=True)
    user_agent  = get_request_json(request, "ua",           optional=True)
    browser     = get_request_json(request, "browser",      optional=True)
    os          = get_request_json(request, "os",           optional=True)
    device      = get_request_json(request, "device",       optional=True)
    cpu         = get_request_json(request, "cpu",          optional=True)
    engine      = get_request_json(request, "engine",       optional=True)

    # Reformat fields
    if browser:
        browser = browser["name"] + " " + browser["version"] + " " + browser["major"]

    if os:
        os = os["name"] + " " + os["version"]

    if cpu:
        cpu = cpu["architecture"]

    if engine:
        engine = engine["name"] + " " + engine["version"]

    if not description:
        raise (MissingParameterException(f"Include a Description For Your Problem"))

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
    payload = {
        "name": description,
        "status": "to do",
        "notify_all": True,
        "check_required_custom_fields": True,
        "custom_fields": [
            {"id": "c2891b23-0a2d-4a53-8feb-c77171d3df99", "value": browser }, # Browser Information
            {"id": "17d2e246-df8e-4a66-a86b-8578d46eae53", "value": cpu }, # CPU Type
            {"id": "1f5b9606-293f-4abc-8bdc-15a4d3739749", "value": name }, # Contact
            {"id": "fd844e04-66de-4387-bc0e-4d51c499526b", "value": phone }, # Contact Phone #
            {"id": "8cafe79d-6b05-43f6-8be3-bd8291e18ba9", "value": description }, # Description
            {"id": "df2c9793-df47-432a-9d51-c8c2bfad9da7", "value": device }, # Device Type
            {"id": "3dbe29b4-02ec-41ff-83dd-7e2b0b6d9dff", "value": email }, # Email
            {"id": "d7d4ceec-22e0-4bca-a962-f18a937c507e", "value": engine }, # Engine
            {"id": "55c2e4e1-b127-4e57-9835-93fd3c9e8a1a", "value": os }, # OS Information
            {"id": "7b61b15e-7ab0-47a3-b9c0-a0e209e888ed", "value": user_agent }, # User Agent
            {"id": "5f3010d7-19a0-4be6-a69d-06e1c09d1ca1", "value": user_id }, # User ID
        ],
    }
    
    return requests.post(
        CLICKUP_BASE_URL + "list/" + SUPPORT_LIST_ID + "/task",
        data=json.dumps(payload),
        headers=HEADERS,
    )

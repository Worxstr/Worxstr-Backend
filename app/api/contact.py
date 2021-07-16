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

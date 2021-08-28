from flask import request
from flask_security import login_required, roles_accepted, current_user

from app import db, payments, payments_auth
from app.api import bp
from app.errors.customs import MissingParameterException
from app.models import Organization, TimeCard, User, TimeClock, ContractorInfo
from app.api.clock import calculate_timecard
from app.utils import OK_RESPONSE, get_request_arg, get_request_json


@bp.route("/payments/access", methods=["POST"])
def access_payment_facilitator():
    return {"token": payments.app_token.access_token}


@login_required
@bp.route("/payments/accounts", methods=["POST"])
def add_account():
    public_token = get_request_json(request, "public_token")
    account_id = get_request_json(request, "account_id")
    account_name = get_request_json(request, "name")

    dwolla_token = payments_auth.get_dwolla_token(public_token, account_id)
    if current_user.has_role("contractor"):
        customer_url = current_user.dwolla_customer_url
    else:
        customer_url = (
            db.session.query(Organization.dwolla_customer_url)
            .filter(Organization.id == current_user.organization_id)
            .one()[0]
        )
    return payments.authenticate_funding_source(
        customer_url, dwolla_token, account_name
    )


@login_required
@bp.route("/payments/accounts", methods=["GET"])
def get_accounts():
    if current_user.has_role("contractor"):
        customer_url = current_user.dwolla_customer_url
    else:
        customer_url = (
            db.session.query(Organization.dwolla_customer_url)
            .filter(Organization.id == current_user.organization_id)
            .one()[0]
        )
    return payments.get_funding_sources(customer_url)


@login_required
@bp.route("/payments/accounts", methods=["PUT"])
def edit_account():
    location = get_request_json(request, "location")
    account_name = get_request_json(request, "name")
    return payments.edit_funding_source(location, account_name)


@login_required
@bp.route("/payments/accounts", methods=["DELETE"])
def remove_account():
    location = get_request_json(request, "location")
    payments.remove_funding_source(location)
    return OK_RESPONSE


@login_required
@bp.route("/payments/plaid-link-token", methods=["POST"])
def get_link_token():
    return {"token": payments_auth.obtain_link_token(current_user.id)}


@bp.route("/payments/deny", methods=["PUT"])
@login_required
@roles_accepted("organization_manager", "contractor_manager")
def deny_payment():
    timecards = get_request_json(request, "timecards")

    ids = []
    for timecard in timecards:
        ids.append(timecard["id"])
        if "denied" in timecard.keys():
            db.session.query(TimeCard).filter(TimeCard.id == timecard["id"]).update(
                {TimeCard.denied: timecard["denied"]}, synchronize_session=False
            )
    db.session.commit()
    timecards = db.session.query(TimeCard).filter(TimeCard.id.in_(ids)).all()

    return OK_RESPONSE


@bp.route("/payments/timecards", methods=["GET"])
@login_required
@roles_accepted("organization_manager", "contractor_manager")
def get_timecards():
    """Endpoint to get all unpaid timecards associated with the current logged in manager.
    ---
    definitions:
        TimeCard:
            type: object
            properties:
                id:
                    type: integer
                time_in:
                    type: string
                    format: date-time
                time_out:
                    type: string
                    format: date-time
                time_break:
                    type: integer
                contractor_id:
                    type: integer
                total_payment:
                    type: number
                paid:
                    type: boolean
                first_name:
                    type: string
                last_name:
                    type: string
                time_clocks:
                    type: array
                    items :
                        $ref: '#/definitions/TimeClock'
        TimeClock:
            type: object
            properties:
                id:
                    type: integer
                time:
                    type: string
                    format: date-time
                action:
                    type: string
                    enum: []
                contractor_id:
                    type: integer
    responses:
        200:
            description: Returns the timecards associated with a manager
            schema:
                $ref: '#/definitions/TimeCard'
    """
    timecards = (
        db.session.query(TimeCard, User.first_name, User.last_name)
        .join(User)
        .filter(
            TimeCard.paid == False,
            TimeCard.denied == False,
            User.manager_id == current_user.id,
        )
        .all()
    )

    # TODO: Implement paging here
    result = []
    for i in timecards:
        timecard = i[0].to_dict()
        timecard["first_name"] = i[1]
        timecard["last_name"] = i[2]
        timecard["pay_rate"] = float(
            db.session.query(ContractorInfo.hourly_rate)
            .filter(ContractorInfo.id == timecard["contractor_id"])
            .one()[0]
        )
        timecard["time_clocks"] = [
            timeclock.to_dict()
            for timeclock in db.session.query(TimeClock)
            .filter(TimeClock.timecard_id == timecard["id"])
            .order_by(TimeClock.time)
            .all()
        ]
        result.append(timecard)
    return {"timecards": result}


@bp.route("/payments/timecards/<timecard_id>", methods=["PUT"])
@login_required
@roles_accepted("contractor_manager")
def edit_timecard(timecard_id):
    """Edit a given timecard.
    ---
    parameters:
        - name: id
          in: body
          type: integer
          required: true
          description: TimeCard.id
        - name: changes
          in: body
          type: array
          items:
              $ref: '#/definitions/Change'
          required: true
    definitions:
        Change:
            type: object
            properties:
                id:
                    type: integer
                    description: id of the TimeClock event to be modified
                time:
                    type: string
                    format: date-time
        TimeCard:
            type: object
            properties:
                id:
                    type: integer
                time_in:
                    type: string
                    format: date-time
                time_out:
                    type: string
                    format: date-time
                time_break:
                    type: integer
                contractor_id:
                    type: integer
                total_payment:
                    type: number
                paid:
                    type: boolean
    responses:
        200:
            description: An updated TimeCard showing the new changes.
            schema:
                $ref: '#/definitions/TimeCard'
    """
    changes = get_request_json(request, "changes")

    timecard = db.session.query(TimeCard).filter(TimeCard.id == timecard_id).one()
    contractor_id = timecard.contractor_id

    for i in changes:
        db.session.query(TimeClock).filter(TimeClock.id == i["id"]).update(
            {TimeClock.time: i["time"]}, synchronize_session=False
        )

    db.session.commit()
    calculate_timecard(timecard.id)
    # TODO: These could likely be combined into one query
    rate = (
        db.session.query(ContractorInfo.hourly_rate)
        .filter(ContractorInfo.id == contractor_id)
        .one()
    )
    user = (
        db.session.query(User.first_name, User.last_name)
        .filter(User.id == contractor_id)
        .one()
    )
    result = (
        db.session.query(TimeCard).filter(TimeCard.id == timecard.id).one().to_dict()
    )
    result["first_name"] = user[0]
    result["last_name"] = user[1]
    result["pay_rate"] = float(rate[0])
    result["time_clocks"] = [
        timeclock.to_dict()
        for timeclock in db.session.query(TimeClock)
        .filter(TimeClock.timecard_id == timecard_id)
        .order_by(TimeClock.time)
        .all()
    ]
    return {"timecard": result}

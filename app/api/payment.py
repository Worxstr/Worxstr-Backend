from datetime import datetime
from flask import request
from flask_security import login_required, roles_accepted, current_user
from sqlalchemy.sql.elements import Null, or_

from app import db, payments, payments_auth, notifications
from app.api import bp
from app.errors.customs import MissingParameterException
from app.models import (
    Invoice,
    InvoiceItem,
    Organization,
    Payment,
    TimeCard,
    User,
    TimeClock,
    ContractorInfo,
    Role,
)
from app.api.clock import calculate_timecard
from app.api.sockets import emit_to_users
from app.utils import OK_RESPONSE, get_request_arg, get_request_json


def get_manager_user_ids(organization_id):
    # Get the ids of managers within the current organization
    return [
        r[0]
        for r in db.session.query(User.id)
        .filter(
            User.organization_id == organization_id,
            User.roles.any(
                Role.name.in_(["contractor_manager", "organization_manager"])
            ),
        )
        .all()
    ]


@bp.route("/payments/accounts/status", methods=["POST"])
def update_account_status():
    topic = get_request_json(request, "topic")
    links = get_request_json(request, "_links")
    if (
        topic == "customer_verified"
        or topic == "customer_verification_document_needed"
        or topic == "customer_reverification_needed"
        or topic == "customer_suspended"
    ):
        customer_url = links["customer"]["href"]
        customer = payments.get_customer_info(customer_url)
        if customer["type"] == "personal":
            db.session.query(ContractorInfo).filter(
                ContractorInfo.dwolla_customer_url == customer_url
            ).update({ContractorInfo.dwolla_customer_status: customer["status"]})
            db.session.commit()
    return OK_RESPONSE


@bp.route("/payments/access", methods=["POST"])
def access_payment_facilitator():
    return {"token": payments.app_token.access_token}


@bp.route("/payments/transfers", methods=["GET"])
@login_required
def get_transfers():
    limit = int(get_request_arg(request, "limit", True)) or 15
    offset = limit * int(get_request_arg(request, "offset", True)) or 0
    customer_url = current_user.dwolla_customer_url
    return payments.get_transfers(customer_url, limit, offset)


@bp.route("/payments/balance", methods=["GET"])
@login_required
def get_balance():
    customer_url = current_user.dwolla_customer_url
    return payments.get_balance(customer_url)


@bp.route("/payments/balance/add", methods=["POST"])
@login_required
def add_balance():
    location = get_request_json(request, "location")
    amount = get_request_json(request, "amount")
    customer_url = current_user.dwolla_customer_url
    balance = payments.get_balance(customer_url)["location"]
    response = payments.transfer_funds(str(amount), location, balance)
    if type(response) is tuple:
        return response
    emit_to_users(
        "ADD_TRANSFER",
        response["transfer"],
        get_manager_user_ids(current_user.organization_id),
    )
    return response


@bp.route("/payments/balance/remove", methods=["POST"])
@login_required
def remove_balance():
    location = get_request_json(request, "location")
    amount = get_request_json(request, "amount")
    customer_url = current_user.dwolla_customer_url
    balance = payments.get_balance(customer_url)["location"]
    if current_user.has_role("contractor"):
        user_ids = [current_user.id]
    else:
        user_ids = get_manager_user_ids(current_user.organization_id)
    response = payments.transfer_funds(str(amount), balance, location)
    new_balance = payments.get_balance(customer_url)["balance"]
    response["transfer"]["new_balance"] = new_balance
    emit_to_users("ADD_TRANSFER", response["transfer"], user_ids)
    emit_to_users("SET_BALANCE", new_balance, user_ids)
    return response


@bp.route("/payments/accounts", methods=["POST"])
@login_required
def add_account():
    public_token = get_request_json(request, "public_token", optional=True) or None
    account_id = get_request_json(request, "account_id", optional=True) or None
    account_name = get_request_json(request, "name")
    routing_number = get_request_json(request, "routing_number", optional=True) or None
    account_number = get_request_json(request, "account_number", optional=True) or None
    account_type = get_request_json(request, "account_type", optional=True) or None

    customer_url = current_user.dwolla_customer_url

    if public_token != None and account_id != None:
        dwolla_token = payments_auth.get_dwolla_token(public_token, account_id)
        response = payments.authenticate_funding_source(
            customer_url, dwolla_token, account_name
        )
    elif routing_number != None and account_number != None and account_type != None:
        response = payments.create_funding_source_micro(
            routing_number, account_number, account_type, account_name, customer_url
        )
    else:
        return {"message": "Please provide a valid request!"}, 403

    if current_user.has_role("contractor"):
        user_ids = [current_user.id]
    else:
        user_ids = get_manager_user_ids(current_user.organization_id)

    emit_to_users("ADD_FUNDING_SOURCE", response, user_ids)
    return response


@bp.route("/payments/accounts/verify", methods=["PUT"])
@login_required
def verify_micro():
    funding_source = get_request_json(request, "funding_source")
    amount1 = get_request_json(request, "amount1")
    amount2 = get_request_json(request, "amount2")
    result = payments.verify_micro_deposits(amount1, amount2, funding_source)

    if result[1] == 200:
        if current_user.has_role("contractor"):
            user_ids = [current_user.id]
        else:
            user_ids = get_manager_user_ids(current_user.organization_id)
        emit_to_users("ADD_FUNDING_SOURCE", result[0], user_ids)
    return result


@bp.route("/payments/accounts", methods=["GET"])
@login_required
def get_accounts():
    customer_url = current_user.dwolla_customer_url
    return payments.get_funding_sources(
        customer_url, current_user.has_role("contractor")
    )


@bp.route("/payments/accounts", methods=["PUT"])
@login_required
def edit_account():
    location = get_request_json(request, "_links")["self"]["href"]
    account_name = get_request_json(request, "name")
    if current_user.has_role("contractor"):
        user_ids = [current_user.id]
    else:
        user_ids = get_manager_user_ids(current_user.organization_id)
    response = payments.edit_funding_source(location, account_name)
    emit_to_users("ADD_FUNDING_SOURCE", response, user_ids)
    return response


@bp.route("/payments/accounts", methods=["DELETE"])
@login_required
def remove_account():
    location = get_request_json(request, "location")
    payments.remove_funding_source(location)
    if current_user.has_role("contractor"):
        user_ids = [current_user.id]
    else:
        user_ids = get_manager_user_ids(current_user.organization_id)
    emit_to_users("REMOVE_FUNDING_SOURCE", location, user_ids)
    return OK_RESPONSE


@bp.route("/payments/plaid-link-token", methods=["POST"])
@login_required
def get_link_token():
    return {"token": payments_auth.obtain_link_token(current_user.id)}


@bp.route("/payments/complete", methods=["PUT"])
@login_required
@roles_accepted("organization_manager", "contractor_manager")
def complete_payments():
    timecard_ids = get_request_json(request, "timecard_ids")
    timecards = (
        db.session.query(TimeCard, User)
        .filter(User.id == TimeCard.contractor_id, TimeCard.id.in_(timecard_ids))
        .all()
    )
    customer_url = current_user.dwolla_customer_url
    transfers = []
    for timecard in timecards:
        fees = None
        fee = timecard[0].fees_payment
        if fee > 0:
            fees = [
                {
                    "_links": {"charge-to": {"href": customer_url}},
                    "amount": {"value": str(fee), "currency": "USD"},
                }
            ]
        transfer = payments.transfer_funds(
            str(timecard[0].wage_payment),
            payments.get_balance(customer_url)["location"],
            payments.get_balance(timecard[1].dwolla_customer_url)["location"],
            fees,
        )
        if type(transfer) is not tuple:
            db.session.query(TimeCard).filter(TimeCard.id == timecard[0].id).update(
                {TimeCard.paid: True}
            )
            message_body = (
                "You received a payment for $" + str(timecard[0].wage_payment) + "."
            )
            notifications.send_notification(
                "You've been paid!", message_body, [timecard[0].contractor_id]
            )
        transfers.append(transfer["transfer"])
    db.session.commit()
    response = transfers
    user_ids = get_manager_user_ids(current_user.organization_id)

    for transfer in transfers:
        # TODO: When a contractor has multiple shifts approved their transfer history will only show
        # a single transfer of the last amount. This can be fixed by querying on transfer id.
        receiving_customer_url = transfer["_links"]["destination"]["href"]
        receiving_user_id = [
            db.session.query(ContractorInfo.id)
            .filter(ContractorInfo.dwolla_customer_url == receiving_customer_url)
            .one()[0]
        ]
        receiving_transfer = payments.get_transfers(receiving_customer_url, 1, 0)[
            "transfers"
        ][0]
        receiving_balance = payments.get_balance(receiving_customer_url)["balance"]
        emit_to_users("SET_BALANCE", receiving_balance, receiving_user_id)
        emit_to_users("ADD_TRANSFER", receiving_transfer, receiving_user_id)
        emit_to_users("ADD_TRANSFER", transfer, user_ids)

    for timecard_id in timecard_ids:
        emit_to_users("REMOVE_TIMECARD", timecard_id, user_ids)

    balance = payments.get_balance(customer_url)["balance"]
    emit_to_users("SET_BALANCE", balance, user_ids)

    return {"transfers": response, "balance": balance}


@bp.route("/payments/deny", methods=["PUT"])
@login_required
@roles_accepted("organization_manager", "contractor_manager")
def deny_payment():
    timecard_ids = get_request_json(request, "timecard_ids")
    db.session.query(TimeCard).filter(TimeCard.id.in_(timecard_ids)).update(
        {TimeCard.denied: True}, synchronize_session=False
    )
    db.session.commit()
    user_ids = get_manager_user_ids(current_user.organization_id)

    for timecard_id in timecard_ids:
        emit_to_users("REMOVE_TIMECARD", timecard_id, user_ids)
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
            TimeCard.total_payment != None,
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
    user_ids = get_manager_user_ids(current_user.organization_id)

    emit_to_users("ADD_TIMECARD", result, user_ids)

    return result


@bp.route("/payments", methods=["GET"])
@login_required
def get_payments():
    payments = (
        db.session.query(Payment)
        .filter(
            Payment.date_completed == None,
            or_(
                Payment.sender_dwolla_url == current_user.dwolla_customer_url,
                Payment.receiver_dwolla_url == current_user.dwolla_customer_url,
            ),
        )
        .all()
    )
    result = []
    for payment in payments:
        result.append(payment.to_dict())
    return {"payments":result}


@bp.route("/payments/invoices", methods=["POST"])
@login_required
def create_invoice():
    description = get_request_json(request, "description", optional=True) or None
    items = get_request_json(request, "items")
    invoice = Invoice(
        description=description, date_created=datetime.utcnow()
    )
    db.session.add(invoice)
    db.session.commit()
    amount = 0.0
    for item in items:
        item = InvoiceItem(
            description=item["description"],
            amount=item["amount"],
            invoice_id=invoice.id
        )
        amount += item.amount
        db.session.add(item)
    invoice.amount = amount
    db.session.commit()
    payment = Payment(
        amount=invoice.amount,
        invoice_id=invoice.id,
        sender_dwolla_url=current_user.organization.dwolla_customer_url,
        receiver_dwolla_url=current_user.dwolla_customer_url
    )
    db.session.add(payment)
    db.session.commit()
    return update_payment(invoice.id)


@bp.route("/payments/invoices/<invoice_id>", methods=["PUT"])
@login_required
def edit_invoice(invoice_id):
    invoice_items = get_request_json(request, "items")
    description = get_request_json(request, "description", optional=True) or None
    invoice_ids = (
        db.session.query(InvoiceItem.id).filter(InvoiceItem.invoice_id == invoice_id).all()
    )
    x = 0
    for i in invoice_ids:
        invoice_ids[x] = i[0]
        x += 1

    for item in invoice_items:
        if "id" in item:
            invoice_ids.remove(item["id"])
            db.session.query(InvoiceItem).filter(InvoiceItem.id == item["id"]).update(
                {
                    InvoiceItem.amount: item["amount"] or InvoiceItem.amount,
                    InvoiceItem.description: item["description"] or InvoiceItem.description,
                }
            )
        else:
            i = InvoiceItem(
                invoice_id=invoice_id,
                description=item["description"],
                amount=item["amount"],
            )
            db.session.add(i)
    db.session.query(InvoiceItem).filter(InvoiceItem.id.in_(invoice_ids)).delete(
        synchronize_session="fetch"
    )
    db.session.query(Invoice).filter(Invoice.id == invoice_id).update(
        {
            Invoice.description: description or Invoice.description,
        }
    )
    db.session.commit()
    return update_invoice(invoice_id)

def update_invoice(invoice_id):
    invoice = db.session.query(Invoice).filter(Invoice.id == invoice_id).one()
    amount = 0
    for item in invoice.items:
        amount += item.amount
    db.session.query(Invoice).filter(Invoice.id == invoice_id).update(
        {
            Invoice.amount: amount
        }
    )
    db.session.commit()
    return update_payment(invoice_id)

def update_payment(invoice_id):
    payment = db.session.query(Payment).filter(Payment.invoice_id == invoice_id).one()
    organization = db.session.query(Organization).filter(Organization.dwolla_customer_url == payment.sender_dwolla_url).one()
    transaction_fee = round(payment.amount * organization.subscription_tier.transfer_fee, 2)
    total = payment.amount + transaction_fee
    db.session.query(Payment).filter(Payment.invoice_id == invoice_id).update(
        {
            Payment.fee: transaction_fee,
            Payment.total: total
        }
    )
    db.session.commit()
    return payment.to_dict()
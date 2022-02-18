from datetime import datetime
from flask import request
from flask_security import login_required, roles_accepted, current_user
from sqlalchemy.sql.elements import Null, or_

from app import db, payments, payments_auth, notifications
from app.api import bp
from app.errors.customs import MissingParameterException
from app.models import (
    BankTransfer,
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
    fee = round(
        amount * current_user.organization.subscription_tier.business_ach_fee, 2
    )
    amount = amount - fee
    if fee > 0.0:
        response = payments.transfer_funds(str(amount), location, balance, fee)
    else:
        response = payments.transfer_funds(str(amount), location, balance)
    if type(response) is tuple:
        return response
    transfer = BankTransfer(
        amount=float(response["transfer"]["amount"]["value"]),
        transaction_type="debit",
        status=response["transfer"]["status"],
        status_updated=response["transfer"]["created"],
    )
    db.session.add(transfer)
    db.session.commit()
    payment = Payment(
        amount=transfer.amount,
        fee=fee,
        total=amount + fee,
        bank_transfer_id=transfer.id,
        date_completed=datetime.utcnow(),
        dwolla_payment_transaction_id=response["transfer"]["id"],
        sender_dwolla_url=current_user.dwolla_customer_url,
        receiver_dwolla_url=current_user.dwolla_customer_url,
    )
    db.session.add(payment)
    db.session.commit()
    emit_to_users(
        "ADD_TRANSFER",
        payment.to_dict(),
        get_manager_user_ids(current_user.organization_id),
    )
    return payment.to_dict()


@bp.route("/payments/balance/remove", methods=["POST"])
@login_required
def remove_balance():
    location = get_request_json(request, "location")
    amount = get_request_json(request, "amount")
    customer_url = current_user.dwolla_customer_url
    balance = payments.get_balance(customer_url)["location"]
    if current_user.has_role("contractor"):
        user_ids = [current_user.id]
        fee = round(
            amount
            * float(current_user.organization.subscription_tier.contractor_ach_fee),
            2,
        )
        amount = amount - fee
    else:
        user_ids = get_manager_user_ids(current_user.organization_id)
        fee = round(
            amount
            * float(current_user.organization.subscription_tier.business_ach_fee),
            2,
        )
        amount = amount - fee
    if fee > 0.0:
        fee_request = [
            {
                "_links": {"charge-to": {"href": customer_url}},
                "amount": {"value": str(fee), "currency": "USD"},
            }
        ]
        response = payments.transfer_funds(str(amount), balance, location, None)
    else:
        response = payments.transfer_funds(str(amount), balance, location)
    transfer = BankTransfer(
        amount=float(response["transfer"]["amount"]["value"]),
        transaction_type="credit",
        status=response["transfer"]["status"],
        status_updated=response["transfer"]["created"],
    )
    db.session.add(transfer)
    db.session.commit()
    payment = Payment(
        amount=transfer.amount,
        bank_transfer_id=transfer.id,
        date_completed=datetime.utcnow(),
        dwolla_payment_transaction_id=response["transfer"]["id"],
        sender_dwolla_url=current_user.dwolla_customer_url,
        receiver_dwolla_url=current_user.dwolla_customer_url,
    )
    db.session.add(payment)
    db.session.commit()
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
    payment_ids = get_request_json(request, "payment_ids")
    payments_res = (
        db.session.query(Payment)
        .filter(
            Payment.id.in_(payment_ids), Payment.dwolla_payment_transaction_id == None
        )
        .all()
    )
    response = {"payments": []}
    user_ids = get_manager_user_ids(current_user.organization_id)
    customer_urls = []
    for payment in payments_res:
        customer_url = payment.sender_dwolla_url
        if customer_url not in customer_urls:
            customer_urls.append(customer_url)
        fees = None
        fee = payment.fee
        if fee > 0:
            fees = [
                {
                    "_links": {"charge-to": {"href": customer_url}},
                    "amount": {"value": str(fee), "currency": "USD"},
                }
            ]
        transfer = payments.transfer_funds(
            str(payment.amount),
            payments.get_balance(customer_url)["location"],
            payments.get_balance(payment.receiver_dwolla_url)["location"],
            fees,
        )
        if type(transfer) is not tuple:
            db.session.query(Payment).filter(Payment.id == payment.id).update(
                {Payment.dwolla_payment_transaction_id: transfer["transfer"]["id"]}
            )
            message_body = "You received a payment for $" + str(payment.amount) + "."
            if payment.receiver is User:
                notifications.send_notification(
                    "You've been paid!", message_body, [payment.receiver.id]
                )

        # Handle real time notifications
        receiving_user_id = [
            db.session.query(ContractorInfo.id)
            .filter(ContractorInfo.dwolla_customer_url == payment.receiver_dwolla_url)
            .one()[0]
        ]
        receiving_balance = payments.get_balance(payment.receiver_dwolla_url)["balance"]
        emit_to_users("SET_BALANCE", receiving_balance, receiving_user_id)
        emit_to_users("ADD_PAYMENT", payment.to_dict(), receiving_user_id)
        # emit_to_users("ADD_PAYMENT", transfer, user_ids)

        response["payments"].append(payment.to_dict())
    db.session.commit()

    for customer_url in customer_urls:
        balance = payments.get_balance(customer_url)["balance"]
        emit_to_users("SET_BALANCE", balance, user_ids)

    return {"payments": response["payments"], "balance": balance}


@bp.route("/payments/deny", methods=["PUT"])
@login_required
@roles_accepted("organization_manager", "contractor_manager")
def deny_payment():
    payment_ids = get_request_json(request, "payment_ids")
    db.session.query(Payment).filter(Payment.id.in_(payment_ids)).update(
        {Payment.denied: True}, synchronize_session=False
    )
    db.session.commit()
    user_ids = get_manager_user_ids(current_user.organization_id)

    for payment_id in payment_ids:
        emit_to_users("REMOVE_PAYMENT", payment_id, user_ids)
    return OK_RESPONSE


@bp.route("/payments/<payment_id>", methods=["PUT"])
@login_required
def edit_payment_route(payment_id):
    timecard_changes = (
        get_request_json(request, "timecard.clock_events", optional=True) or None
    )
    invoice_items = get_request_json(request, "invoice.items", optional=True) or None
    invoice_description = (
        get_request_json(request, "invoice.description", optional=True) or None
    )
    payment = db.session.query(Payment).filter(Payment.id == payment_id).one()
    if timecard_changes != None:
        edit_timecard(payment.invoice.timecard_id, timecard_changes)
    if invoice_items != None:
        edit_invoice(payment.invoice_id, invoice_items, invoice_description)

    # TODO: There may be a better way to do this than querying again,
    # TODO: but Jackson didn't return the object so I'm doing his job
    payment = db.session.query(Payment).filter(Payment.id == payment_id).one()

    return payment.to_dict()


def edit_timecard(timecard_id, changes):
    timecard = db.session.query(TimeCard).filter(TimeCard.id == timecard_id).one()
    contractor_id = timecard.contractor_id

    for i in changes:
        db.session.query(TimeClock).filter(TimeClock.id == i["id"]).update(
            {TimeClock.time: i["time"]}, synchronize_session=False
        )

    db.session.commit()
    calculate_timecard(timecard.id)
    invoice = db.session.query(Invoice).filter(Invoice.timecard_id == timecard_id).one()
    update_invoice(invoice.id)
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
            or_(
                Payment.sender_dwolla_url == current_user.dwolla_customer_url,
                Payment.receiver_dwolla_url == current_user.dwolla_customer_url,
            ),
            Payment.denied == False,
        )
        .all()
    )
    result = []
    for payment in payments:
        result.append(payment.to_dict())
    return {"payments": result}


@bp.route("/payments/<payment_id>", methods=["GET"])
@login_required
def get_payment(payment_id):
    payment = db.session.query(Payment).filter(Payment.id == payment_id).one()
    return payment.to_dict()


@bp.route("/payments/invoices", methods=["POST"])
@login_required
def create_invoice():
    description = get_request_json(request, "description", optional=True) or None
    items = get_request_json(request, "items")
    invoice = Invoice(description=description, date_created=datetime.utcnow())
    db.session.add(invoice)
    db.session.commit()
    amount = 0.0
    for item in items:
        item = InvoiceItem(
            description=item["description"],
            amount=item["amount"],
            invoice_id=invoice.id,
        )
        amount += item.amount
        db.session.add(item)
    invoice.amount = amount
    db.session.commit()
    payment = Payment(
        amount=invoice.amount,
        invoice_id=invoice.id,
        sender_dwolla_url=current_user.organization.dwolla_customer_url,
        receiver_dwolla_url=current_user.dwolla_customer_url,
    )
    db.session.add(payment)
    db.session.commit()
    return update_payment(invoice.id)


@bp.route("/payments/invoices/<invoice_id>", methods=["PUT"])
@login_required
def edit_invoice_route(invoice_id):
    invoice_items = get_request_json(request, "items")
    description = get_request_json(request, "description", optional=True) or None
    return edit_invoice(invoice_id, invoice_items, description)


def edit_invoice(invoice_id, invoice_items, description):
    invoice_ids = (
        db.session.query(InvoiceItem.id)
        .filter(InvoiceItem.invoice_id == invoice_id)
        .all()
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
                    InvoiceItem.description: item["description"]
                    or InvoiceItem.description,
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
    if invoice.timecard:
        amount += invoice.timecard.wage_payment
    db.session.query(Invoice).filter(Invoice.id == invoice_id).update(
        {Invoice.amount: amount}
    )
    db.session.commit()
    return update_payment(invoice_id)


def update_payment(invoice_id):
    payment = db.session.query(Payment).filter(Payment.invoice_id == invoice_id).one()
    if payment.invoice:
        payment.amount = payment.invoice.amount
    organization = (
        db.session.query(Organization)
        .filter(Organization.dwolla_customer_url == payment.sender_dwolla_url)
        .one()
    )
    transaction_fee = round(
        payment.amount * organization.subscription_tier.transfer_fee, 2
    )
    total = round(payment.amount + transaction_fee, 2)
    db.session.query(Payment).filter(Payment.invoice_id == invoice_id).update(
        {Payment.fee: transaction_fee, Payment.total: total}
    )
    db.session.commit()
    return payment.to_dict()

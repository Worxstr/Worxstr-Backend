from flask import request
from flask_security import login_required, roles_accepted

from app import db
from app.api import bp
from app.api.paypal import GetOrder, SendPayouts
from app.errors.customs import MissingParameterException
from app.models import TimeCard, User, TimeClock
from app.utils import OK_RESPONSE, get_request_arg, get_request_json
from app import payments


@bp.route("/payments/access", methods=["POST"])
def access_payment_facilitator():
    return {"token": payments.app_token.access_token}


@bp.route("/payments/approve", methods=["PUT"])
@bp.route("/payments/deny", methods=["PUT"])
@login_required
@roles_accepted("organization_manager", "contractor_manager")
def approve_payment():
    timecards = get_request_json(request, "timecards")

    ids = []
    for timecard in timecards:
        ids.append(timecard["id"])
        if "denied" in timecard.keys():
            db.session.query(TimeCard).filter(TimeCard.id == timecard["id"]).update(
                {TimeCard.denied: timecard["denied"]}, synchronize_session=False
            )
        else:
            db.session.query(TimeCard).filter(TimeCard.id == timecard["id"]).update(
                {
                    TimeCard.approved: timecard["approved"],
                    TimeCard.paid: (not timecard["paypal"]),
                },
                synchronize_session=False,
            )
    db.session.commit()
    timecards = db.session.query(TimeCard).filter(TimeCard.id.in_(ids)).all()
    result = []

    for timecard in [t.to_dict() for t in timecards]:
        timecard["first_name"] = (
            db.session.query(User.first_name)
            .filter(User.id == timecard["contractor_id"])
            .one()[0]
        )
        timecard["last_name"] = (
            db.session.query(User.last_name)
            .filter(User.id == timecard["contractor_id"])
            .one()[0]
        )
        timecard["time_clocks"] = [
            i.to_dict()
            for i in db.session.query(TimeClock)
            .filter(TimeClock.timecard_id == timecard["id"])
            .all()
        ]
        result.append(timecard)

    return {"event": result}


@bp.route("/payments/complete", methods=["PUT"])
@login_required
@roles_accepted("organization_manager", "contractor_manager")
def add_order_id():
    timecards = get_request_json(request, "timecards")
    order_id = get_request_json(request, "transaction").get("orderID")
    if order_id is None:
        raise MissingParameterException("Request attribute not found: orderID")

    order_confirmation = GetOrder().get_order(order_id)

    if order_confirmation["status"] == GetOrder.ORDER_APPROVED:
        payments = []
        total_payment = 0.0
        for i in timecards:
            total_payment = total_payment + float(i["total_payment"])

            email = (
                db.session.query(User.email).filter(User.id == i["contractor_id"]).one()
            )
            payment = {
                "email": email[0],
                "note": "Payment",
                "payment": str(
                    round(float(i["wage_payment"]) - float(i["fees_payment"]), 2)
                ),
            }
            payments.append(payment)
            db.session.query(TimeCard).filter(TimeCard.id == i["id"]).update(
                {TimeCard.transaction_id: order_id}, synchronize_session=False
            )
        db.session.commit()
        if float(order_confirmation["gross_amount"]) == total_payment:
            payout_id = SendPayouts().send_payouts(payments)
            for i in get_request_json(request, "timecards", optional=True):
                db.session.query(TimeCard).filter(TimeCard.id == i["id"]).update(
                    {TimeCard.payout_id: payout_id, TimeCard.paid: True},
                    synchronize_session=False,
                )
            db.session.commit()

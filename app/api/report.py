import os
from requests import Response
from sqlalchemy import desc, or_
import xlsxwriter
from flask_security import current_user, login_required, roles_accepted
from app import db
from app.api import bp
from flask import request
from app.models import ContractorInfo, Invoice, Job, Payment, ScheduleShift, User
from flask import request, send_from_directory
from app.utils import (
    OK_RESPONSE,
    get_request_arg,
    list_to_csv,
    flatten_dict_list,
    flatten_dict,
)
from config import Config
import json


@bp.route("/reports", methods=["GET"])
@login_required
@roles_accepted("organization_manager", "contractor_manager")
def export_payments():
    report_type = get_request_arg(request, "report_type")
    if report_type == "payments":
        filters = [
            or_(
                Payment.sender_dwolla_url == current_user.dwolla_customer_url,
                Payment.receiver_dwolla_url == current_user.dwolla_customer_url,
            ),
            Payment.denied == False,
        ]
        payments = (
            db.session.query(Payment)
            .filter(*filters)
            .order_by(desc(Payment.date_created))
            .all()
        )

        data = []
        for payment in payments:
            payment = payment.to_dict()
            data.append(
                {
                    "total": payment.get("total"),
                    "amount": payment.get("amount"),
                    "fee": payment.get("fee"),
                    "date_created": payment.get("date_created"),
                    "date_completed": payment.get("date_completed"),
                }
            )

        format = request.args.get("format")

        if format == "csv":
            filename = "payments_export.csv"
            mimetype = "text/csv"
            output = list_to_csv(data)

        elif format == "json":
            filename = "payments_export.json"
            mimetype = "application/json"
            output = json.dumps(data)

        # elif format == 'xlsx':
        #     filename = "payments_export.xlsx"
        #     mimetype = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        #     output = list_to_xlsx(data)

        # elif format == 'pdf':
        #     filename = "payments_export.pdf"
        #     mimetype = "application/pdf"
        #     output = list_to_pdf(data)

        else:
            return "Invalid format provided", 400

        return Response(
            output,
            # mimetype=mimetype,
            headers={"Content-disposition": "attachment; filename=" + filename},
        )
    elif report_type == "time":
        start_date = get_request_arg(request, "start_date")
        end_date = get_request_arg(request, "end_date")

        invoices = (
            db.session.query(Invoice)
            .filter(
                Invoice.job.has(organization_id=current_user.organization_id),
                Invoice.date_created > start_date,
                Invoice.date_created < end_date,
            )
            .all()
        )
        jobs = list(set([invoice.job for invoice in invoices]))
        filename = "ContractorPayByJob" + start_date + "-" + end_date + ".xlsx"
        workbook = xlsxwriter.Workbook(os.path.join(Config.DOWNLOAD_FOLDER, filename))
        for job in jobs:
            worksheet = workbook.add_worksheet(job.name)
            row = 0
            col = 0
            worksheet.write(row, col, "First Name")
            worksheet.write(row, col + 1, "Last Name")
            row += 1
            invoice_ids = []
            for invoice in invoices:
                if invoice.job == job:
                    invoice_ids.append(invoice.id)
            payments = (
                db.session.query(Payment)
                .filter(
                    Payment.invoice_id.in_(invoice_ids),
                    Payment.date_created > start_date,
                    Payment.date_created < end_date,
                )
                .all()
            )
            recipient_dwolla_urls = list(
                set([payment.receiver_dwolla_url for payment in payments])
            )
            recipients = list(
                set(
                    db.session.query(User, ContractorInfo)
                    .filter(
                        ContractorInfo.dwolla_customer_url.in_(recipient_dwolla_urls)
                    )
                    .all()
                )
            )
            for recipient in recipients:
                recipient = recipient[0]
                worksheet.write(row, col, recipient.first_name)
                worksheet.write(row, col + 1, recipient.last_name)
                row += 1
        workbook.close()
        return send_from_directory(Config.DOWNLOAD_FOLDER, filename)

import os
import xlsxwriter
from flask_login import current_user, login_required
from app import db
from app.api import bp
from flask import request
from app.models import ContractorInfo, Invoice, Job, Payment, ScheduleShift, User
from flask import request, send_from_directory
from app.utils import OK_RESPONSE, get_request_arg
from config import Config

@bp.route("/reports/job", methods=["GET"])
@login_required
def get_contractor_pay_by_job():
    start_date = get_request_arg(request, "start_date")
    end_date = get_request_arg(request, "end_date")

    invoices = db.session.query(Invoice).filter(Invoice.job.has(organization_id = current_user.organization_id), Invoice.date_created > start_date, Invoice.date_created < end_date).all()
    jobs = list(set([invoice.job for invoice in invoices]))
    filename = 'ContractorPayByJob' + start_date + '-' + end_date + '.xlsx'
    workbook = xlsxwriter.Workbook(os.path.join(Config.DOWNLOAD_FOLDER, filename))
    for job in jobs:
        worksheet = workbook.add_worksheet(job.name)
        row = 0
        col = 0
        worksheet.write(row, col, 'First Name')
        worksheet.write(row, col+1, 'Last Name')
        row += 1
        invoice_ids = []
        for invoice in invoices:
            if invoice.job == job:
                invoice_ids.append(invoice.id)
        payments = db.session.query(Payment).filter(Payment.invoice_id.in_(invoice_ids), Payment.date_created > start_date, Payment.date_created < end_date).all()
        recipient_dwolla_urls = list(set([payment.receiver_dwolla_url for payment in payments]))
        recipients = list(set(db.session.query(User, ContractorInfo).filter(ContractorInfo.dwolla_customer_url.in_(recipient_dwolla_urls)).all()))
        for recipient in recipients:
            recipient = recipient[0]
            worksheet.write(row, col, recipient.first_name)
            worksheet.write(row, col+1, recipient.last_name)
            row += 1
    workbook.close()
    return send_from_directory(Config.DOWNLOAD_FOLDER, filename)


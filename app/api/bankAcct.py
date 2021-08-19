# Read env vars from .env file
from plaid.model.payment_amount import PaymentAmount
from plaid.model.products import Products
from plaid.model.numbers_bacs_nullable import NumbersBACSNullable
from plaid.model.payment_initiation_address import PaymentInitiationAddress
from plaid.model.payment_initiation_recipient_create_request import PaymentInitiationRecipientCreateRequest
from plaid.model.payment_initiation_payment_create_request import PaymentInitiationPaymentCreateRequest
from plaid.model.payment_initiation_payment_get_request import PaymentInitiationPaymentGetRequest
from plaid.model.link_token_create_request_payment_initiation import LinkTokenCreateRequestPaymentInitiation
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.asset_report_create_request import AssetReportCreateRequest
from plaid.model.asset_report_create_request_options import AssetReportCreateRequestOptions
from plaid.model.asset_report_user import AssetReportUser
from plaid.model.asset_report_get_request import AssetReportGetRequest
from plaid.model.asset_report_pdf_get_request import AssetReportPDFGetRequest
from plaid.model.auth_get_request import AuthGetRequest
from plaid.model.transactions_get_request import TransactionsGetRequest
from plaid.model.transactions_get_request_options import TransactionsGetRequestOptions
from plaid.model.identity_get_request import IdentityGetRequest
from plaid.model.investments_transactions_get_request_options import InvestmentsTransactionsGetRequestOptions
from plaid.model.investments_transactions_get_request import InvestmentsTransactionsGetRequest
from plaid.model.accounts_balance_get_request import AccountsBalanceGetRequest
from plaid.model.accounts_get_request import AccountsGetRequest
from plaid.model.investments_holdings_get_request import InvestmentsHoldingsGetRequest
from plaid.model.item_get_request import ItemGetRequest
from plaid.model.institutions_get_by_id_request import InstitutionsGetByIdRequest
from plaid.api import plaid_api
from flask import Flask
from flask import render_template
from flask import request
from flask import jsonify
from datetime import datetime
from datetime import timedelta
import plaid
import base64
import os
import datetime
import json
import time
from app.api import bp

from dotenv import load_dotenv
load_dotenv()


client_id = os.environ.get('PLAID_CLIENT_ID')
secret = os.environ.get("PLAID_SECRET")
host = os.environ.get("PLAID_ENV")
client_name=os.environ.get("PLAID_TEST_CLIENT_NAME")
products=os.environ.get("PLAID_PRODUCTS")
country_codes = os.environ.get("PLAID_COUNTRY_CODES")
access_token = None
item_id = None

# set configuration for plaid Endpoints

config = plaid.Configuration(
    host=host,
    api_key={
        'clientId': client_id,
        'secret': secret,
    }
)
api_client =plaid.ApiClient(config)
client = plaid_api.PlaidApi(api_client)
#



@bp.route("/item/create_link_token/",methods=['POST'])
def obtain_processor_token():

    request = LinkTokenCreateRequest(client_name=client_name,
                           country_codes=country_codes,
                           language='en',
                           user=LinkTokenCreateRequestUser(
                               client_user_id=str(time.time())
                           )
                        )

    print(request.to_dict())
    return request.to_str()

# Create a link_token for the given user



   # exchange_token_response = client.Item.public_token.exchange('[Plaid Link public_token]')
    #access_token = exchange_token_response['access_token']

"""
@bp.route()
def create_funding_src():

@bp.route()
def get_routing_and_acct_num():

@bp.route()
def get_funding_src():
"""

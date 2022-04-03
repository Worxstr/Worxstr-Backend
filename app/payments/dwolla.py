import dwollav2
from dwollav2.error import ValidationError, NotFoundError
from functools import wraps


def catch_errors(f):
    @wraps(f)
    def inner(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ValidationError as ex:
            print(ex)
            error = ex.body["_embedded"]["errors"][0]
            if error["code"] == "Restricted":
                return {
                    "message": "Beneficial owner information required. Please check settings.",
                    "error": error,
                    "actions": [
                        {"name": "VERIFY_BENEFICIAL_OWNERS", "action_text": "Verify"}
                    ],
                }, 401
            if error["code"] == "Duplicate":
                return {
                    "message": "That email is already in use.",
                    "error": error,
                }, 401
            return {
                "message": error["message"],
                "error": error,
            }, 400
        except NotFoundError as ex:
            return {"message": ex.body["message"], "error": ex.body["code"]}

    return inner


class Dwolla:
    app_token = None
    client = None
    secret = None
    url = None

    def __init__(self, app_key, app_secret, host, secret, url):
        self.client = dwollav2.Client(key=app_key, secret=app_secret, environment=host)
        self.secret = secret
        self.url = url
        self.refresh_app_token()
        if "localhost" not in self.url:
            self.subscribe_webhooks()

    def refresh_app_token(self):
        self.app_token = self.client.Auth.client()

    def subscribe_webhooks(self):
        webhook_subscriptions = self.app_token.get("webhook-subscriptions")
        if webhook_subscriptions.body["total"] > 0:
            for webhook in webhook_subscriptions.body["_embedded"][
                "webhook-subscriptions"
            ]:
                self.app_token.delete(webhook["_links"]["self"]["href"])

        request_body = {
            "url": "https://" + self.url + "/payments/accounts/status",
            "secret": self.secret,
        }
        self.app_token.post("webhook-subscriptions", request_body)

    @catch_errors
    def get_customer_info(self, customer_url):
        customer = self.app_token.get(customer_url)
        return customer.body

    @catch_errors
    def authenticate_funding_source(self, customer_url, plaid_token, source_name):
        request_body = {"plaidToken": plaid_token, "name": source_name}
        customer = self.app_token.post(
            "%s/funding-sources" % customer_url, request_body
        )
        return self.get_customer_info(customer.headers["location"])

    @catch_errors
    def get_funding_sources(self, customer_url, is_contractor):
        funding_sources = self.app_token.get("%s/funding-sources" % customer_url)
        ownership_flag = None
        if not is_contractor:
            try:
                beneficial_ownership = self.app_token.get(
                    "%s/beneficial-ownership" % customer_url
                )
                if beneficial_ownership.body["status"] == "certified":
                    ownership_flag = True
                else:
                    ownership_flag = False
            except NotFoundError as ex:
                print(ex)
                code = ex.body["code"]
                if code == "NotFound":
                    ownership_flag = True
        result = []
        for funding_source in funding_sources.body["_embedded"]["funding-sources"]:
            if not funding_source["removed"] and funding_source["type"] != "balance":
                result.append(funding_source)

        return {"funding_sources": result, "certified_ownership": ownership_flag}

    @catch_errors
    def edit_funding_source(self, location, account_name):
        request_body = {"name": account_name}
        funding_source = self.app_token.post(location, request_body)
        return self.get_customer_info(location)

    @catch_errors
    def remove_funding_source(self, location):
        request_body = {"removed": True}
        funding_source = self.app_token.post(location, request_body)
        return

    @catch_errors
    def transfer_funds(
        self, amount, source, destination, fees=None, transfer_speed="standard"
    ):
        request_body = {
            "_links": {
                "source": {"href": source},
                "destination": {"href": destination},
            },
            "amount": {"currency": "USD", "value": amount},
            "clearing": {"source": transfer_speed},
        }
        if fees != None:
            request_body["fees"] = fees

        transfer = self.app_token.post("transfers", request_body)

        transfer_obj = self.get_customer_info(transfer.headers._store["location"][1])
        transfer_obj["_links"]["destination"][
            "additional-information"
        ] = self.get_customer_info(transfer_obj["_links"]["destination"]["href"])
        transfer_obj["_links"]["source"][
            "additional-information"
        ] = self.get_customer_info(transfer_obj["_links"]["source"]["href"])
        return {"transfer": transfer_obj}

    @catch_errors
    def get_transfers(self, customer_url, limit, offset):

        request_body = {"limit": limit, "offset": offset}
        transfers = self.app_token.get("%s/transfers" % customer_url, request_body)
        result = {"transfers": transfers.body["_embedded"]["transfers"]}

        for transfer in result["transfers"]:
            transfer["_links"]["destination"][
                "additional-information"
            ] = self.get_customer_info(transfer["_links"]["destination"]["href"])
            transfer["_links"]["source"][
                "additional-information"
            ] = self.get_customer_info(transfer["_links"]["source"]["href"])

        return result

    @catch_errors
    def get_balance(self, customer_url):
        funding_sources = self.app_token.get("%s/funding-sources" % customer_url)
        balance_location = ""

        for source in funding_sources.body["_embedded"]["funding-sources"]:
            if source["type"] == "balance":
                balance_location = source["_links"]["self"]["href"]

        balance = self.app_token.get("%s/balance" % balance_location)
        return {"balance": balance.body["balance"], "location": balance_location}

    @catch_errors
    def create_personal_customer(self, request_body):
        customer = self.app_token.post("customers", request_body)
        return customer.headers["location"]

    @catch_errors
    def create_business_customer(self, request_body):
        customer = self.app_token.post("customers", request_body)
        return customer.headers["location"]

    @catch_errors
    def retry_personal_customer(self, request_body, customer_url):
        self.app_token.post(customer_url, request_body)
        return self.get_customer_info(customer_url)["status"]

    @catch_errors
    def retry_business_customer(self, request_body, customer_url):
        self.app_token.post(customer_url, request_body)
        return self.get_customer_info(customer_url)["status"]

    @catch_errors
    def create_funding_source_micro(
        self, routing_number, account_number, account_type, name, customer_url
    ):
        request_body = {
            "routingNumber": routing_number,
            "accountNumber": account_number,
            "bankAccountType": account_type,
            "name": name,
        }
        account = self.app_token.post("%s/funding-sources" % customer_url, request_body)
        funding_source_url = account.headers["location"]
        self.app_token.post("%s/micro-deposits" % funding_source_url)
        return self.get_customer_info(funding_source_url)

    @catch_errors
    def verify_micro_deposits(self, amount1, amount2, funding_source_url):
        request_body = {
            "amount1": {"value": amount1, "currency": "USD"},
            "amount2": {"value": amount2, "currency": "USD"},
        }
        result = self.app_token.post(
            "%s/micro-deposits" % funding_source_url, request_body
        )
        if result.status == 200:
            return self.get_customer_info(funding_source_url), 200
        elif result == 202:
            return {"message": "Try again later. Deposits have not settled."}, 202
        elif result == 400:
            return {"message": "Wrong amount(s)"}, 400
        elif result == 403:
            return {"message": "Account already verified or too many attempts."}, 403
        elif result == 404:
            return {"message": "Funding source not found!"}, 404
        else:
            return {
                "message": "Internal server error. Please contact support issue persists"
            }, 500

import dwollav2
from dwollav2.error import ValidationError


class Dwolla:
    app_token = None
    client = None

    def __init__(self, app_key, app_secret, host):
        self.client = dwollav2.Client(key=app_key, secret=app_secret, environment=host)

        self.refresh_app_token()

    def refresh_app_token(self):
        self.app_token = self.client.Auth.client()

    def get_customer_info(self, customer_url):
        customer = self.app_token.get(customer_url)
        return customer.body

    def authenticate_funding_source(self, customer_url, plaid_token, source_name):
        request_body = {"plaidToken": plaid_token, "name": source_name}
        customer = self.app_token.post(
            "%s/funding-sources" % customer_url, request_body
        )
        return self.get_customer_info(customer.headers["location"])

    def get_funding_sources(self, customer_url, is_contractor):
        funding_sources = self.app_token.get("%s/funding-sources" % customer_url)
        ownership_flag = None
        if not is_contractor:
            beneficial_ownership = self.app_token.get(
                "%s/beneficial-ownership" % customer_url
            )
            if beneficial_ownership.body["status"] == "certified":
                ownership_flag = True
            else:
                ownership_flag = False
        result = []
        for funding_source in funding_sources.body["_embedded"]["funding-sources"]:
            if not funding_source["removed"] and funding_source["type"] != "balance":
                result.append(funding_source)

        return {"funding_sources": result, "certified_ownership": ownership_flag}

    def edit_funding_source(self, location, account_name):
        request_body = {"name": account_name}
        funding_source = self.app_token.post(location, request_body)
        return self.get_customer_info(location)

    def remove_funding_source(self, location):
        request_body = {"removed": True}
        funding_source = self.app_token.post(location, request_body)
        return

    def transfer_funds(self, amount, source, destination, fees=None):
        request_body = {
            "_links": {
                "source": {"href": source},
                "destination": {"href": destination},
            },
            "amount": {"currency": "USD", "value": amount},
        }
        if fees != None:
            request_body["fees"] = fees
        try:
            transfer = self.app_token.post("transfers", request_body)
        except ValidationError as e:
            # TODO: If there is a an error raised while exectued /payments/complete this is added to the response
            return {
                "message": "Beneficial owner information required. Please check settings.",
                "error": e.body["_embedded"]["errors"][0]["message"],
                "actions": [
                    {"name": "VERIFY_BENEFICIAL_OWNERS", "action_text": "Verify"}
                ],
            }, 401
        transfer_obj = self.get_customer_info(transfer.headers._store["location"][1])
        transfer_obj["_links"]["destination"][
            "additional-information"
        ] = self.get_customer_info(transfer_obj["_links"]["destination"]["href"])
        transfer_obj["_links"]["source"][
            "additional-information"
        ] = self.get_customer_info(transfer_obj["_links"]["source"]["href"])
        return {"transfer": transfer_obj}

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

    def get_balance(self, customer_url):
        funding_sources = self.app_token.get("%s/funding-sources" % customer_url)
        balance_location = ""
        for source in funding_sources.body["_embedded"]["funding-sources"]:
            if source["type"] == "balance":
                balance_location = source["_links"]["self"]["href"]
        balance = self.app_token.get("%s/balance" % balance_location)
        return {"balance": balance.body["balance"], "location": balance_location}

    def create_personal_customer(self, request_body):
        customer = self.app_token.post("customers", request_body)
        return customer.headers["location"]

    def create_business_customer(self, request_body):
        customer = self.app_token.post("customers", request_body)
        return customer.headers["location"]

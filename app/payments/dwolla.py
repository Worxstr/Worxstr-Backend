from datetime import date
import dwollav2
from flask.globals import request


class Dwolla:
    app_token = None

    def __init__(self, app_key, app_secret):
        client = dwollav2.Client(key=app_key, secret=app_secret, environment="sandbox")

        self.app_token = client.Auth.client()

    def get_customer_info(self, customer_url):
        customer = self.app_token.get(customer_url)
        return customer.body

    def create_personal_customer(
        self,
        firstName,
        lastName,
        email,
        address1,
        city,
        state,
        postalCode,
        dateOfBirth,
        ssn,
    ):
        request_body = {
            "firstName": firstName,
            "lastName": lastName,
            "email": email,
            "type": "personal",
            "address1": address1,
            "city": city,
            "state": state,
            "postalCode": postalCode,
            "dateOfBirth": dateOfBirth,
            "ssn": ssn,
        }
        customer = self.app_token.post("customers", request_body)
        return customer.headers["location"]

    def authenticate_funding_source(self, customer_url, plaid_token, source_name):
        request_body = {"plaidToken": plaid_token, "name": source_name}
        customer = self.app_token.post(
            "%s/funding-sources" % customer_url, request_body
        )
        return {"location": customer.headers["location"], "name": source_name}

    def get_funding_sources(self, customer_url):
        funding_sources = self.app_token.get("%s/funding-sources" % customer_url)
        result = []
        for sources in funding_sources.body["_embedded"]["funding-sources"]:
            if sources["type"] == "bank":
                result.append(
                    {
                        "location": sources["_links"]["self"]["href"],
                        "name": sources["name"],
                    }
                )
        return {"funding_sources": result}

    def edit_funding_source(self, location, account_name):
        request_body = {"name": account_name}
        funding_source = self.app_token.post(location, request_body)
        return {"location": location, "name": funding_source.body["name"]}

    def remove_funding_source(self, location):
        request_body = {"removed": True}
        funding_source = self.app_token.post(location, request_body)
        return

    def create_business_customer(
        self,
        firstName,
        lastName,
        email,
        ipAddress,
        address1,
        city,
        state,
        postalCode,
        controller,
        businessClassification,
        businessType,
        businessName,
        ein,
    ):
        request_body = None
        if businessType == "soleProprietorship":
            request_body = {
                "firstName": firstName,
                "lastName": lastName,
                "email": email,
                "ipAddress": ipAddress,
                "type": "business",
                "dateOfBirth": controller["dateOfBirth"],
                "ssn": controller["ssn"],
                "address1": address1,
                "city": city,
                "state": state,
                "postalCode": postalCode,
                "businessClassification": businessClassification,
                "businessType": businessType,
                "businessName": businessName,
                "ein": ein,
            }
        else:
            request_body = {
                "firstName": firstName,
                "lastName": lastName,
                "email": email,
                "type": "business",
                "address1": address1,
                "city": city,
                "state": state,
                "postalCode": postalCode,
                "controller": {
                    "firstName": controller["firstName"],
                    "lastName": controller["lastName"],
                    "title": controller["title"],
                    "dateOfBirth": controller["dateOfBirth"],
                    "ssn": controller["ssn"],
                    "address": {
                        "address1": controller["address1"],
                        "address2": controller["address2"],
                        "city": controller["city"],
                        "stateProvinceRegion": controller["stateProvinceRegion"],
                        "postalCode": controller["postalCode"],
                        "country": controller["country"],
                    },
                },
                "businessClassification": businessClassification,
                "businessType": businessType,
                "businessName": businessName,
                "ein": ein,
            }
        customer = self.app_token.post("customers", request_body)
        return customer.headers["location"]

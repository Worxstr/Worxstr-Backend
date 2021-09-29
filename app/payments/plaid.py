import plaid
from plaid.api import plaid_api
from plaid.model.item_public_token_exchange_request import (
    ItemPublicTokenExchangeRequest,
)
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.country_code import CountryCode
from plaid.model.processor_token_create_request import ProcessorTokenCreateRequest
from plaid.model.products import Products


class Plaid:
    api_client = None
    client = None
    country_codes = [CountryCode("US")]
    client_name = "Worxstr"

    def __init__(self, client_id, secret, host):
        config = plaid.Configuration(
            host=host,
            api_key={
                "clientId": client_id,
                "secret": secret,
            },
        )
        self.api_client = plaid.ApiClient(config)
        self.client = plaid_api.PlaidApi(self.api_client)

    def generate_client_token(self):
        self.client = plaid_api.PlaidApi(self.api_client)

    def obtain_link_token(self, user_id):
        request = LinkTokenCreateRequest(
            products=[Products("auth"), Products("transactions")],
            client_name=self.client_name,
            country_codes=self.country_codes,
            language="en",
            user=LinkTokenCreateRequestUser(client_user_id=str(user_id)),
        )

        response = self.client.link_token_create(request)
        return response["link_token"]

    def get_dwolla_token(self, public_token, account_id):
        access_token = self.obtain_access_token(public_token)
        return self.obtain_processor_token(access_token, account_id, "dwolla")

    def obtain_access_token(self, public_token):
        request = ItemPublicTokenExchangeRequest(public_token=public_token)
        response = self.client.item_public_token_exchange(request)
        return response["access_token"]

    def obtain_processor_token(self, access_token, account_id, processor):
        request = ProcessorTokenCreateRequest(
            access_token=access_token, account_id=account_id, processor=processor
        )
        response = self.client.processor_token_create(request)
        return response["processor_token"]

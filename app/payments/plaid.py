import plaid
from plaid.api import plaid_api
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.country_code import CountryCode
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

    def obtain_processor_token(self, user_id):

        request = LinkTokenCreateRequest(
            products=[Products("auth"), Products("transactions")],
            client_name=self.client_name,
            country_codes=self.country_codes,
            language="en",
            user=LinkTokenCreateRequestUser(client_user_id=str(user_id)),
        )

        response = self.client.link_token_create(request)
        return response["link_token"]

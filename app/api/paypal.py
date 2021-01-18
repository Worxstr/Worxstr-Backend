# 1. Import the PayPal SDK client that was created in `Set up Server-Side SDK`.
from paypalcheckoutsdk.orders import OrdersGetRequest

from paypalcheckoutsdk.core import PayPalHttpClient, SandboxEnvironment

import sys



class PayPalClient:
	def __init__(self):
		self.client_id = "AdZlQYu3D1K6pWydQvrevs_Ln5xX-006zna6_MTnlkw7chrHg8MKd3rtZqRB5QKY1TwVXFNGflr7Aw6B"
		self.client_secret = "EE0xz5ElDk1hdyYFBs67WtaH25Q2QpxSGjL0MFf2pZsz7SdLrH5Gt_vP0O8wmiF-DMDDG2oLvZFfJP0p"

		"""Set up and return PayPal Python SDK environment with PayPal access credentials.
		   This sample uses SandboxEnvironment. In production, use LiveEnvironment."""

		self.environment = SandboxEnvironment(client_id=self.client_id, client_secret=self.client_secret)

		""" Returns PayPal HTTP client instance with environment that has access
			credentials context. Use this instance to invoke PayPal APIs, provided the
			credentials have access. """
		self.client = PayPalHttpClient(self.environment)

	def object_to_json(self, json_data):
		"""
		Function to print all json data in an organized readable manner
		"""
		result = {}
		if sys.version_info[0] < 3:
			itr = json_data.__dict__.iteritems()
		else:
			itr = json_data.__dict__.items()
		for key,value in itr:
			# Skip internal attributes.
			if key.startswith("__"):
				continue
			result[key] = self.array_to_json_array(value) if isinstance(value, list) else\
						self.object_to_json(value) if not self.is_primittive(value) else\
						 value
		return result
	def array_to_json_array(self, json_array):
		result =[]
		if isinstance(json_array, list):
			for item in json_array:
				result.append(self.object_to_json(item) if  not self.is_primittive(item) \
							  else self.array_to_json_array(item) if isinstance(item, list) else item)
		return result

	def is_primittive(self, data):
		return isinstance(data, bytes) or isinstance(data, str) or isinstance(data, int)

class GetOrder(PayPalClient):

	ORDER_APPROVED = "APPROVED"

	#2. Set up your server to receive a call from the client
	"""You can use this function to retrieve an order by passing order ID as an argument"""   
	def get_order(self, order_id):
		"""Method to get order"""
		request = OrdersGetRequest(order_id)
		#3. Call PayPal to get the transaction
		response = self.client.execute(request)
		#4. Save the transaction in your database. Implement logic to save transaction to your database for future reference.
		result = {
			"status_code": response.status_code,
			"status": response.result.status,
			"order_id": response.result.id,
			"gross_amount": response.result.purchase_units[0].amount.value
		}
		return result

class SendPayouts(PayPalClient):
	def send_payouts(self, payments):
		request = PayoutsGetRequest(payments)

		response = self.client.execute(request)

		return response.result.batch_header.payout_batch_id

class PayoutsGetRequest:
	"""
	Shows details for an order, by ID.
	"""
	def __init__(self, payments):
		self.verb = "POST"
		self.path = "/v1/payments/payouts"
		self.headers = {}
		self.headers["Content-Type"] = "application/json"
		self.body = {}
		self.body["sender_batch_header"] = {}
		self.body["sender_batch_header"]["email_subject"] = "Worxstr Shift Payment"
		self.body["sender_batch_header"]["email_message"] = "You have received payment for your shift. Thank you for using Worxstr!"
		self.body["items"] = []
		for i in payments:
			payment = {}
			payment["recipient_type"] = "EMAIL"
			payment["amount"] = {}
			print(i["payment"])
			payment["amount"]["value"] = i["payment"]
			payment["amount"]["currency"] = "USD"
			payment["note"] = i["note"]
			payment["receiver"] = i["email"]
			self.body["items"].append(payment)
import requests
from requests.auth import HTTPBasicAuth
from django.conf import settings
from datetime import datetime
import base64
from decouple import config

class DarajaClient:
    def __init__(self):
        self.consumer_key = config('DARAJA_CONSUMER_KEY')
        self.consumer_secret = config('DARAJA_CONSUMER_SECRET')
        self.business_short_code = config('DARAJA_SHORTCODE')
        self.passkey = config('DARAJA_PASSKEY')
        self.base_url = "https://sandbox.safaricom.co.ke"

    def get_token(self):
        url = f"{self.base_url}/oauth/v1/generate?grant_type=client_credentials"
        response = requests.get(url, auth=HTTPBasicAuth(self.consumer_key, self.consumer_secret))
        return response.json().get('access_token')

    def trigger_stk_push(self, phone_number, amount, callback_url):
        access_token = self.get_token()
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        
        # Password is Base64(ShortCode + Passkey + Timestamp)
        data_to_encode = self.business_short_code + self.passkey + timestamp
        password = base64.b64encode(data_to_encode.encode()).decode('utf-8')

        headers = {"Authorization": f"Bearer {access_token}"}
        
        payload = {
            "BusinessShortCode": self.business_short_code,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": amount,
            "PartyA": phone_number, # The phone sending money
            "PartyB": self.business_short_code,
            "PhoneNumber": phone_number,
            "CallBackURL": callback_url, # Where Safaricom sends results
            "AccountReference": "JODASA_FEES",
            "TransactionDesc": "School Fee Payment"
        }

        
        # Corrected URL for the process request:
        process_url = f"{self.base_url}/mpesa/stkpush/v1/processrequest"
        
        response = requests.post(process_url, json=payload, headers=headers)
        return response.json()
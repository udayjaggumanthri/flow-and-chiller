import json
import requests
from config import ANTAR_IIoT_URL


class access_Token:
    @staticmethod
    def access_Token_Generator():
        print("accessTokenGenerator:")
        print(ANTAR_IIoT_URL)
        url = f"{ANTAR_IIoT_URL}/api/auth/login"
        # deviceID = deviceIDsWithKeys.get(token)
        # Define the request headers
        headers1 = {
            "accept": "application/json",
            "Content-Type": "application/json",
        }
        # data1 = {"username": "kalyan@antariot.com", "password": "antariot"}
        # data = {"username": "tenant@antariiot.com", "password": "tenant"}
        data = {"username": "tenant@thingsboard.org", "password": "tenant"}

        # Send a POST request to the endpoint with the headers and data
        response = requests.post(url, headers=headers1, data=json.dumps(data))

        if response.status_code == 200:
            # THINGSBOARD_URL = "http://locahost:8080"
            ACCESS_TOKEN = response.json().get("token")
            print("LogIn was Successfull.")
            return ACCESS_TOKEN
        else:
            print("Token generation failed.")

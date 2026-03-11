import requests
from config import ANTAR_IIoT_URL


class device_Name_Class:
    @staticmethod
    def device_Name_From_Thingsboard(item, token):

        # print(token)
        url = f"{ANTAR_IIoT_URL}/api/device/{item}"
        headers = {
            "Content-Type": "application/json",
            "X-Authorization": f"Bearer {token}",
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            return data["name"]
            # print(data["name"])
        else:
            print(
                "Request failed to get the Device Name with status code:",
                response.status_code,
            )

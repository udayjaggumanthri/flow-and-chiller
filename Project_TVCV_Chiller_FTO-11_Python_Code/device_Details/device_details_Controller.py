class DeviceManager:
    @staticmethod
    def get_device_id_by_token(token):
        devices = {
            "tvcv1": "6bc0f150-e600-11ef-8136-31766ac937d3",
            "tvcv2": "7d75b7f0-e600-11ef-8136-31766ac937d3",
            # "tvcv3": "fd882c60-4a7e-11f0-82c1-49c59e8f9ba9",
            # "tvcv4": "1f83c7a1-15e6-11f0-86da-6fbdb9db8a06",
            # "tvcv5": "1a213010-4a7f-11f0-82c1-49c59e8f9ba9",
        }
        return devices.get(token)

    @staticmethod
    def get_device_ids():
        return {
            "6bc0f150-e600-11ef-8136-31766ac937d3",
            "7d75b7f0-e600-11ef-8136-31766ac937d3",
        }


from ..data_Check_Controllers.data_push_controller import data_push_class
class mqtt_Data_Controller:
    @staticmethod
    def topic_check(topic,converted_payload,original_payload,client,ACCESS_TOKEN_1):
        print("topic check:------------------------\n", topic)
        if topic[-5:-1] == "tvcv":
            token = topic[-5:]
            mqtt_Data_Controller.send_dump(token,converted_payload,original_payload,client,ACCESS_TOKEN_1)
        elif topic[-7:-1] == "buzzer":
        # print(t)
            tokenb = topic[-7:]
            
    @staticmethod
    def send_dump(token,converted_payload,original_payload,client,ACCESS_TOKEN_1):
        print("Send_Dump:-----------")
        # print("CV" in d and "TV" in d)
        try:
            if "deviceID" in converted_payload:
                print("check")
                data_push_class.check_for_CV_TV(token,converted_payload,original_payload,client,ACCESS_TOKEN_1)
            else:
                print("Payload formate was NOT right.")
        except Exception as main_exception:
            print("An error occurred in the main block:", str(main_exception))
    
    
            
            
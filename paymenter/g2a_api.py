# <--- Import --->
import requests
import json

# <--- Import from --->
from urllib.parse import urlencode

# <--- Self-made reversed g2a api handler --->
class G2A:
    # <--- Essential URL's --->
    G2A_Generate_Cart_Url = "https://www.g2a.com/cart/api/carts?"
    G2A_Preorder_Url = "https://www.g2a.com/cart/api/preorder?"
    G2A_Payment_Intetion_Url = "https://www.g2a.com/payment/api/v1/intention?"
    G2A_Checkout_Url = "https://www.g2a.com/payment/api/v1/intention/{payment_intention}/checkout?"
    # <--- End of essential URL's --->
    headers = {
        "Content-type": "application/json;charset=utf-8",
        "User-Agent": "PostmanRuntime/7.29.2",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept": "*/*"
    }
    def __init__(self) -> None:
        pass

    def generate_cart(self, auction_id: str): # Function allows to generate cart with given auction id
        payload = {
            "currencyCode": "USD",
            "storeCode": "englishus",
            "items": [
                {
                "auctionId": auction_id,
                "context": "selected-offer",
                "source": "new-layout",
                "type": "simple",
                "quantity": 1
                }
            ]
        }
        resp = requests.post(self.G2A_Generate_Cart_Url, headers=self.headers, data=json.dumps(payload))
        return resp

    def preorder(self, cartId: str, deliveryEmail: str): # Function allows to create order on g2a with given cartid & deliveryemail}
        payload = {
            "cartId": cartId,
            "currencyCode": "USD",
            "context": {},
            "email": deliveryEmail
        }
        resp = requests.post(self.G2A_Preorder_Url, headers=self.headers, data=json.dumps(payload))
        return resp

    def payment_intention(self, cartId: str, returnUrl: str, returnUrlFailure: str):
        payload = {
            "cartId": cartId,
            "returnUrl": returnUrl,
            "failureUrl": returnUrlFailure,
            "countryCode": "US"
        }
        resp = requests.post(self.G2A_Payment_Intetion_Url, headers=self.headers, data=json.dumps(payload))
        return resp
    
    def checkout(self, cartId: str, paymentIntentionId: str, returnUrl: str, returnUrlFailure: str, payment_form_code: str = "paypal"):
        queryString = {
            "order_id": paymentIntentionId
        }
        payload = {
            "cartId": cartId,
            "method": payment_form_code,
            "returnUrl": f"{returnUrl}?{urlencode(queryString)}",
            "failureUrl": f"{returnUrlFailure}?{urlencode(queryString)}",
            "type": "payin",
            "context": {},
            "paymentSessionId": None,
            "paymentLocale": "US"
        }
        url = self.G2A_Checkout_Url.replace("{payment_intention}", paymentIntentionId)
        resp = requests.post(url, headers=self.headers, data=json.dumps(payload))
        return resp


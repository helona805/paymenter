# <--- Import --->
import requests
import json

# <--- Import from --->

# <--- Flask --->
from flask import Flask, jsonify, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
# <--- End flask --->

# <--- Utils --->
from paymenter.config import ConfigManager
from paymenter.g2a_api import G2A
# <--- End utils --->

app = Flask(__name__)
limiter = Limiter(app, key_func=get_remote_address)
config = ConfigManager().load()
g2a = G2A()

@app.route("/", methods = ["GET"])
@limiter.limit("5/minute")
def index():
    status = {
        "message": "Welcome to paymenter, simple private api to generate checkouts"
    }
    return jsonify(status), 200

@app.route("/generate_checkout", methods = ["POST"])
@limiter.limit("5/minute")
def generate():
    checkout_info = {
        "url": "",
        "payment_method": "",
        "price": "",
        "price_with_currency": "",
        "service_fee": "",
        "price_without_fee": "",
    }
    
    content = request.get_json()
    user_info = {}
    product_id = 0
    order_info = {
        "cart_id": "",
        "payment_intention_id": "",
        "payment_method": ""
    }

    # <--- API KEY CHECK --->
    if "api_key" in content:
        if content["api_key"] != "":
            if content["api_key"] in config.get("api_keys"):
                user_info = config.get("api_keys")[content["api_key"]]
            else:
                message = {
                    "message": "api key not found in database"
                }
                return jsonify(message), 400
        else:
            message = {
                "message": "api_key is empty!"
            }
            return jsonify(message), 400
    else:
        message = {
            "message": "No api_key in request found!"
        }
        return jsonify("message"), 
    # <--- END OF API KEY CHECK --->

    # <--- PRODUCT ID CHECK --->
    if "product_id" in content:
        if content["product_id"] != "":
            if type(content["product_id"]) != int:
                message = {
                    "message": "product_id needs to be integer"
                }
                return jsonify(message), 400
            
            if content["product_id"] == 0 or content["product_id"] > len(user_info.get("product_auctions")):
                message = {
                    "message": "product_id is out of range!"
                }
                return jsonify(message), 400

            if str(content["product_id"]) in user_info.get("product_auctions"):
                product_id = str(content["product_id"])
            else:
                message = {
                    "message": "product_id not found in database"
                }
                return jsonify(message), 400
        else:
            message = {
                "message": "product_id is empty!"
            }
            return jsonify(message), 400

    else:
        message = {
            "No product_id in request found!"
        }
        return jsonify(message), 400
    
    # <--- END OF PRODUCT ID CHECK --->
    
    # <--- PAYMENT METHOD CHECK --->
    if "payment_method" in content:
        if content["payment_method"] != "":
            order_info["payment_method"] = content["payment_method"]
        else:
            message = {
                "message": "payment_method is empty!"
            }
            return jsonify(message), 400
    else:
        message = {
            "message": "no payment method in request"
        }
        return jsonify(message), 400
    # <--- END OF PAYMENT METHOD CHECK --->

    # <--- Get product info --->
    product_info = user_info.get("product_auctions").get(product_id)

    # <--- Generate cart G2A --->
    resp_raw = g2a.generate_cart(product_info.get("auction_id"))
    if resp_raw.status_code == 200:
        resp = resp_raw.json()
        order_info["cart_id"] = resp.get("data").get("id")
        checkout_info["price"] = resp.get("data").get("items")[0].get("finalPrice")
        checkout_info["price_with_currency"] = f"{checkout_info['price']} {resp.get('data').get('currencyCode')}"
    else:
        return resp_raw.json(), resp_raw.status_code

    # <--- Preorder at g2a --->
    resp = g2a.preorder(
        cartId=order_info.get("cart_id"), 
        deliveryEmail=user_info.get("deliveryEmail")
    )

    if resp.status_code != 200:
        return resp.json(), resp.status_code
    
    # <--- Payment intention at g2a --->
    resp = g2a.payment_intention(
        cartId=order_info.get("cart_id"),
        returnUrl=user_info.get("returnUrlSucess"),
        returnUrlFailure=user_info.get("returnUrlFailure")    
    )

    if resp.status_code == 201:
        order_info["payment_intention_id"] = resp.json().get("data").get("paymentIntentionId")
        payment_methods = resp.json().get("data").get("paymentIntentionAvailableMethods")
        if not order_info.get("payment_method") in payment_methods:
            message = {"message": f"'{order_info.get('payment_method')}' not available as payment form"}
            return jsonify(message), 400

    # <--- Generate checkout on g2a --->
    resp = g2a.checkout(
        cartId=order_info.get("cart_id"),
        paymentIntentionId=order_info.get("payment_intention_id"),
        returnUrl=user_info.get("returnUrlSucess"),
        returnUrlFailure=user_info.get("returnUrlFailure"),
        payment_form_code=order_info.get("payment_method")
    )
    
    if not resp.status_code == 201:
        return resp.json(), resp.status_code
    
    checkout_info["url"] = resp.json().get("data").get("data").get("url")
    checkout_info["payment_method"] = order_info.get("payment_method")
    checkout_info["price_without_fee"] = str(product_info.get("price"))
    checkout_info["service_fee"] = str(
        round(
            float(checkout_info.get("price")) - 
            float(checkout_info.get("price_without_fee"))
        , ndigits=2)
    )

    return jsonify(checkout_info), 200

if __name__ == "__main__":
    app.run()
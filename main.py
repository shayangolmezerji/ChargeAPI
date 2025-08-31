# main.py
import os
import requests
import re
import json
import random
from typing import Literal
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from dotenv import load_dotenv

# --- Configuration ---
load_dotenv()
WEB_ID = os.getenv("CHARGE_RESELLER_WEB_ID")
REDIRECT_URL = "https://domain.com/charge.php"
API_URLS = {
    "direct": "https://chr724.ir/services/v3/EasyCharge/TopUp",
    "pincode": "https://chr724.ir/services/v3/EasyCharge/BuyProduct"
}

# --- Pydantic Models for Data Validation ---
class ChargeRequest(BaseModel):
    """
    Request body model for charge requests.
    FastAPI automatically validates the incoming JSON against this model.
    """
    amount: int
    phone: str
    super: bool = False
    daemi: bool = False
    charge_type: Literal["direct", "pincode"]

# --- API Instance ---
app = FastAPI(
    title="Shayan Golmezerji's Charge API",
    description="A robust and secure API for handling mobile charge and top-up requests.",
    version="1.0.0",
)

# --- Helper Functions ---
def is_valid_phone(phone: str) -> bool:
    """Checks if the phone number is valid (11 digits, starts with '09')."""
    return bool(re.fullmatch(r"09\d{9}", phone))

def get_operator(phone: str, super_charge: bool, daemi: bool) -> str | None:
    """Determines the operator based on the phone number prefix."""
    if re.fullmatch(r"09[03]\d{8}", phone):
        if super_charge:
            return "!MTN"
        elif daemi:
            return "#MTN"
        else:
            return "MTN"
    elif re.fullmatch(r"09[19]\d{8}", phone):
        return "MCI"
    elif re.fullmatch(r"094\d{8}", phone):
        return "WiMax"
    elif re.fullmatch(r"092[0-2]\d{7}", phone):
        if super_charge:
            return "!RTL"
        else:
            return "RTL"
    return None

def build_params(data: dict) -> dict:
    """Builds and cleans the API request parameters."""
    params = {
        "data[webserviceId]": WEB_ID,
        "data[redirectUrl]": REDIRECT_URL,
        "data[count]": 1,
        "data[email]": "",
        "data[packageId]": "",
        "data[billId]": "",
        "data[paymentId]": "",
        "data[issuer]": "",
        "data[paymentDetails]": "true",
        "data[redirectToPage]": "true",
        "data[scriptVersion]": "Script-fluent-1.7",
        "data[firstOutputType]": "json",
        "data[isTarabord]": "false",
        "data[secondOutputType]": "get",
        "data[ChargeKind]": "",
        "_": random.randint(1111111111111, 9999999999999),
    }
    
    params.update({
        "data[amount]": data.get("amount"),
        "data[cellphone]": data.get("phone"),
        "data[type]": data.get("operator"),
    })

    if data.get("type") == "pincode":
        params["data[productId]"] = f"CC-{data.get('operator')}-{data.get('amount')}"
    
    return params

# --- API Endpoint ---
@app.post("/charge", status_code=status.HTTP_200_OK)
async def process_charge(request: ChargeRequest):
    """
    Handles a charge request by validating input and forwarding it to the
    charge reseller API.
    
    Returns the JSON response from the external API.
    """
    # --- Input Validation ---
    if not WEB_ID:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Web service ID not configured. Please set CHARGE_RESELLER_WEB_ID environment variable."
        )

    if not (2000 <= request.amount <= 20000):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="مبلغ باید بیشتر از 2000 تومان و کمتر از 20000 تومان باشد"
        )
    
    if not is_valid_phone(request.phone):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="شماره تلفن باید 11 رقم باشد و با 09 شروع شود"
        )

    # --- Logic to get operator and build request ---
    operator = get_operator(request.phone, request.super, request.daemi)
    if not operator:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="اپراتور برای این شماره تلفن یافت نشد"
        )
    
    api_url = API_URLS.get(request.charge_type)
    if not api_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="نوع شارژ نامعتبر است"
        )
        
    request_data = {
        "amount": request.amount,
        "phone": request.phone,
        "operator": operator,
        "type": request.charge_type
    }
    
    callback_name = f"Shayan Golmezerji{random.randint(1111111111, 9999999999)}_{random.randint(1111111111, 9999999999)}"
    params = build_params(request_data)
    params["callback"] = callback_name

    try:
        response = requests.get(api_url, params=params)
        response.raise_for_status()
        response_text = response.text.replace(callback_name, "", 1)
        match = re.search(r"^\((.*)\)$", response_text, re.DOTALL)
        if match:
            json_string = match.group(1)
            result = json.loads(json_string)
            return result
        else:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="پاسخ API نامعتبر است"
            )
            
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"خطا در ارتباط با API: {e}"
        )
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="خطا در پردازش پاسخ JSON"
        )

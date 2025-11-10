# main.py
import os
import re
import json
import random
from typing import Literal, Optional, Dict, Any

import requests
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# --- کانفیگ ---

load_dotenv()

# کلید API و لینک ریدایرکت
WEB_SERVICE_ID: Optional[str] = os.getenv("CHARGE_RESELLER_WEB_ID")
REDIRECT_URL: str = "https://domain.com/charge.php"

# آدرس ها بر اساس نوع شارژ
API_ENDPOINTS: Dict[str, str] = {
    "direct": "https://chr724.ir/services/v3/EasyCharge/TopUp",
    "pincode": "https://chr724.ir/services/v3/EasyCharge/BuyProduct"
}

OperatorType = Literal["MTN", "#MTN", "!MTN", "MCI", "WiMax", "RTL", "!RTL"]

# --- مدل ها ---

class ChargeRequest(BaseModel):
    """
    مدل ورودی درخواست شارژ.
    """
    amount: int = Field(..., ge=2000, le=20000, description="مبلغ (۲۰۰۰ تا ۲۰۰۰۰ تومان)")
    phone: str = Field(..., description="شماره موبایل ۱۱ رقمی (شروع با ۰۹)")
    super: bool = False
    daemi: bool = False
    charge_type: Literal["direct", "pincode"]

# --- توابع ---

def _get_operator(phone: str, super: bool, daemi: bool) -> Optional[OperatorType]:
    """تعیین اپراتور و نوع شارژ بر اساس پیش‌شماره."""

    if re.fullmatch(r"09[03]\d{8}", phone):
        if super:
            return "!MTN"
        elif daemi:
            return "#MTN"
        return "MTN"
        
    elif re.fullmatch(r"09[19]\d{8}", phone):
        return "MCI"
        
    elif re.fullmatch(r"094\d{8}", phone):
        return "WiMax"
        
    elif re.fullmatch(r"092[0-2]\d{7}", phone):
        return "!RTL" if super else "RTL"
        
    return None

def _prep_api_payload(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """آماده‌سازی پارامترهای نهایی برای ارسال به API واسط."""
    
    base_params = {
        "data[webserviceId]": WEB_SERVICE_ID,
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
        "data[nonce]": random.randint(1111111111111, 9999999999999),
    }

    charge_params = {
        "data[amount]": request_data["amount"],
        "data[cellphone]": request_data["phone"],
        "data[type]": request_data["operator"],
    }

    payload = {**base_params, **charge_params}

    if request_data["type"] == "pincode":
        payload["data[productId]"] = f"CC-{request_data['operator']}-{request_data['amount']}"
    
    return payload

# --- نمونه ---

app = FastAPI(
    title="Type Shit",
    description="سرویس پردازش درخواست‌های شارژ موبایل.",
    version="1.0.0",
)

# --- پایان نمونه ---

@app.post("/charge", status_code=status.HTTP_200_OK)
async def create_charge(request: ChargeRequest):
    """
    درخواست شارژ را دریافت، اعتبارسنجی و به API واسط ارسال می‌کند.
    """
    
    if not WEB_SERVICE_ID:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="خطای سرور: کلید وب‌سرویس (WEB_SERVICE_ID) تنظیم نشده است."
        )

    operator = _get_operator(
        request.phone, 
        request.super,
        request.daemi
    )
    
    if not operator:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="اپراتور برای این شماره تلفن یافت نشد."
        )
    
    api_url = API_ENDPOINTS.get(request.charge_type)
    if not api_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="نوع شارژ نامعتبر است."
        )
        
    request_data_for_payload = {
        "amount": request.amount,
        "phone": request.phone,
        "operator": operator,
        "type": request.charge_type
    }
    
    # ساخت Callback
    random_suffix = "".join(str(random.randint(0, 9)) for _ in range(15))
    callback_name = f"callback_{random_suffix}"
    
    params = _prep_api_payload(request_data_for_payload)
    params["callback"] = callback_name
    
    try:
        response = requests.get(api_url, params=params, timeout=10)
        response.raise_for_status() 
        
        # حذف Callback + پرانتزها برای تبدیل JSONP به JSON
        response_text_clean = response.text.replace(f"{callback_name}", "").strip().lstrip('(').rstrip(')')
            
        result = json.loads(response_text_clean)
        return result

    except requests.exceptions.Timeout:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="درخواست API منقضی شد."
        )
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"خطا در ارتباط با API: {e}"
        )
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="خطا در پردازش پاسخ JSON."
        )

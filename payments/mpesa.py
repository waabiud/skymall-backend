import requests
import hashlib
import hmac
import os


def get_signature(payload: dict) -> str:
    """Generate HMAC SHA256 signature for request verification"""
    secret = os.getenv('CODIAN_SIGNATURE_SECRET', '')
    # sort keys and join as key=value pairs
    message = '&'.join(f'{k}={v}' for k, v in sorted(payload.items()))
    signature = hmac.new(
        secret.encode(), message.encode(), hashlib.sha256
    ).hexdigest()
    return signature


def normalize_phone(phone: str) -> str:
    """Convert any Kenyan phone format to 2547XXXXXXXX"""
    phone = phone.strip().replace(' ', '')
    if phone.startswith('+'):
        phone = phone[1:]
    if phone.startswith('0'):
        phone = '254' + phone[1:]
    return phone


def stk_push(phone_number: str, amount: int, order_number: str) -> dict:
    """Initiate Codian STK push"""
    client_id     = os.getenv('CODIAN_CLIENT_ID')
    client_secret = os.getenv('CODIAN_CLIENT_SECRET')
    callback_url  = os.getenv('CODIAN_CALLBACK_URL')
    account_number= os.getenv('CODIAN_ACCOUNT_NUMBER', order_number)

    phone = normalize_phone(phone_number)

    payload = {
        'client_id':      client_id,
        'client_secret':  client_secret,
        'amount':         int(amount),
        'phone':          phone,
        'account_number': account_number or order_number,
        'callback_url':   callback_url,
        'reference':      order_number,
    }

    response = requests.post(
        'https://api.codian.co.ke/v1/payments/c2b/initiate/',
        json=payload,
        timeout=30,
    )
    return response.json()


def query_payment_status(checkout_request_id: str) -> dict:
    """Query status of a Codian payment"""
    client_id     = os.getenv('CODIAN_CLIENT_ID')
    client_secret = os.getenv('CODIAN_CLIENT_SECRET')

    response = requests.post(
        'https://api.codian.co.ke/v1/payments/c2b/status/',
        json={
            'client_id':           client_id,
            'client_secret':       client_secret,
            'checkout_request_id': checkout_request_id,
        },
        timeout=30,
    )
    return response.json()

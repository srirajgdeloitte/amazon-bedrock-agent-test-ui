import json
import uuid
import re
import logging
from datetime import datetime

# Configure logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)  # You can change to DEBUG for more detail

def is_valid_credit_card(number):
    return number.isdigit() and len(number) == 16

def is_valid_cvv(cvv):
    return cvv.isdigit() and len(cvv) in [3, 4]

def is_valid_expiry(expiry):
    match = re.fullmatch(r"(0[1-9]|1[0-2])\/(\d{2})", expiry)
    if not match:
        return False

    month, year_suffix = match.groups()
    exp_month = int(month)
    exp_year = int("20" + year_suffix)  # Convert YY to YYYY

    now = datetime.now()
    expiry_date = datetime(exp_year, exp_month, 1)
    return expiry_date >= datetime(now.year, now.month, 1)

def lambda_handler(event, context):
    logger.info("Received event: %s", json.dumps(event))

    try:
        body = json.loads(event.get("body", "{}"))

        booking_id = body.get("booking_id")
        credit_card_number = body.get("credit_card_number")
        expiry_date = body.get("expiry_date")
        cvv = body.get("cvv")

        logger.info("Parsed input: booking_id=%s, expiry_date=%s", booking_id, expiry_date)

        if not all([booking_id, credit_card_number, expiry_date, cvv]):
            logger.warning("Missing fields in request body")
            return {
                "statusCode": 400,
                "body": json.dumps({"message": "Missing required fields"})
            }

        if not is_valid_credit_card(credit_card_number):
            logger.warning("Invalid credit card number")
            return {
                "statusCode": 400,
                "body": json.dumps({"message": "Invalid credit card number (must be 16 digits)"})
            }

        if not is_valid_cvv(cvv):
            logger.warning("Invalid CVV")
            return {
                "statusCode": 400,
                "body": json.dumps({"message": "Invalid CVV (must be 3 or 4 digits)"})
            }

        if not is_valid_expiry(expiry_date):
            logger.warning("Invalid or expired expiry date")
            return {
                "statusCode": 400,
                "body": json.dumps({"message": "Invalid or expired expiry date (use MM/YY format)"})
            }

        confirmation_id = f"PAY-{uuid.uuid4().hex[:8].upper()}"
        logger.info("Payment confirmed with confirmation_id=%s", confirmation_id)

        return {
            "statusCode": 200,
            "body": json.dumps({
                "confirmation_id": confirmation_id,
                "message": "Payment successful"
            })
        }

    except Exception as e:
        logger.exception("Unhandled exception occurred")
        return {
            "statusCode": 500,
            "body": json.dumps({"message": f"Internal error: {str(e)}"})
        }

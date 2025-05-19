import json

import uuid

from datetime import datetime

import logging

from typing import Dict, Any

from http import HTTPStatus

from fuzzywuzzy import fuzz
 
logger = logging.getLogger()

logger.setLevel(logging.INFO)
 
# Load resort data from file

try:

    with open('resort_details.json') as f:

        MAHINDRA_RESORTS = json.load(f)

except Exception as e:

    logger.error(f"Failed to load resort data: {e}")

    MAHINDRA_RESORTS = []
 
def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:

    logger.info(f"Received event: {json.dumps(event)}")
 
    try:

        action_group = event['actionGroup']

        apiPath = event['apiPath']

        httpMethod = event['httpMethod']

        parameters = event['requestBody']['content']['application/json'].get('properties', [])
 
        # Extract parameter values

        resort_name = None

        check_in_date = None

        check_out_date = None

        number_of_units = 1  # Default if not provided
 
        for param in parameters:

            param_name = param.get('name', '').lower()

            param_value = param.get('value')
 
            if param_name == 'resort_name':

                resort_name = param_value

            elif param_name == 'check_in_date':

                check_in_date = param_value

            elif param_name == 'check_out_date':

                check_out_date = param_value

            elif param_name == 'number_of_units':

                number_of_units = int(param_value)
 
        if not resort_name:

            return error_response("Missing required parameter: resort_name")
 
        booked_resort = None

        for resort in MAHINDRA_RESORTS:

            if resort:

                try:

                    logger.info(f"Checking resort: {json.dumps(resort)}")

                    similarity_score = fuzz.ratio(resort_name.lower(), resort.get('hotel_name', '').lower())

                    logger.info(f"Similarity score: {similarity_score}")
 
                    if similarity_score >= 75:

                        available_units = int(resort.get('available_units', 0))
 
                        if available_units >= number_of_units:

                            resort['available_units'] -= number_of_units

                            booked_resort = resort

                            break

                        else:

                            return success_response({

                                'message': f"Sorry, not enough available units for {resort_name}. Requested: {number_of_units}, Available: {available_units}"

                            })

                except Exception as resort_err:

                    logger.error(f"Error processing resort: {resort_err}")
 
        if not booked_resort:

            return success_response({

                'message': f"No suitable resort found matching: {resort_name}"

            })
 
        # Construct success response

        response = {

            "message": "Booking successful",

            "resort": {

                "hotel_name": booked_resort.get("hotel_name"),

                "location": booked_resort.get("hotel_location"),

                "rating": booked_resort.get("hotel_rating"),

                "price_per_night": booked_resort.get("hotel_price_per_night"),

                "currency": booked_resort.get("price_currency"),

                "remaining_units": booked_resort.get("available_units"),

                "amenities": booked_resort.get("hotel_amenities"),

            },

            "check_in_date": check_in_date,

            "check_out_date": check_out_date,

            "units_booked": number_of_units,

            "booking_id": str(uuid.uuid4()),

            "booking_timestamp": datetime.now().isoformat()

        }
 
        return success_response(response)
 
    except KeyError as e:

        logger.error(f"Missing key in event: {e}")

        return error_response(f"Missing key: {str(e)}")

    except Exception as ex:

        logger.error(f"Unexpected error: {ex}")

        return error_response(f"Unexpected error: {str(ex)}")
 
 
def success_response(body: Dict[str, Any]) -> Dict[str, Any]:

    return {

        "statusCode": HTTPStatus.OK,

        "headers": {"Content-Type": "application/json"},

        "body": json.dumps(body)

    }
 
def error_response(message: str) -> Dict[str, Any]:

    return {

        "statusCode": HTTPStatus.BAD_REQUEST,

        "headers": {"Content-Type": "application/json"},

        "body": json.dumps({"error": message})

    }

 
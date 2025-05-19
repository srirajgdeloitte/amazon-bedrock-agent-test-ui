import json
import logging
from typing import Dict, Any
from http import HTTPStatus
from datetime import timedelta, datetime
import ast 
from fuzzywuzzy import fuzz

logger = logging.getLogger()
logger.setLevel(logging.INFO)

month_dict = {
    "January": 1,
    "February": 2,
    "March": 3,
    "April": 4,
    "May": 5,
    "June": 6,
    "July": 7,
    "August": 8,
    "September": 9,
    "October": 10,
    "November": 11,
    "December": 12
}


def get_current_month():
    """
    Returns the current month as a string.
    """
    return month_dict.get(datetime.now().strftime("%B"))


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler for processing Bedrock agent requests.

    Args:
        event (Dict[str, Any]): The Lambda event containing action details
        context (Any): The Lambda context object

    Returns:
        Dict[str, Any]: Response containing the action execution results

    Raises:
        KeyError: If required fields are missing from the event
    """
    logger.info(f"Received event: {json.dumps(event)}")
    try:
        action_group = event['actionGroup']
        apiPath = event['apiPath']
        httpMethod = event['httpMethod']
        parameters = event.get('parameters', [])
        message_version = event.get('messageVersion', 1)

        # Execute your business logic here. For more information,
        # refer to: https://docs.aws.amazon.com/bedrock/latest/userguide/agents-lambda.html
        resort_names = None
        month = None
        response_body = {}
        available_resort_names = []
        MAHINDRA_RESORTS = json.load(open('resort_details.json'))

        for param in parameters:
            if param['name'] == 'resort_names':
                x = param['value']

                # Remove brackets and split
                items = x.strip('[]').split(',')

                # Strip whitespace and wrap each item in quotes
                resort_names = [item.strip() for item in items]
            elif param['name'] == 'month':
                month = param['value']

        current_month = get_current_month()
        input_month = month_dict.get(month)


        logger.info(
            f"Checking Availability For: resort_name={resort_names}, month={month}")

        if not resort_names or not month:
            response_body = {
                'application/json': {
                    'body': f'I need the resort name and the start and end dates to check availability.'
                }
            }
        else:
            try:
                if current_month > input_month:
                    response_body = {
                        'application/json': {
                            'body': f'Sorry, I cannot plan your vacation in past. Please select a future month.'
                        }
                    }

                else:
                    for resort_name in resort_names:
                        for resort in MAHINDRA_RESORTS:
                            similarity_score = fuzz.ratio(resort_name, resort['hotel_name'])
                            if similarity_score >= 75 and resort['Availability'][0]['2025'][month]=='True':
                                available_resort_names.append(resort_name)

            except Exception as excp:
                logger.error('Exception occurred: %s', str(excp))
                response_body = {
                    'application/json': {
                        'body': f'Error occurred while checking availability: {str(excp)}'
                    }
                }

        logger.info(f"Available Resorts: {available_resort_names}")

        if len(available_resort_names) > 0:
            response_body = {
                'application/json': {
                    'body': f'Great! I can plan your vacation in {available_resort_names} for {month}.'
                }
            }
        else:
            response_body = {
                'application/json': {
                    'body': f'Sorry, I cannot plan your vacation in {resort_names} for {month}.'
                }
            }

        action_response = {
            'actionGroup': action_group,
            'apiPath': apiPath,
            'httpMethod': httpMethod,
            'httpStatusCode': 200,
            'responseBody': response_body
        }
        response = {
            'response': action_response,
            'messageVersion': message_version
        }

        logger.info('Response: %s', response)
        return response

    except KeyError as e:
        logger.error('Missing required field: %s', str(e))
        return {
            'statusCode': HTTPStatus.BAD_REQUEST,
            'body': f'Error: {str(e)}'
        }
    except Exception as e:
        logger.error('Unexpected error: %s', str(e))
        return {
            'statusCode': HTTPStatus.INTERNAL_SERVER_ERROR,
            'body': 'Internal server error'
        }

 
with open('resort_details.json', 'r') as f:
            raw = f.read()
            logger.info('here', raw)  # For debugging
            MAHINDRA_RESORTS = json.loads(raw)
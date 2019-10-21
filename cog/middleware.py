from flask import request
from functools import wraps
import requests
from CTRegisterMicroserviceFlask import request_to_microservice

class DatasetService(object):

    @staticmethod
    def execute(config):
        response = request_to_microservice(config)
        if not response or response.get('errors'):
            raise LayerNotFound(message='Layer not found')

        layer = response.get('data', None).get('attributes', None)
        return layer

    @staticmethod
    def get(dataset_id):
        config = {
            'uri': '/dataset/'+dataset_id,
            'method': 'GET'
        }
        return DatasetService.execute(config)


def parse_payload(func):
    """Get payload data"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        logging.info(f'[POST]: Recieved {payload}')
        kwargs["payload"] = request.args.get('payload', {'payload': None})
        return func(*args, **kwargs)
    return wrapper


def get_layer(func):
    """Get geodata"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            if kwargs['map_object'] is None:
                layer = kwargs['layer']
                logging.debug('Getting layer ' + layer)
                kwargs["layer_obj"] = LayerService.get(layer)
            return func(*args, **kwargs)
        except LayerNotFound as e:
            return error(status=404, detail=e.message)
        except Exception as e:
            return error(detail='Generic error')
    return wrapper



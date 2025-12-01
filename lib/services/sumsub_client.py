import logging
import time
import hashlib
import hmac
import json

import requests
import subprocess
# from lib.cache import PrefixedRedisCache
from exchange.settings.kyc import SUMSUB_SECRET_KEY, SUMSUB_APP_TOKEN

logger = logging.getLogger(__name__)
# cache = PrefixedRedisCache.get_cache(prefix='sumsub-app-cache-')
REQUEST_TIMEOUT = 60
SUMSUB_TEST_BASE_URL = "https://api.sumsub.com"

def sign_request(request: requests.Request) -> requests.PreparedRequest:
    prepared_request = request.prepare()
    now = int(time.time())
    method = request.method.upper()
    path_url = prepared_request.path_url  # includes encoded query params
    # could be None so we use an empty **byte** string here
    body = b'' if prepared_request.body is None else prepared_request.body
    if isinstance(body, str):
        body = body.encode('utf-8')
    data_to_sign = str(now).encode('utf-8') + method.encode('utf-8') + path_url.encode('utf-8') + body
    logger.info("data_to_sign: %s", data_to_sign)
    # hmac needs bytes
    signature = hmac.new(
        SUMSUB_SECRET_KEY.encode('utf-8'),
        data_to_sign,
        digestmod=hashlib.sha256
    )
    logger.info("signature: %s", signature.hexdigest())
    prepared_request.headers['X-App-Token'] = SUMSUB_APP_TOKEN
    prepared_request.headers['X-App-Access-Ts'] = str(now)
    prepared_request.headers['X-App-Access-Sig'] = signature.hexdigest()
    logger.info("headers: %s", prepared_request.headers)
    return prepared_request

def get_access_token(external_user_id, level_name):
    logger.info(f'Getting access token for user: %s, level: %s', external_user_id, level_name)
    # https://docs.sumsub.com/reference/generate-access-token
    body = {'userId': external_user_id, 'levelName': level_name}
    headers = {'Content-Type': 'application/json',
               'Content-Encoding': 'utf-8'
               }
    
    resp = sign_request(requests.Request('POST', SUMSUB_TEST_BASE_URL + '/resources/accessTokens/sdk',
                                         data=json.dumps(body),
                                         headers=headers))
    s = requests.Session()
    response = s.send(resp, timeout=REQUEST_TIMEOUT)
    logger.info(response.text)
    return response.json()
    # token = (response.json()['token'])

    # return token

class SumSubClient:
    session = requests.Session()
    HOST = 'https://api.sumsub.com'

    def __init__(self, host=None):
        if host:
            self.HOST = host

    def post(self, url, return_result=True, **kwargs):
        try:
            headers = kwargs.pop('headers', {})
            resp = self.sign_request(requests.Request('POST',
                                                      f'{self.HOST}{url}',
                                                      headers=headers,
                                                      **kwargs))
            response = self.session.send(resp)
            response.raise_for_status()
            if return_result:
                return response.json()
        except Exception:
            logger.error(f'error on {url}: {kwargs}', exc_info=True)
            raise

    def get(self, url, **kwargs):
        try:
            headers = kwargs.pop('headers', {})
            resp = self.sign_request(requests.Request('GET',
                                                      f'{self.HOST}{url}',
                                                      headers=headers,
                                                      **kwargs))
            response = self.session.send(resp)
            response.raise_for_status()
            return response.json()
        except Exception:
            logger.error(f'error on {url}: {kwargs}', exc_info=True)
            raise
    
    def get_acces_token_v1(self, external_user_id, level_name='id-only'):
        #    'ttlInSecs': '600',
        params = {
            'userId': external_user_id,
            'levelName': level_name}
        headers = {'Content-Type': 'application/json',
                   'Content-Encoding': 'utf-8'
                   }
        resp = self.sign_request_v2(requests.Request('POST', self.HOST + '/resources/accessTokens/sdk',
                                                #   params=params,
                                                  data=json.dumps(params),
                                                  headers=headers))
        response = self.session.send(resp)
        logger.info("res: %s", response.text)
        return response.json()
#         return {
#     "token": "_act-sbx-jwt-eyJhbGciOiJub25lIn0.eyJqdGkiOiJfYWN0LXNieC1mYjM2MDJjYS1hNTBlLTQ5YjUtOGNhZi03ZDEwMDEzYjc1ZTQtdjIiLCJ1cmwiOiJodHRwczovL2FwaS5zdW1zdWIuY29tIn0.-v2",
#     "userId": "random-postman-user-pq2joj5im"
# }
    def get_access_token(self, external_user_id, level_name='id-only'):
        command = ["/usr/local/bin/python", "AppTokenPythonExample.py", external_user_id]
        try:
            result = subprocess.run(
                command,             # Command and arguments as a list
                capture_output=True, # Capture standard output and standard error
                text=True,           # Return output as a string (instead of bytes)
                check=True           # Raise an exception if the command fails
            )

            # Get the standard output as a string
            output = result.stdout.strip()
            logger.info("Command Output:", output)
            return {
                "token": output,
                "userId": external_user_id
            }

        except subprocess.CalledProcessError as e:
            logger.error(f"Error running command: {e}", exc_info=True)
            # raise

        # return get_access_token(external_user_id, level_name)
    def get_access_token_v0(self, external_user_id, level_name='id-only'):
        # https://docs.sumsub.com/reference/generate-access-token
        body = {'userId': external_user_id, 'levelName': level_name}
        headers = {'Content-Type': 'application/json',
                'Content-Encoding': 'utf-8'
                }
        
        resp = sign_request(requests.Request('POST', SUMSUB_TEST_BASE_URL + '/resources/accessTokens/sdk',
                                            data=json.dumps(body),
                                            headers=headers))
        s = requests.Session()
        response = s.send(resp, timeout=REQUEST_TIMEOUT)
        logging.info(response.text)
        token = (response.json()['token'])

        return response.json()
    def sign_request_v2(self,request: requests.Request) -> requests.PreparedRequest:
        prepared_request = request.prepare()
        now = int(time.time())
        method = request.method.upper()
        path_url = prepared_request.path_url  # includes encoded query params
        # could be None so we use an empty **byte** string here
        body = b'' if prepared_request.body is None else prepared_request.body
        if isinstance(body, str):
            body = body.encode('utf-8')
        data_to_sign = str(now).encode('utf-8') + method.encode('utf-8') + path_url.encode('utf-8') + body
        # hmac needs bytes
        signature = hmac.new(
            SUMSUB_SECRET_KEY.encode('utf-8'),
            data_to_sign,
            digestmod=hashlib.sha256
        )
        prepared_request.headers['X-App-Token'] = SUMSUB_APP_TOKEN
        prepared_request.headers['X-App-Access-Ts'] = str(now)
        prepared_request.headers['X-App-Access-Sig'] = signature.hexdigest()
        return prepared_request


    def sign_request(self, request):
        prepared_request = request.prepare()
        now = int(time.time())
        method = request.method.upper()
        path_url = prepared_request.path_url
        body = b'' if prepared_request.body is None else prepared_request.body
        if isinstance(body, str):
            body = body.encode('utf-8')
        data_to_sign = str(now).encode(
            'utf-8') + method.encode('utf-8') + path_url.encode('utf-8') + body
        logger.info("data_to_sign: %s", data_to_sign)
        signature = hmac.new(
            SUMSUB_SECRET_KEY.encode('utf-8'),
            data_to_sign,
            digestmod=hashlib.sha256
        )
        prepared_request.headers['X-App-Token'] = SUMSUB_APP_TOKEN
        prepared_request.headers['X-App-Access-Ts'] = str(now)
        prepared_request.headers['X-App-Access-Sig'] = signature.hexdigest()
        logger.info("headers: %s", prepared_request.headers)
        return prepared_request

    def get_applicant_data(self, applicantId):
        return self.get(f'/resources/applicants/{applicantId}')

    def get_applicant_doc_status(self, applicantId):
        return self.get(
            f'/resources/applicants/{applicantId}/requiredIdDocsStatus')

    def get_image(self, inspectionId, imageId):
        return self.get(
            f'/resources/inspections/{inspectionId}/resources/{imageId}')

from gevent import monkey  # fmt: skip
monkey.patch_all()

import logging
import gevent
import os
import json

from flask import Flask, request
from guessit import api as GuessitApi

from src.base import const
from src.base.framework import (
    JsonResponse,
)
# from src.base.session import LazySessionInterface, MongoStore

application = app = Flask(__name__)
# application.config.update(config.FLASK_CONFIG)
application.url_map.strict_slashes = False
# application.session_interface = LazySessionInterface(MongoStore(xplayer_db.session))

# print(os.path.join(os.getcwd(), 'src/config/guessit_conf.json'))
# with open(os.path.join(os.getcwd(), 'src/config/guessit_conf.json')) as f:
#     print(GuessitApi.configure(options=json.load(f)))
# print(GuessitApi.configure(options=json.load(os.path.join(os.getcwd(), 'src/config/guessit_conf.json'))))

# from src.logic.apscheduler import background_scheduler  # noqa: F401

# background_scheduler.start()

'''
@application.before_request
def before_request():
    logging.info(
        "%s req_path: %s, query: %s",
        request.method,
        request.path,
        request.query_string,
    )


@application.after_request
def after_request(response):
    if not request.path.endswith('/check_cdn') and not response.headers.get('Cache-Control'):
        response.headers['Cache-Control'] = "no-cache"

    resp = getattr(response, 'decrypted_data', None)
    resp = resp or (response.get_json() if response.is_json else response.data)
    ntes_trace_id = request.headers.get(const.HEADER.NTES_TRACE_ID)
    if not config.DEBUG:
        LENGTH = 5000
        resp = str(resp)
        resp = resp[:LENGTH] + ' ||TRUNCATE..' if resp and len(resp) > LENGTH * 2 else resp
    logging.info(
        "%s resp_path: %s, data: %s",
        request.method,
        request.path,
        resp,
    )
    if ntes_trace_id:
        response.headers[const.HEADER.XPLAYER_TRACE_ID] = ntes_trace_id
    return response
'''

@application.errorhandler(400)
@application.errorhandler(422)
def bad_params(e):
    logging.warning('resp_path: %s, bad_param: %s', request.path, str(e.exc))
    return JsonResponse(const.API_ERROR.BAD_PARAMS, data={'error': str(e.exc)})


@application.errorhandler(404)
def page_not_found(e):
    return JsonResponse(const.API_ERROR.NOT_FOUND)


@application.errorhandler(405)
def method_not_allowed(e):
    return JsonResponse(const.API_ERROR.METHOD_NOT_ALLOWED)


@application.errorhandler(Exception)
def default_exception_handler(e):
    logging.exception('unexpected error')
    return JsonResponse(const.API_ERROR.SERVER_ERROR)


view_modules = [
    'common',
]

for name in view_modules:
    module = __import__("src.views.%s" % name, fromlist=[name])
    application.register_blueprint(getattr(module, name.split('.')[-1]))


if __name__ == '__main__':
    application.run(host='127.0.0.1', port=10087)
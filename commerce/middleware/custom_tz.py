import pytz
from django.utils import timezone
from urllib import request as requests
import json

class TimezoneMiddleware(object):
    """
    Middleware to properly handle the users timezone
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        user_time_zone = request.session.get('user_time_zone', None)
        try:
            if user_time_zone is None:
                with requests.urlopen(f'http://ip-api.com/json/') as response: 
                    freegeoip_response = json.loads(response.read().decode('utf8'))

                user_time_zone = freegeoip_response.get('timezone')
                if user_time_zone:
                    request.session['user_time_zone'] = user_time_zone
            timezone.activate(pytz.timezone(user_time_zone))
        except Exception as er:
            print("custom_tz:er: ", er)

        response = self.get_response(request)
        return response
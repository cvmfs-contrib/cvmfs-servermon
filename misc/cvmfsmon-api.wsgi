import os, sys, re
import cvmfsmon_api
import cgi

# A URL is of the form:
# /cvmfsmon/api/v1.0/montests&param1=value1&param2=value2
# The "/cvmfsmon/api" is stripped off by apache.
# The value of "montests" and the params is determined in the 
#  cvmfsmon_api.dispatch function.

pattern = re.compile('^/(v[^/]*)/([^&]*)(&|)(.*)$')

def application(environ, start_response):
    request_url  = environ['PATH_INFO']
    match_result = pattern.search(request_url)

    if not match_result:
        return cvmfsmon_api.bad_request(start_response, 'malformed api URL: ' + request_url)

    version, montests, separator, paramstring = match_result.groups()

    try:
        # python 2.6 and later is suppsed to use urlparse instead of cgi
        parameters = cgi.parse_qs(paramstring)
    except:
        return cvmfsmon_api.bad_request(start_response, 'failure parsing parameters: ' + paramstring)

    return cvmfsmon_api.dispatch(version, montests, parameters, start_response, environ)

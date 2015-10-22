import os, sys, socket, urllib2, anyjson
import cvmfsmon_updated

negative_expire_secs = 60*2;        # 2 minutes
positive_expire_secs = 60*2;        # 2 minutes
timeout_secs = 5 		    # tries twice for 5 seconds

def error_request(start_response, response_code, response_body):
    response_body = response_body + '\n'
    start_response(response_code,
                   [('Cache-control', 'max-age=' + str(negative_expire_secs)),
                    ('Content-Length', str(len(response_body)))])
    return [response_body]

def bad_request(start_response, reason):
    response_body = 'Bad Request: ' + reason
    return error_request(start_response, '400 Bad Request', response_body)

def good_request(start_response, response_body):
    response_body = response_body + '\n'
    response_code = '200 OK'
    start_response(response_code,
    		  [('Content-Type', 'text/plain'),
		   ('Cache-Control', 'max-age=' + str(positive_expire_secs)),
		   ('Content-Length', str(len(response_body)))])
    return [response_body]

def parse_api_conf():
    aliases = {}
    aliases['local'] = '127.0.0.1'
    excludes = []
    for line in open('/etc/cvmfsmon/api.conf', 'r').read().split('\n'):
	words = line.split()
	if words:
	    if words[0] == 'serveralias':
		parts = words[1].split('=')
		aliases[parts[0]] = parts[1]
	    elif words[0] == 'excluderepo':
		excludes.append(words[1])
    return aliases, excludes

def dispatch(version, montests, parameters, start_response, environ):
    aliases, excludes = parse_api_conf()

    if 'server' in parameters:
	serveralias = parameters['server'][0]
    else:
	serveralias = 'local'
    if serveralias in aliases:
	server = aliases[serveralias]
    else:
	return bad_request(start_response, 'unrecognized server alias ' + serveralias)

    socket.setdefaulttimeout(timeout_secs)

    url = 'http://' + server + '/cvmfs/info/repositories'
    repos = []
    try:
	json_data = urllib2.urlopen(url).read()
	repos_info = anyjson.deserialize(json_data)
	if 'replicas' in repos_info:
	    for repo_info in repos_info['replicas']:
		repos.append(repo_info['name'])
    except:
	return error_request(start_response, '502 Bad Gateway', url + ' error: ' + str(sys.exc_info()[0]) + ' ' + str(sys.exc_info()[1]))

    allresults = []
    for repo in repos:
	results = []
	if montests == 'ok':
	    results.append([ 'ok', repo, 'OK', '' ])
	if (montests == "updated") or (montests == "all"):
	    results.append(cvmfsmon_updated.runtest(repo, 'http://' + server))
	if results == []:
	    return bad_request(start_response, 'unrecognized montests ' + montests)
	allresults.extend(results)

    print allresults

    return good_request(start_response, 'OK')


# Implement the cvmfsmon API
# A URL is of the form:
#  /cvmfsmon/api/v1.0/montests&param1=value1&param2=value2
# The URL is parsed by the calling function, and the params come in a 
#   dictionary of keys, each with a list of values
# Currently supported "montests" are
#  ok - always returns OK
#  all - runs all applicable tests but 'ok'
#  updated - verifies that updates are happening on a stratum 1
# Currently supported parameters are
#  format - value one of the following (default: list)
#    status - reports only one line: OK, WARNING, or CRITICAL
#    list - reports a line for each available status, followed by colon, 
#      followed by a comma-separated list of repositories at that status.
#    details - detailed json output with all the tests and messages
#  server - value is either 'local' (the default, indicating localhost) or
#    an alias of a server as defined in /etc/cvmfsmon/api.conf

import os, sys, socket, urllib2, anyjson, pprint, StringIO, string
import cvmfsmon_updated

negative_expire_secs = 60*2;        # 2 minutes
positive_expire_secs = 60*2;        # 2 minutes
timeout_secs = 5                    # tries twice for 5 seconds

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

    url = 'http://' + server + '/cvmfs/info/v1/repositories.json'
    repos = []
    try:
        request = urllib2.Request(url, headers={"Cache-control" : "max-age=60"})
        json_data = urllib2.urlopen(request).read()
        repos_info = anyjson.deserialize(json_data)
        if 'replicas' in repos_info:
            for repo_info in repos_info['replicas']:
                # the url always has the visible name
                # use "str" to convert from unicode to string
                repos.append(str(repo_info['url'].replace('/cvmfs/','')))
    except:
        return error_request(start_response, '502 Bad Gateway', url + ' error: ' + str(sys.exc_info()[0]) + ' ' + str(sys.exc_info()[1]))

    allresults = []
    for repo in repos:
        if repo in excludes:
            continue
        results = []
        if montests == 'ok':
            results.append([ 'ok', repo, 'OK', '' ])
        if (montests == "updated") or (montests == "all"):
            results.append(cvmfsmon_updated.runtest(repo, 'http://' + server))
        if results == []:
            return bad_request(start_response, 'unrecognized montests ' + montests)
        allresults.extend(results)

    format = 'list'
    if 'format' in parameters:
        formats = parameters['format']
        l = len(formats)
        if l > 0:
            format = formats[l - 1]

    body = ""
    if format == 'status':
        worststatus = 'OK'
        for result in allresults:
            status = result[2]
            if status == 'CRITICAL':
                worststatus = 'CRITICAL'
            elif (status == 'WARNING') and (worststatus != 'CRITICAL'):
                worststatus = 'WARNING'
        body = worststatus + '\n'
    elif format == 'details':
        details = {}
        for result in allresults:
            test = result[0]
            status = result[2]
            repomsg = {'repo' : result[1], 'msg': result[3]}
            if status in details:
                if test in details[status]:
                    details[status][test].append(repomsg)
                else:
                    details[status][test] = [repomsg]
            else:
                details[status] = {}
                details[status][test] = [repomsg]

        output = StringIO.StringIO()
        pprint.pprint(details, output)
        body = output.getvalue()
        output.close()
        body = string.replace(body,"'", '"')
    else:  # list format
        repostatuses = {}
        for result in allresults:
            repo = result[1]
            status = result[2]
            worststatus = 'OK'
            if repo in repostatuses:
                worststatus = repostatuses[repo]
            if status == 'CRITICAL':
                worststatus = status
            elif (status == 'WARNING') and (worststatus != 'CRITICAL'):
                worststatus = status
            repostatuses[repo] = worststatus

        statusrepos = {}
        for repo in repostatuses:
            status = repostatuses[repo]
            if not status in statusrepos:
                statusrepos[status] = []
            statusrepos[status].append(repo)
        for status in ['CRITICAL', 'WARNING', 'OK']:
            if status in statusrepos:
                statusrepos[status].sort()
                body += status + ':' + ",".join(statusrepos[status]) + '\n'

    return good_request(start_response, body)


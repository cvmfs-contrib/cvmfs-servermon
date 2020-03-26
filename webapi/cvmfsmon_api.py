# Implement the cvmfsmon API
# A URL is of the form:
#  /cvmfsmon/api/v1.0/montests&param1=value1&param2=value2
# The URL is parsed by the calling function, and the params come in a 
#   dictionary of keys, each with a list of values
# Currently supported "montests" are
#  ok - always returns OK
#  all - runs all applicable tests but 'ok'
#  updated - verifies that updates are happening on a stratum 1
#  gc - verifies that repositories that have done garbage collection
#       have done it successfully recently
# Currently supported parameters are
#  format - value one of the following (default: list)
#    status - reports only one line: OK, WARNING, or CRITICAL
#    list - reports a line for each available status, followed by colon, 
#      followed by a comma-separated list of repositories at that status.
#    details - detailed json output with all the tests and messages
#  server - value is either 'local' (the default, indicating localhost) or
#    an alias of a server as defined in /etc/cvmfsmon/api.conf

import os, sys, socket, urllib2, anyjson, pprint, StringIO, string
import time, threading
import cvmfsmon_updated, cvmfsmon_gc

negative_expire_secs = 60*2         # 2 minutes
positive_expire_secs = 60*2         # 2 minutes
timeout_secs = 5                    # tries twice for 5 seconds
request_max_secs = 30               # maximum cache seconds when reading
config_update_time = 60             # seconds between checking config file

conf_mod_time = 0
last_config_time = 0
aliases = {}
excludes = []
limits = {}
lock = threading.Lock()

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
    global aliases, excludes, limits
    global conf_mod_time
    conffile = '/etc/cvmfsmon/api.conf'
    try:
        modtime = os.stat(conffile).st_mtime
        if modtime == conf_mod_time:
            # no change
            return
        conf_mod_time = modtime

        aliases = { 'local' : '127.0.0.1' }
        excludes = []
        limits = {
            'updated-warning': 8,
            'updated-critical': 24,
            'gc-warning': 10,
            'gc-critical': 20
        }

        for line in open(conffile, 'r').read().split('\n'):
            words = line.split()
            if words:
                if words[0] == 'serveralias' and len(words) > 1:
                    parts = words[1].split('=')
                    aliases[parts[0]] = parts[1]
                elif words[0] == 'excluderepo':
                    excludes.append(words[1])
                elif words[0] == 'limit' and len(words) > 1:
                    parts = words[1].split('=')
                    limits[parts[0]] = int(parts[1])

        print('processed ' + conffile)
        print('aliases: ' + str(aliases))
        print('excludes: ' + str(excludes))
        print('limits: ' + str(limits))
    except Exception, e:
	print('error reading ' + conffile + ', continuing: ' + str(e))
        conf_mod_time = 0

def dispatch(version, montests, parameters, start_response, environ):
    global last_config_time
    now = time.time()
    lock.acquire()
    if now - config_update_time > last_config_time:
        last_config_time = now
        parse_api_conf()
    lock.release()

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
    replicas = []
    repos = []
    try:
        request = urllib2.Request(url, 
            headers={"Cache-control" : "max-age=" + str(request_max_secs)})
        json_data = urllib2.urlopen(request).read()
        repos_info = anyjson.deserialize(json_data)
        if 'replicas' in repos_info:
            for repo_info in repos_info['replicas']:
                # the url always has the visible name
                # use "str" to convert from unicode to string
                replicas.append(str(repo_info['url'].replace('/cvmfs/','')))
        if 'repositories' in repos_info:
            for repo_info in repos_info['repositories']:
                repos.append(str(repo_info['url'].replace('/cvmfs/','')))
    except:
        return error_request(start_response, '502 Bad Gateway', url + ' error: ' + str(sys.exc_info()[1]))

    allresults = []
    for repo in replicas + repos:
        if repo in excludes:
            continue
        results = []
        if montests == 'ok':
            results.append([ 'ok', repo, 'OK', '' ])
            continue
        errormsg = ""
        doupdated = False
        if (repo in replicas) and ((montests == "updated") or (montests == "all")):
            doupdated = True
        repo_status = {}
        url = 'http://' + server + '/cvmfs/' + repo + '/.cvmfs_status.json'
        try:
            request = urllib2.Request(url, headers={"Cache-control" : "max-age=30"})
            status_json = urllib2.urlopen(request).read()
            repo_status = anyjson.deserialize(status_json)
        except urllib2.HTTPError, e:
            if e.code == 404:
                if doupdated:
                    # for backward compatibility, look for .cvmfs_last_snapshot
                    #   if .cvmfs_status.json was not found
                    try:
                        url2 = 'http://' + server + '/cvmfs/' + repo + '/.cvmfs_last_snapshot'
                        request = urllib2.Request(url2,
                            headers={"Cache-control" : "max-age=" + str(request_max_secs)})
                        snapshot_string = urllib2.urlopen(request).read()
                        repo_status = {"last_snapshot": snapshot_string}
                    except urllib2.HTTPError, e:
                        if e.code == 404:
                            errormsg = url + ' and .cvmfs_last_snapshot Not found'
                        else:
                            errormsg =  str(sys.exc_info()[1])
                    except:
                        errormsg =  str(sys.exc_info()[1])
                else:
                    errormsg = url + ' Not found'
            else:
                errormsg =  str(sys.exc_info()[1])
        except:
            errormsg =  str(sys.exc_info()[1])

        if doupdated:
            results.append(cvmfsmon_updated.runtest(repo, limits, repo_status, errormsg))
        if (montests == "gc") or (montests == "all"):
            results.append(cvmfsmon_gc.runtest(repo, limits, repo_status, errormsg))
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
            if len(result) == 0:
                continue
            status = result[2]
            if status == 'CRITICAL':
                worststatus = 'CRITICAL'
            elif (status == 'WARNING') and (worststatus != 'CRITICAL'):
                worststatus = 'WARNING'
        body = worststatus + '\n'
    elif format == 'details':
        details = {}
        for result in allresults:
            if len(result) == 0:
                continue
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
            if len(result) == 0:
                continue
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


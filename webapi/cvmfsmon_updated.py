import urllib2, sys, datetime, dateutil.parser, dateutil.tz

def runtest(repo, serverurl):
    warning_secs = 8*60*60
    critical_secs = 24*60*60

    testname = 'updated'
    url = serverurl + '/cvmfs/' + repo + '/.cvmfs_last_snapshot'
    try:
	snapshot_string = urllib2.urlopen(url).read()
	snapshot_date = dateutil.parser.parse(snapshot_string)
    except urllib2.HTTPError, e:
	if e.code == 404:
	    return [ testname, repo, 'OK', 'initial snapshot in progress' ]
	return [ testname, repo, 'CRITICAL', url + ' error: ' + str(sys.exc_info()[0]) + ' ' + str(sys.exc_info()[1]) ]
    except:
	return [ testname, repo, 'CRITICAL', url + ' error: ' + str(sys.exc_info()[0]) + ' ' + str(sys.exc_info()[1]) ]

    now = datetime.datetime.now(dateutil.tz.tzutc())
    delta = now-snapshot_date
    diff_secs = delta.days * 24 * 3600 + delta.seconds

    if diff_secs < warning_secs:
	status = 'OK'
    elif diff_secs < critical_secs:
	status = 'WARNING'
    else:
	status = 'CRITICAL'

    if status == 'OK':
	msg = ''
    else:
	msg = 'last successful snapshot ' + str(diff_secs) + ' seconds ago'

    return [ testname, repo, status, msg ]

import sys
import datetime, dateutil.parser, dateutil.tz

def runtest(repo, limits, repo_status, errormsg):
    testname = 'updated'

    warning_hours = limits[testname + '-warning']
    critical_hours = limits[testname + '-critical']

    if errormsg != "":
        if not errormsg.endswith('Not found'):
            return [ testname, repo, 'CRITICAL', 'error: ' + errormsg]
        # else Not found, treat it as initial snapshot in progress
    if 'last_snapshot' in repo_status:
        lastdate_string = repo_status['last_snapshot']
        if lastdate_string == '':
          return [ testname, repo, 'CRITICAL', 'error: empty snapshot date' ]
        try:
            lastdate = dateutil.parser.parse(lastdate_string)
        except:
            msg =  str(str(sys.exc_info()[1]))
            return [ testname, repo, 'CRITICAL', 'error parsing date: ' + msg]
    else:
        return [ testname, repo, 'OK', 'initial snapshot in progress' ]

    now = datetime.datetime.now(dateutil.tz.tzutc())
    delta = now-lastdate
    diff_hours = (delta.days * 24) + (delta.seconds / 3600)

    if diff_hours < warning_hours:
        status = 'OK'
    elif diff_hours < critical_hours:
        status = 'WARNING'
    else:
        status = 'CRITICAL'

    if status == 'OK':
        msg = ''
    else:
        msg = 'last successful snapshot ' + str(diff_hours) + ' hours ago'

    return [ testname, repo, status, msg ]

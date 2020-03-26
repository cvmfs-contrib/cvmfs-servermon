import sys
import datetime, dateutil.parser, dateutil.tz

def runtest(repo, limits, repo_status, errormsg):
    testname = 'gc'

    warning_days = limits[testname + '-warning']
    critical_days = limits[testname + '-critical']

    if errormsg != "":
        if errormsg.endswith('Not found'):
            # ignore repos with a missing status file
            return []
        return [ testname, repo, 'CRITICAL', 'error: ' + errormsg]
    if 'last_gc' in repo_status:
        lastdate_string = repo_status['last_gc']
        if lastdate_string == '':
          return [ testname, repo, 'CRITICAL', url + ' error: empty gc date' ]
        try:
            lastdate = dateutil.parser.parse(lastdate_string)
        except:
            msg =  str(str(sys.exc_info()[1]))
            return [ testname, repo, 'CRITICAL', 'error parsing date: ' + msg]
    else:
        # ignore repos without a last_gc
        return []

    now = datetime.datetime.now(dateutil.tz.tzutc())
    delta = now-lastdate
    diff_days = delta.days

    if diff_days < warning_days:
        status = 'OK'
    elif diff_days < critical_days:
        status = 'WARNING'
    else:
        status = 'CRITICAL'

    if status == 'OK':
        msg = ''
    else:
        msg = 'last successful gc ' + str(diff_days) + ' days ago'

    return [ testname, repo, status, msg ]

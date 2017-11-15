import datetime, dateutil.parser, dateutil.tz

def runtest(repo, repo_status, errormsg):
    warning_hours = 8*60
    critical_hours = 24*60

    testname = 'updated'
    if errormsg != "":
        return [ testname, repo, 'CRITICAL', 'error: ' + errormsg]
    if 'last_snapshot' in repo_status:
        lastdate_string = repo_status['last_snapshot']
        if lastdate_string == '':
          return [ testname, repo, 'CRITICAL', url + ' error: empty snapshot date' ]
        lastdate = dateutil.parser.parse(lastdate_string)
    else:
        return [ testname, repo, 'OK', 'initial snapshot in progress' ]

    now = datetime.datetime.now(dateutil.tz.tzutc())
    delta = now-lastdate
    diff_hours = (delta.days * 24 * 60) + (delta.seconds / 60)

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

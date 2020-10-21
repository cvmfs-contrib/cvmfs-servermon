import sys
import datetime, dateutil.parser, dateutil.tz

def runtest(repo, limits, repo_status, errormsg):
    testname = 'updated'

    warning_hours = limits[testname + '-warning']
    critical_hours = limits[testname + '-critical']

    msg = ''
    multiplier = 1
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
            return [ testname, repo, 'CRITICAL', 'error parsing last_snapshot date: ' + msg]
    else:
        # no 'last_snapshot' found in .cvmfs_status.json
        if 'snapshotting_since' not in repo_status:
            return [ testname, repo, 'WARNING', 'initial snapshot not in progress' ]
        lastdate_string = repo_status['snapshotting_since']
        if lastdate_string == '':
          return [ testname, repo, 'CRITICAL', 'error: empty .cvmfs_is_snapshotting' ]
        try:
            lastdate = dateutil.parser.parse(lastdate_string)
        except:
            msg =  str(str(sys.exc_info()[1]))
            return [ testname, repo, 'CRITICAL', 'error parsing .cvmfs_is_snapshotting date: ' + msg]

        msg = 'initial snapshot started'
        # turn 8 hours into 3 days and 24 hours into 9 days
        multiplier = 9

    now = datetime.datetime.now(dateutil.tz.tzutc())
    delta = now - lastdate
    diff_hours = (delta.days * 24) + int(delta.seconds / 3600)

    if diff_hours < (warning_hours * multiplier):
        status = 'OK'
    elif diff_hours < (critical_hours * multiplier):
        status = 'WARNING'
    else:
        status = 'CRITICAL'

    if status != 'OK':
        if msg == '':
            msg = 'last successful snapshot'
        msg += ' ' + str(diff_hours) + ' hours ago'

    return [ testname, repo, status, msg ]

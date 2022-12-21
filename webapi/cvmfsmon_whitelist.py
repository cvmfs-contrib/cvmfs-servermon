import dateutil.tz
from datetime import datetime


def runtest(repo, limits, whitelist, errormsg):
    testname = 'whitelist'
    warning_hours = limits[testname + '-warning']

    if errormsg != '':
        if errormsg.lower().endswith('not found'):
            # ignore repos with a missing whitelist file
            return []
        return [ testname, repo, 'CRITICAL', 'error: ' + errormsg]

    try:
        utc = dateutil.tz.tzutc()
        for line in whitelist.splitlines():
            if line.startswith('E'):
                expiration_time = (datetime.strptime(line[1:], '%Y%m%d%H%M%S').replace(tzinfo=utc) - datetime.now(utc)).total_seconds() / 3600
                break
        else:
            raise Exception('cannot find expiration time')
    except Exception as e:
        return [ testname, repo, 'CRITICAL', str(e) ]

    if expiration_time < 0:
       return [ testname, repo, 'CRITICAL', 'whitelist is expired' ]
    if expiration_time < warning_hours:
       return [ testname, repo, 'WARNING', 'whitelist expiration time is less than %s hours' % str(warning_hours) ]

    return [ testname, repo, 'OK', '' ]

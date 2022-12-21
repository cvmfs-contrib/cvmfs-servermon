import dateutil.tz
from datetime import datetime

try:
    from urllib import request as urllib_request
except ImportError:  # python < 3
    import urllib2 as urllib_request


def runtest(repo, server, headers, last_geodb_update):
    url = ('http://%s/cvmfs/%s/api/v1.0/geo/cvmfs-stratum-one.cern.ch'
           '/cvmfs-s1fnal.opensciencegrid.org,cvmfs-stratum-one.cern.ch,cvmfs-stratum-one.ihep.ac.cn'
           % (server, repo))
    msg = ''
    try:
        if last_geodb_update != '':
            utc = dateutil.tz.tzutc()
            diff_days = (datetime.now(utc) - datetime.strptime(last_geodb_update, '%a %b %d %H:%M:%S %Z %Y').replace(tzinfo=utc)).days
            if diff_days > 30:
                msg = 'last geodb update ' + str(diff_days) + ' days ago'
        request = urllib_request.Request(url, headers=headers)
        response = urllib_request.urlopen(request)
        output = response.read().decode('utf-8').strip()
        status = 'OK' if output == '2,1,3' and msg == '' else 'WARNING'
    except Exception as e:
        status = 'CRITICAL'
        msg = str(e)

    return [ 'geo', repo, status, msg ]


try:
    from urllib import request as urllib_request
except ImportError:  # python < 3
    import urllib2 as urllib_request


def runtest(repo, server, headers):
    url = ('http://%s/cvmfs/%s/api/v1.0/geo/cvmfs-stratum-one.cern.ch'
           '/cvmfs-s1fnal.opensciencegrid.org,cvmfs-stratum-one.cern.ch,cvmfs-stratum-one.ihep.ac.cn'
           % (server, repo))
    msg = ''
    try:
        request = urllib_request.Request(url, headers=headers)
        response = urllib_request.urlopen(request)
        output = response.read().decode('utf-8').strip()
        status = 'OK' if output == '2,1,3' else 'WARNING'
    except Exception as e:
        status = 'CRITICAL'
        msg = str(e)

    return [ 'geo', repo, status, msg ]


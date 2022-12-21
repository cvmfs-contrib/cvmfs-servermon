def runtest(repo, check_status, errormsg):
    testname = 'check'

    if errormsg != '':
        if errormsg.endswith('Not found'):
            # ignore repos with a missing status file
            return []
        return [ testname, repo, 'CRITICAL', 'error: ' + errormsg]

    if check_status == 'failed':
        return [ testname, repo, 'WARNING', 'cvmfs_server check failure']

    return [ testname, repo, 'OK', '']

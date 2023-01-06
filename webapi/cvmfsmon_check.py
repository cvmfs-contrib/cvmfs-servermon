def runtest(repo, repo_status, errormsg):
    testname = 'check'

    if errormsg != '':
        if errormsg.lower().endswith('not found'):
            # ignore repos with a missing status file
            return []
        return [ testname, repo, 'CRITICAL', 'error: ' + errormsg]

    check_status = repo_status.get('check_status', '')

    if check_status == '':
        return []

    if check_status == 'failed':
        return [ testname, repo, 'WARNING', 'cvmfs_server check failure']

    return [ testname, repo, 'OK', '']

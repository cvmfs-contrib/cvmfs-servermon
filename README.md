CVMFS Stratum One monitoring assist
===================================

To assist with monitoring cvmfs servers, there is a separate rpm
called \"cvmfs-servermon\". It interprets conditions on cvmfs servers
and makes them available in a friendly API. Currently it monitors two
aspects on Stratum 1 servers (serving \"replicas\") and one on Stratum
0 servers (a.k.a \"release managers\"), and it is designed to be
extended as more test cases are added. It is intended to be very easy
to tie into any local monitoring system that can probe over http.  There
is also a [monitoring probe at CERN](#cern-xsls-availability-monitor)
that uses the interface to monitor many stratum 1s.

cvmfs-servermon can be configured to read from more than one remote
machine, but by default it is configured to read from localhost and
that\'s the easiest way to use it.

If you have a good idea for extension or have any problems please create a
[github issue](https://github.com/cvmfs-contrib/cvmfs-servermon/issues).

Installation and configuration
------------------------------

To install on a RHEL6-compatible or RHEL7-compatible machine, do the
following. If you have not yet set up the cvmfs-contrib repository,
first do that as instructed on the
[cvmfs-contrib home page](https://cvmfs-contrib.github.io).

Then install cvmfs-servermon:

    # yum install -y cvmfs-servermon

Configuration is optional in a simple file `/etc/cvmfsmon/api.conf`. In
there you can define aliases for remote machines, list repositories you
want to exclude from monitoring, and change the default test limits. See
the comments in the file.

If you are using a shared cvmfs httpd configuration file and not letting
the cvmfs\_server command manage the httpd configuration itself, then it
needs a small modification. In particular, with the configuration
recommended on the
[StratumOnes twiki](https://twiki.cern.ch/twiki/bin/view/CvmFS/StratumOnes#2_1_X_Configuration),
add `:/usr/share/cvmfs-servermon/webapi` to the end of the
WSGIDaemonProcess python-path. Reload httpd after making that change.

API
---

The web API is very simple. URLs are of the following format:

    /cvmfsmon/api/v1.0/montests&param1=value1&param2=value2

\"montests\" are currently one of the following:

1.  \"ok\" - always returns OK (useful for just getting a list of
    repositories)
2.  \"all\" - runs all applicable tests but \'ok\'
3.  \"updated\" - verifies that updates are happening to the
    repositories of a stratum 1. If no updates have happened in the
    previous 8 hours, a repository is considered to be OK. If updates
    last occurred between 8 and 24 hours ago, a repository will be in
    WARNING condition. If the last update happened more than 24 hours
    ago, a repository will be in CRITICAL condition. The limits of 8 and
    24 can be changed in `/etc/cvmfsmon/api.conf`.
4.  \"gc\" - verifies that repositories that have ever had garbage
    collection run on them, on a stratum 0 or a stratum 1, have
    successfully completed garbage collection recently. If no successful
    garbage collections have happened in the last 10 days and less than
    20 days ago, the repository will be in a WARNING condition, and it
    will be in CRITICAL condition if the last successful garbage
    collection was more than 20 days ago. The limits can be changed in
    `/etc/cvmfsmon/api.conf`.

The params are all optional. The currently supported params are:

1.  \"format\" - value is one of the following:
    1.  \"status\" - only returns one of the following on one line: OK,
        WARNING, or CRITICAL. The condition returned is the worst one of
        any of the tests.
    2.  \"list\" - (default if format not specified) - reports one line
        for each current status (in the order of CRITICAL, WARNING, OK)
        followed by a colon and a comma-separated list of repositories
        in that condition.
    3.  \"details\" - returns a detailed json-formatted list of all
        conditions of every montest, the repositories in those
        conditions, and any messages explaining the conditions.
2.  \"server\" - value is an alias defined in `/etc/cvmfsmon/api.conf`.
    Default is \"local\" which maps to the hostname \"localhost\".

Examples
--------

Try clicking on the following or reading them with curl or wget:

- <http://hcc-cvmfs.unl.edu/cvmfsmon/api/v1.0/all&format=status>
- <http://hcc-cvmfs.unl.edu/cvmfsmon/api/v1.0/ok>
- <http://hcc-cvmfs.unl.edu/cvmfsmon/api/v1.0/all>
- <http://hcc-cvmfs.unl.edu/cvmfsmon/api/v1.0/all&format=details>


CERN XSLS availability monitor
------------------------------

cvmfs-servermon is intended to be used easily by any site\'s own
monitoring system, but there is also a monitoring system at CERN that
tracks the status of all the major stratum 1s that support
cvmfs-servermon. The CERN monitoring system runs every 15 minutes, and
whenever the status has changed for two probes in a row it sends an
email to the
[cvmfs-stratum-alarm@cern.ch](mailto:cvmfs-stratum-alarm@cern.ch)
mailing list. For a graphical history it also uploads the status to
[CERN\'s kibana-based XSLS availability website](https://meter.cern.ch/public/_plugin/kibana/#/dashboard/elasticsearch/Metrics:%20Availability?query=cvmfs_stratum1mon*)
(via the mechanism documented
[here](https://itmon.web.cern.ch/itmon/recipes/how_to_publish_service_metrics.html) and
[here](https://itmon.web.cern.ch/itmon/recipes/how_to_create_a_service_xml.html).
If you'd like a change to the stratum 1s that are monitored, contact
[cvmfs-servermon-support@cern.ch](mailto:cvmfs-servermon-support@cern.ch).
In order to be monitored, a stratum 1 needs to either be running
cvmfs-server-2.2.X or later, or have cvmfs-servermon installed (or
both).

The machine at CERN that is doing the probes is wlcg-squid-monitor.cern.ch.
cvmfs-servermon is installed there, so it can read the status remotely
from stratum 1s. The primary advantage to running cvmfs-servermon on
the stratum 1s themselves is that that allows the stratum 1
administrator to choose when to exclude a repository from monitoring
(by configuring it in `/etc/cvmfsmon/api.conf`). Also, that reduces
the number of remote TCP connections needed; a remote cvmfs-servermon
has to read the status of each repository separately.


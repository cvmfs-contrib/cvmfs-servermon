Summary: CernVM File System Server Monitoring
Name: cvmfs-servermon
Version: 1.29
# The release_prefix macro is used in the OBS prjconf, don't change its name
%define release_prefix 1
Release: %{release_prefix}%{?dist}
BuildArch: noarch
Group: Applications/System
License: BSD
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
Source0: https://github.com/cvmfs/%{name}/archive/%{name}-%{version}.tar.gz

Requires: httpd
%if %{rhel} > 7
Requires: python3
Requires: python3-mod_wsgi
Requires: python3-dateutil
%else
Requires: mod_wsgi
Requires: python-dateutil
%endif

%description
Provides an api for monitoring a cvmfs-server installation or multiple
cvmfs-server installations.

%prep
%setup -q

%build
%if %{rhel} < 7
sed 's/{ACCESS_CONTROL}/Order allow,deny\n  Allow from all/' misc/cvmfsmon.conf.in >misc/cvmfsmon.conf
%else
sed 's/{ACCESS_CONTROL}/Require all granted/' misc/cvmfsmon.conf.in >misc/cvmfsmon.conf
%endif

%install
mkdir -p $RPM_BUILD_ROOT/etc/cvmfsmon
install -p -m 644 etc/* $RPM_BUILD_ROOT/etc/cvmfsmon
mkdir -p $RPM_BUILD_ROOT%{_sbindir}
install -p -m 555 compat/* $RPM_BUILD_ROOT%{_sbindir}
mkdir -p $RPM_BUILD_ROOT/etc/httpd/conf.d
install -p -m 444 misc/cvmfsmon.conf $RPM_BUILD_ROOT/etc/httpd/conf.d
mkdir -p $RPM_BUILD_ROOT/var/www/wsgi-scripts/cvmfs-servermon
install -p -m 555 misc/cvmfsmon-api.wsgi $RPM_BUILD_ROOT/var/www/wsgi-scripts/cvmfs-servermon
mkdir -p $RPM_BUILD_ROOT/usr/share/cvmfs-servermon/webapi
install -p -m 444 webapi/* $RPM_BUILD_ROOT/usr/share/cvmfs-servermon/webapi

%post
%if %{rhel} < 7
if /sbin/service httpd status >/dev/null; then
    /sbin/service httpd reload
fi
%else
if systemctl --quiet is-active httpd; then
    systemctl reload httpd
fi
%endif
# Allow our httpd module to read from the network when SELinux is enabled
setsebool -P httpd_can_network_connect 1 2>/dev/null || true

%files
%dir /etc/cvmfsmon
%config(noreplace) /etc/cvmfsmon/*
%{_sbindir}/*
/etc/httpd/conf.d/*
/var/www/wsgi-scripts/*
/usr/share/cvmfs-servermon

%changelog
* Mon Feb 10 2025 Dave Dykstra <dwd@fnal.gov> - 1.29-1
- Fix the /ok api, which was showing nothing.

* Mon Sep  2 2024 Dave Dykstra <dwd@fnal.gov> - 1.28-1
- Prevent json pretty printer from breaking up long strings, the way
  pyhon2 did it.
- Remove old workaround added in version 1.12 because it incorrectly
  reported the status of a repo without an initial snapshot but with 
  a completed gc.

* Mon Oct 23 2023 Dave Dykstra <dwd@fnal.gov> - 1.27-1
- Correct inconsistent tab/space which python3 rejected.
- Fix rare error message regarding an empty last_gc status that pylint
  found was referencing an undefined variable.
- Minor fix in log output for updated-slowrepo.

* Thu Oct 12 2023 Dave Dykstra <dwd@fnal.gov> - 1.26-1
- Add update-slowrepo and limit updated-multiplier configuration options.

* Mon Jul  3 2023 Dave Dykstra <dwd@fnal.gov> - 1.25-1
- Convert from using cgi.parse_qs to either urlparse.parse_qs (python 2)
  or urllib.parse (python 3).  The cgi module does not exist on el9.

* Mon Jul  3 2023 Dave Dykstra <dwd@fnal.gov> - 1.24-1
- Convert from anyjson to the standard python json library because anyjson
  isn't available on el9 and because json is now part of the standard library
  even on el7 python2.

* Tue Mar 14 2023 Dave Dykstra <dwd@fnal.gov> - 1.23-1
- Clear errors from reading .cvmfs_status.json before reading whitelist.
  That was causing stratum 0 repositories that had no status file to skip
  doing the whitelist check.

* Mon Jan  9 2023 Dave Dykstra <dwd@fnal.gov> - 1.22-1
- Add disabletest configuration option

* Fri Jan  6 2023 Dave Dykstra <dwd@fnal.gov> - 1.21-1
- Only show check status on repositories that have it, similar to the
  gc test

* Fri Jan  6 2023 Dave Dykstra <dwd@fnal.gov> - 1.20-1
- Decode the whitelist file data into a string for python3
- Add whitelist testname to comment in api.conf

* Wed Dec 21 2022 Edita Kizinevic <edita.kizinevic@cern.ch> - 1.19-1
- Add monitor of geodb age.
- Add monitor of whitelist expiration.
- Add monitor of cvmfs_server check failures.

* Mon Dec 13 2021 Edita Kizinevic <edita.kizinevic@cern.ch> - 1.18-1
- Add an optional subdirectory to the URL used for reading .cvmfs_status.json.

* Tue Nov  7 2021 Edita Kizinevic <edita.kizinevic@cern.ch> - 1.17-1
- Fix the error message for geo api exceptions to be a string instead
  of a python object (which messed up the json output)

* Thu Sep 30 2021 Edita Kizinevic <edita.kizinevic@cern.ch> - 1.16-1
- Add monitor for stratum 1 geo api.

* Tue Mar 23 2021 Dave Dykstra <dwd@fnal.gov> - 1.15-1
- Support common short timezone abbreviations in .cvmfs_is_snapshotting

* Mon Oct 26 2020 Dave Dykstra <dwd@fnal.gov> - 1.14-2
- Add 'setsebool -P httpd_can_network_connect 1' to %post rules to
  make work with SELinux.

* Tue Oct 20 2020 Dave Dykstra <dwd@fnal.gov> - 1.14-1
- Make compatible with python3, and use it on el8.

* Tue Jul 28 2020 Dave Dykstra <dwd@fnal.gov> - 1.13-1
- Add support for "pass-through" boolean in repositories.json; do not
  monitor the repository if it is set to true.

* Mon May 11 2020 Dave Dykstra <dwd@fnal.gov> - 1.12-1
- Work around bug in cvmfs_server prior to 2.7.3 that caused the 
  last_snapshot status to be deleted when last_gc was updated.

* Thu May 07 2020 Dave Dykstra <dwd@fnal.gov> - 1.11-1
- Add check for long-running initial snapshots.  Multiply the number of
  hours by 9, so by default warnings come in 3 days and critical errors
  in 9 days.  If there's no .cvmfs_is_snapshotting, it is a permanent
  warning.

* Thu Mar 26 2020 Dave Dykstra <dwd@fnal.gov> - 1.10-1
- Catch date parsing errors
- Remove unhelpful exception type from exception messages

* Fri Jul 05 2019 Dave Dykstra <dwd@fnal.gov> - 1.9-1
- Fix thread locking while reading the configuration file; it was
  previously non-functional.

* Fri Apr 20 2018 Dave Dykstra <dwd@fnal.gov> - 1.8-1
- Remove reference to an obsolete variable name in the error message about
  an empty snapshot file.

* Tue Dec 05 2017 Dave Dykstra <dwd@fnal.gov> - 1.7-1
- Restore the behavior of treating missing status files as "Initial 
  snapshot in progress".

* Mon Nov 20 2017 Dave Dykstra <dwd@fnal.gov> - 1.6-1
- Fix bug causing an Internal Server Error when .cvmfs_status.json
  (and .cvmfs_last_snapshot on a stratum 1) is missing.

* Wed Nov 15 2017 Dave Dykstra <dwd@fnal.gov> - 1.5-1
- Add check for garbage collections that haven't been run in a long time
- Add 'limit' option in api.conf to change the default warning and critical
  times for each test
- Check api.conf once every minute and re-read it if it has changed
- Update to modern wsgi configuration
- Use systemctl commands to reload apache on el7

* Fri Nov 03 2017 Dave Dykstra <dwd@fnal.gov> - 1.4-2
- Add %release_prefix macro to support openSUSE Build System

* Sun Sep 11 2016 Dave Dykstra <dwd@fnal.gov> - 1.4-1
- Fix the excluderepo keyword in /etc/cvmfsmon/api.conf

* Wed May 04 2016 Dave Dykstra <dwd@fnal.gov> - 1.3-1
- Convert unicode repository name to string. It was causing the
  "format=list" output to crash on el6.

* Thu Mar 03 2016 Dave Dykstra <dwd@fnal.gov> - 1.2-1
- Prevent empty .cvmfs_last_snapshot files (which can happen when a disk
  fills up) from causing a crash and stack trace.

* Fri Feb 05 2016 Dave Dykstra <dwd@fnal.gov> - 1.1-1
- Change test format name from 'ok' to 'status' as was planned and
  documented in the comments.

* Mon Oct 12 2015 Dave Dykstra <dwd@fnal.gov> - 1.0-1
- Initial release

Summary: CernVM File System Server Monitoring
Name: cvmfs-servermon
Version: 1.12
# The release_prefix macro is used in the OBS prjconf, don't change its name
%define release_prefix 1
Release: %{release_prefix}%{?dist}
BuildArch: noarch
Group: Applications/System
License: BSD
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
Source0: https://github.com/cvmfs/%{name}/archive/%{name}-%{version}.tar.gz

Requires: httpd
Requires: mod_wsgi
Requires: python-anyjson
Requires: python-dateutil

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
/sbin/service httpd status >/dev/null && /sbin/service httpd reload
%else
if systemctl --quiet is-active httpd; then
    systemctl reload httpd
fi
%endif

%files
%dir /etc/cvmfsmon
%config(noreplace) /etc/cvmfsmon/*
%{_sbindir}/*
/etc/httpd/conf.d/*
/var/www/wsgi-scripts/*
/usr/share/cvmfs-servermon

%changelog
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

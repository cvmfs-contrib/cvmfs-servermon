Summary: CernVM File System Server Monitoring
Name: cvmfs-servermon
Version: 1.0
Release: 1%{?dist}
BuildArch: noarch
Group: Applications/System
License: BSD
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
Source0: https://ecsft.cern.ch/dist/cvmfs/%{name}-%{version}.tar.gz

Requires: httpd
Requires: mod_wsgi
Requires: python-anyjson
Requires: python-dateutil

%description
Provides an api for monitoring a cvmfs-server installation or multiple
cvmfs-server installations.

%prep
%setup -q

%install
mkdir -p $RPM_BUILD_ROOT/etc/cvmfsmon
install -p -m 644 etc/* $RPM_BUILD_ROOT/etc/cvmfsmon
mkdir -p $RPM_BUILD_ROOT%{_sbindir}
install -p -m 555 compat/* $RPM_BUILD_ROOT%{_sbindir}
mkdir -p $RPM_BUILD_ROOT/etc/httpd/conf.d
install -p -m 444 misc/cvmfsmon.conf $RPM_BUILD_ROOT/etc/httpd/conf.d
mkdir -p $RPM_BUILD_ROOT/var/www/wsgi-scripts
install -p -m 555 misc/cvmfsmon-api.wsgi $RPM_BUILD_ROOT/var/www/wsgi-scripts
mkdir -p $RPM_BUILD_ROOT/usr/share/cvmfs-servermon/webapi
install -p -m 444 webapi/* $RPM_BUILD_ROOT/usr/share/cvmfs-servermon/webapi

%post
/sbin/service httpd status >/dev/null && /sbin/service httpd reload
:

%files
%dir /etc/cvmfsmon
%config(noreplace) /etc/cvmfsmon/*
%{_sbindir}/*
/etc/httpd/conf.d/*
/var/www/wsgi-scripts/*
/usr/share/cvmfs-servermon

%changelog
* Mon Oct 12 2015 Dave Dykstra <dwd@fnal.gov> - 1.0-1
- Initial release

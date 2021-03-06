################################################################################

# rpmbuilder:relative-pack true

################################################################################

%define  debug_package %{nil}

################################################################################

%define _posixroot        /
%define _root             /root
%define _bin              /bin
%define _sbin             /sbin
%define _srv              /srv
%define _home             /home
%define _opt              /opt
%define _lib32            %{_posixroot}lib
%define _lib64            %{_posixroot}lib64
%define _libdir32         %{_prefix}%{_lib32}
%define _libdir64         %{_prefix}%{_lib64}
%define _logdir           %{_localstatedir}/log
%define _rundir           %{_localstatedir}/run
%define _lockdir          %{_localstatedir}/lock/subsys
%define _cachedir         %{_localstatedir}/cache
%define _spooldir         %{_localstatedir}/spool
%define _crondir          %{_sysconfdir}/cron.d
%define _loc_prefix       %{_prefix}/local
%define _loc_exec_prefix  %{_loc_prefix}
%define _loc_bindir       %{_loc_exec_prefix}/bin
%define _loc_libdir       %{_loc_exec_prefix}/%{_lib}
%define _loc_libdir32     %{_loc_exec_prefix}/%{_lib32}
%define _loc_libdir64     %{_loc_exec_prefix}/%{_lib64}
%define _loc_libexecdir   %{_loc_exec_prefix}/libexec
%define _loc_sbindir      %{_loc_exec_prefix}/sbin
%define _loc_bindir       %{_loc_exec_prefix}/bin
%define _loc_datarootdir  %{_loc_prefix}/share
%define _loc_includedir   %{_loc_prefix}/include
%define _loc_mandir       %{_loc_datarootdir}/man
%define _rpmstatedir      %{_sharedstatedir}/rpm-state
%define _pkgconfigdir     %{_libdir}/pkgconfig

%define __service         %{_sbin}/service
%define __chkconfig       %{_sbin}/chkconfig
%define __sysctl          %{_bindir}/systemctl

################################################################################

%define morpher_user      morpher
%define morpher_group     morpher
%define srcdir            src/github.com/essentialkaos/%{name}

################################################################################

Summary:            pkg.re morpher server
Name:               pkgre
Version:            3.6.0
Release:            0%{?dist}
Group:              Applications/System
License:            EKOL
URL:                https://github.com/essentialkaos/pkgre

Source0:            https://source.kaos.st/pkgre/%{name}-%{version}.tar.bz2

BuildRoot:          %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

BuildRequires:      golang >= 1.10

%if 0%{?rhel} >= 7
Requires:           systemd
%else
Requires:           kaosv >= 2.15
%endif

%if 0%{?rhel} >= 7
Requires(pre):      shadow-utils
Requires(post):     systemd
Requires(preun):    systemd
Requires(postun):   systemd
%else
Requires(pre):      shadow-utils
Requires(post):     chkconfig
Requires(preun):    chkconfig
Requires(preun):    initscripts
Requires(postun):   initscripts
%endif

Provides:           %{name} = %{version}-%{release}

################################################################################

%description
pkg.re service morpher server.

################################################################################

%package librato

Summary:            Tool for sending morpher metrics to Librato
Group:              Applications/System

Requires:           pkgre = %{version}

%description librato
Tool for sending morpher metrics to Librato.

################################################################################

%prep
%setup -q

%build
export GOPATH=$(pwd)

pushd src/github.com/essentialkaos/%{name}
  %{__make} %{?_smp_mflags} all
popd

%install
rm -rf %{buildroot}

install -dm 755 %{buildroot}%{_bindir}
install -dm 755 %{buildroot}%{_sysconfdir}
install -dm 755 %{buildroot}%{_sysconfdir}/cron.d
install -dm 755 %{buildroot}%{_sysconfdir}/logrotate.d
install -dm 755 %{buildroot}%{_logdir}
install -dm 755 %{buildroot}%{_logdir}/%{name}/morpher

install -pm 755 %{srcdir}/morpher-server \
                %{buildroot}%{_bindir}/

install -pm 755 %{srcdir}/morpher-librato \
                %{buildroot}%{_bindir}/

install -pm 644 %{srcdir}/common/morpher.knf \
                %{buildroot}%{_sysconfdir}/

install -pm 644 %{srcdir}/common/morpher-librato.knf \
                %{buildroot}%{_sysconfdir}/

install -pm 644 %{srcdir}/common/morpher-librato.cron \
                %{buildroot}%{_sysconfdir}/cron.d/morpher-librato

%if 0%{?rhel} >= 7
install -dm 755 %{buildroot}%{_unitdir}
install -pm 644 %{srcdir}/common/morpher.service \
                %{buildroot}%{_unitdir}/
%else
install -dm 755 %{buildroot}%{_initddir}
install -pm 755 %{srcdir}/common/morpher.init \
                %{buildroot}%{_initddir}/morpher
%endif

install -pm 755 %{srcdir}/common/morpher.logrotate \
                %{buildroot}%{_sysconfdir}/logrotate.d/morpher

%pre
getent group %{morpher_group} >/dev/null || groupadd -r %{morpher_group}
getent passwd %{morpher_user} >/dev/null || useradd -r -M -g %{morpher_group} -s /sbin/nologin %{morpher_user}
exit 0

%post
if [[ $1 -eq 1 ]] ; then
%if 0%{?rhel} >= 7
  %{__sysctl} enable morpher.service &>/dev/null || :
%else
  %{__chkconfig} --add morpher &>/dev/null || :
  %{__chkconfig} morpher on &>/dev/null || :
%endif
fi

%preun
if [[ $1 -eq 0 ]] ; then
%if 0%{?rhel} >= 7
  %{__sysctl} --no-reload disable morpher.service &>/dev/null || :
  %{__sysctl} stop morpher.service &>/dev/null || :
%else
  %{__service} morpher stop &> /dev/null || :
  %{__chkconfig} --del morpher &> /dev/null || :
%endif
fi

%clean
rm -rf %{buildroot}

################################################################################

%files
%defattr(-,root,root,-)
%doc LICENSE.EN LICENSE.RU
%attr(-,%{morpher_user},%{morpher_group}) %dir %{_logdir}/%{name}/morpher/
%config(noreplace) %{_sysconfdir}/morpher.knf
%config(noreplace) %{_sysconfdir}/logrotate.d/morpher
%{_bindir}/morpher-server
%if 0%{?rhel} <= 6
%{_initrddir}/morpher
%else
%{_unitdir}/morpher.service
%endif

%files librato
%defattr(-,root,root,-)
%doc LICENSE.EN LICENSE.RU
%config(noreplace) %{_sysconfdir}/morpher-librato.knf
%config(noreplace) %{_sysconfdir}/cron.d/morpher-librato
%{_bindir}/morpher-librato

################################################################################

%changelog
* Wed Mar 28 2018 Anton Novojilov <andy@essentialkaos.com> - 3.6.0-0
- fasthttp package replaced by erikdubbelboer fork
- Added files limit to init script and systmed unit
- Added systemd unit
- Added autostart

* Tue Mar 06 2018 Anton Novojilov <andy@essentialkaos.com> - 3.5.0-1
- Rebuilt with Go 1.10
- ek package updated to latest release
- fasthttp package updated to latest release

* Tue Oct 31 2017 Anton Novojilov <andy@essentialkaos.com> - 3.5.0-0
- Proxying request's from GoDoc to GitHub

* Fri Oct 13 2017 Anton Novojilov <andy@essentialkaos.com> - 3.4.0-1
- Improved init script
- Improved spec

* Sun May 21 2017 Anton Novojilov <andy@essentialkaos.com> - 3.4.0-0
- ek package updated to v9
- librato package updated to v7

* Sun Apr 16 2017 Anton Novojilov <andy@essentialkaos.com> - 3.3.0-0
- Morpher now return 404 if can't find proper tag/branch
- Code refactoring
- ek package updated to v8
- librato package updated to v6

* Tue Apr 11 2017 Anton Novojilov <andy@essentialkaos.com> - 3.2.0-0
- Return original symref if target version is tag

* Sun Apr 09 2017 Anton Novojilov <andy@essentialkaos.com> - 3.1.0-0
- Default HTTP client replaced by fasthttp client

* Tue Mar 28 2017 Anton Novojilov <andy@essentialkaos.com> - 3.0.0-0
- ek package updated to v7
- librato package updated to v5
- Improved Makefile

* Wed Feb 22 2017 Anton Novojilov <andy@essentialkaos.com> - 2.1.0-0
- ek package updated to v6
- librato package updated to v4

* Thu Oct 27 2016 Anton Novojilov <andy@essentialkaos.com> - 2.0.0-0
- ek package updated to v5
- Removed Librato monitoring from morpher server
- ek.req replaced by default http client
- net/http HTTP server replaced by valyala/fasthttp
- Added recover to request handler

* Fri Jul 01 2016 Anton Novojilov <andy@essentialkaos.com> - 1.0.2-0
- Fixed compatibility with librato.v2

* Wed Jun 29 2016 Anton Novojilov <andy@essentialkaos.com> - 1.0.1-0
- Fixed bug with updating packages with tags
- Migrated to ek.v2
- Minor improvements

* Fri Mar 18 2016 Anton Novojilov <andy@essentialkaos.com> - 1.0.0-0
- First stable release

* Mon Mar 14 2016 Anton Novojilov <andy@essentialkaos.com> - 0.1.5-0
- Redirect requests from browsers to github

* Mon Mar 14 2016 Anton Novojilov <andy@essentialkaos.com> - 0.1.4-0
- Improved refs processing
- pkg.re usage in source code

* Tue Jan 12 2016 Anton Novojilov <andy@essentialkaos.com> - 0.1.3-0
- Fixed bug for url's without version

* Mon Jan 11 2016 Anton Novojilov <andy@essentialkaos.com> - 0.1.1-0
- Improved error handling

* Sun Nov 02 2014 Anton Novojilov <andy@essentialkaos.com> - 0.1-0
- Initial build

%global debug_package %{nil}
%global gittag master

%if 0%{?rhel} && 0%{?rhel} == 7
%define with_python2 1
%else
%if 0%{?rhel} && 0%{?rhel} > 7
%bcond_with python2
%else
%bcond_without python2
%endif
%bcond_without python3
%endif

Name:		healthcheck
Version:	0.1.0
Release:	1%{?dist}
Summary:	Tool to perform system configuration health checks

License:	ASL2.0
URL:		https://oamg.github.io/healtcheck
Source0:    https://github.com/oamg/leapp-repository/archive/leapp-repository-%{version}.tar.gz

BuildRequires:	python-devel
Requires:	    python-setuptools
Requires:       python-six
Requires:       python2-leapp

%description


%prep
%autosetup


%build

cd sources/health-check

install -m 0755 -d %{buildroot}%{_mandir}/man1
install -m 0644 -p man/healthcheck.1 %{buildroot}%{_mandir}/man1/

%if %{with python2}
%py2_build
%endif

%if %{with python3}
%py3_build
%endif

%install

%if %{with python2}
%py2_install
%endif

%if %{with python3}
%py3_install
%endif



%files
%doc sources/healthcheck/README.md
%license COPYING
%{_mandir}/man1/healthcheck.1*
%{_bindir}/healthcheck



%changelog
* Mon Mar 25 2019 Vinzenz Feenstra <evilissimo@gmail.com> - %{version}-%{release}
- Initial rpm

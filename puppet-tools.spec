Name:         puppet-tools
Version:      0.1.1
Release:      1
Summary:      Puppet tools
Group:        Applications/System
License:      GPL
Vendor:       MSAT
Source:       %{name}.tar.gz
BuildRoot:    %{_tmppath}/%{name}-root
Requires:     PyYAML

%description

%prep
%setup -q -n %{name}

%build
# Empty.

%install
rm -rf $RPM_BUILD_ROOT
mkdir $RPM_BUILD_ROOT
cp -R usr $RPM_BUILD_ROOT

%clean
rm -rf $RPM_BUILD_ROOT

%pre
# Empty.

%post
# Empty.

%preun
# Empty.

%postun
# Empty.

%files
%defattr(0644,root,root)
%attr(0755,root,root) /usr/bin/mk_cobbler.py
%attr(0755,root,root) /usr/bin/mk_zones_from_yaml.py
%doc /usr/share/doc/%{name}

%changelog
* Sun Aug 10 2014 Allard Berends <allard.berends@example.com> - 0.1.1-1
- Initial creation of the RPM

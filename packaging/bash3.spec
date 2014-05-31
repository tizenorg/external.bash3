Version: 3.2.0
Name: bash3
Summary: The GNU Bourne Again shell
Release: 1
VCS:     external/bash#bash_4.1-slp2+s3_1-3-g35a92deccc2ab499763d1656732b42d8c433f659
Group: System/Shells
License: GPLv2+
Url: http://www.gnu.org/software/bash
Source0: ftp://ftp.gnu.org/gnu/bash/%{name}-%{version}.tar.gz
Source1001:    %{name}.manifest
Provides: bash

BuildRequires: bison
BuildRequires: autoconf

%description
The GNU Bourne Again shell (Bash) is a shell or command language
interpreter that is compatible with the Bourne shell (sh). Bash
incorporates useful features from the Korn shell (ksh) and the C shell
(csh). Most sh scripts can be run by bash without modification.

%package doc
Summary: Documentation files for %{name}
Group: Development/Languages
Requires: %{name} = %{version}-%{release}

%description doc
This package contains documentation files for %{name}.

%define pkgdocdir %{_datadir}/doc/%{name}-%{version}

%prep
%setup -q

%build
cp %{SOURCE1001} .
autoconf
%configure \
	--enable-largefile \
	--without-bash-malloc \
	--disable-nls

# Recycles pids is neccessary. When bash's last fork's pid was X
# and new fork's pid is also X, bash has to wait for this same pid.
# Without Recycles pids bash will not wait.
make "CPPFLAGS=-D_GNU_SOURCE -DRECYCLES_PIDS `getconf LFS_CFLAGS`"
%check
make check

%install
rm -rf $RPM_BUILD_ROOT

if [ -e autoconf ]; then
  # Yuck. We're using autoconf 2.1x.
  export PATH=.:$PATH
fi

# Fix bug #83776
perl -pi -e 's,bashref\.info,bash.info,' doc/bashref.info

make DESTDIR=$RPM_BUILD_ROOT install

mkdir -p $RPM_BUILD_ROOT/etc

# make manpages for bash builtins as per suggestion in DOC/README
pushd doc
sed -e '
/^\.SH NAME/, /\\- bash built-in commands, see \\fBbash\\fR(1)$/{
/^\.SH NAME/d
s/^bash, //
s/\\- bash built-in commands, see \\fBbash\\fR(1)$//
s/,//g
b
}
d
' builtins.1 > man.pages
for i in echo pwd test kill; do
  perl -pi -e "s,$i,,g" man.pages
  perl -pi -e "s,  , ,g" man.pages
done

install -c -m 644 builtins.1 ${RPM_BUILD_ROOT}%{_mandir}/man1/builtins.1

for i in `cat man.pages` ; do
  echo .so man1/builtins.1 > ${RPM_BUILD_ROOT}%{_mandir}/man1/$i.1
  chmod 0644 ${RPM_BUILD_ROOT}%{_mandir}/man1/$i.1
done
popd

# Link bash man page to sh so that man sh works.
ln -s bash.1 ${RPM_BUILD_ROOT}%{_mandir}/man1/sh.1

# Not for printf, true and false (conflict with coreutils)
rm -f $RPM_BUILD_ROOT/%{_mandir}/man1/printf.1
rm -f $RPM_BUILD_ROOT/%{_mandir}/man1/true.1
rm -f $RPM_BUILD_ROOT/%{_mandir}/man1/false.1

pushd $RPM_BUILD_ROOT
mkdir ./bin
mv ./usr/bin/bash ./bin
ln -sf bash ./bin/sh
rm -f .%{_infodir}/dir
popd
mkdir -p $RPM_BUILD_ROOT/etc/skel
#install -c -m644 %SOURCE1 $RPM_BUILD_ROOT/etc/skel/.bashrc
#install -c -m644 %SOURCE2 $RPM_BUILD_ROOT/etc/skel/.bash_profile
#install -c -m644 %SOURCE3 $RPM_BUILD_ROOT/etc/skel/.bash_logout
LONG_BIT=$(getconf LONG_BIT)
mv $RPM_BUILD_ROOT%{_bindir}/bashbug \
   $RPM_BUILD_ROOT%{_bindir}/bashbug-"${LONG_BIT}"

# Fix missing sh-bangs in example scripts (bug #225609).
for script in \
  examples/scripts/krand.bash \
  examples/scripts/bcsh.sh \
  examples/scripts/precedence \
  examples/scripts/shprompt
do
  cp "$script" "$script"-orig
  echo '#!/bin/bash' > "$script"
  cat "$script"-orig >> "$script"
  rm -f "$script"-orig
done

rm -rf %{buildroot}%{_bindir}/bashbug-*
chmod a-x doc/*.sh

mkdir -p $RPM_BUILD_ROOT%{_datadir}/license
for keyword in LICENSE COPYING COPYRIGHT;
do
	for file in `find %{_builddir} -name $keyword`;
	do
		cat $file >> $RPM_BUILD_ROOT%{_datadir}/license/%{name};
		echo "";
	done;
done

%clean
rm -rf $RPM_BUILD_ROOT

# ***** bash doesn't use install-info. It's always listed in %{_infodir}/dir
# to prevent prereq loops

# post is in lua so that we can run it without any external deps.  Helps
# for bootstrapping a new install.
# Jesse Keating 2009-01-29 (code from Ignacio Vazquez-Abrams)
%post -p <lua>
bashfound = false;
shfound = false;

f = io.open("/etc/shells", "r");
if f == nil
then
  f = io.open("/etc/shells", "w");
else
  repeat
    t = f:read();
    if t == "/bin/bash"
    then
      bashfound = true;
    end
    if t == "/bin/sh"
    then
      shfound = true;
    end
  until t == nil;
end
f:close()

f = io.open("/etc/shells", "a");
if not bashfound
then
  f:write("/bin/bash\n")
end
if not shfound
then
  f:write("/bin/sh\n")
end
f:close()

%postun
if [ "$1" = 0 ]; then
    /bin/grep -v '^/bin/bash$' < /etc/shells | \
      /bin/grep -v '^/bin/sh$' > /etc/shells.new
    /bin/mv /etc/shells.new /etc/shells
fi


%docs_package

%files
%manifest %{name}.manifest
%{_datadir}/license/%{name}
/bin/sh
/bin/bash

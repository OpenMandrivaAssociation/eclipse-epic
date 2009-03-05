%define eclipse_base     %{_libdir}/eclipse
%define gcj_support      0

Name:      eclipse-epic
Version:   0.6.31
Release:   %mkrel 0.1.0
Summary:   Perl Eclipse plugin
Group:     Development/Java
License:   CPL
URL:       http://e-p-i-c.sourceforge.net/

# source tarball and the script used to generate it from upstream's cvs
# script usage:
# $ sh get-epic.sh
Source0:   epic-%{version}.tar.gz
Source1:   get-epic.sh

BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root

%if %{gcj_support}
BuildRequires:    java-gcj-compat-devel
%else
BuildArch:        noarch
%endif
BuildRequires:    java-rpmbuild
BuildRequires:    jpackage-utils
BuildRequires:    eclipse-pde
BuildRequires:    antlr
BuildRequires:    jdom
BuildRequires:    gnu-regexp
BuildRequires:    brazil
BuildRequires:    zip
Requires:         java >= 1.6
Requires:         jpackage-utils
Requires:         eclipse-platform >= 3.4
Requires:         antlr
Requires:         jdom
Requires:         gnu-regexp
Requires:         brazil
Requires:         perl
Requires:         perl-PadWalker

%description
EPIC is an open source Perl IDE based on the Eclipse platform. Features
supported are syntax highlighting, on-the-fly syntax check, content assist,
perldoc support, source formatter, templating support, a regular expression
view and a Perl debugger.

%prep
%setup -q -n epic-%{version}

# ditch bundled libs in favor of building against fedora packaged libs
rm org.epic.lib/lib/jdom-1.1.jar \
   org.epic.lib/lib/antlr-2.7.5.jar \
   org.epic.lib/lib/brazil_mini.jar \
   org.epic.lib/lib/gnu-regexp-1.1.4.jar
build-jar-repository -s -p org.epic.lib/lib jdom antlr gnu-regexp brazil

grep -lR jdom-1.1 *         | xargs sed --in-place "s/jdom-1.1/jdom/"
grep -lR antlr-2.7.5 *      | xargs sed --in-place "s/antlr-2.7.5/antlr/"
grep -lR gnu-regexp-1.1.4 * | xargs sed --in-place "s/gnu-regexp-1.1.4/gnu-regexp/"
grep -lR brazil_mini *      | xargs sed --in-place "s/brazil_mini/brazil/"

# put the source plugin together
for p in org.epic.perleditor \
         org.epic.regexp \
         org.epic.debug; do
  mkdir org.epic.source/src/$p
  pushd $p/src
  zip -r -q ../../org.epic.source/src/$p/src.zip *
  popd
done

# make sure upstream hasn't sneaked in any jars we don't know about
JARS=""
for j in `find -name "*.jar"`; do
  if [ ! -L $j ]; then
    JARS="$JARS $j"
  fi
done
if [ ! -z "$JARS" ]; then
   echo "These jars should be deleted and symlinked to system jars: $JARS"
   exit 1
fi

%build
# parse grammar for grammar parser
pushd org.epic.perleditor/src/org/epic/core/parser/
for g in `find . -name "*.g"`; do
  antlr $g
done
popd

# build the main feature
%{eclipse_base}/buildscripts/pdebuild -f org.epic.feature.main \
  -a "-DjavacTarget=1.4 -DjavacSource=1.4"

%install
rm -rf %{buildroot}
installDir=%{buildroot}%{_datadir}/eclipse/dropins/epic
install -d -m 755 $installDir
unzip -q -d $installDir build/rpmBuild/org.epic.feature.main.zip

# need to recreate the symlinks to libraries that were setup in "prep"
# because for some reason the ant copy task doesn't preserve them
pushd $installDir/eclipse/plugins/org.epic.lib_*/lib
rm *.jar
build-jar-repository -s -p . jdom antlr gnu-regexp brazil
popd

# ensure source packages are correctly verisoned
pushd $installDir/eclipse/plugins
for p in org.epic.perleditor \
         org.epic.regexp \
         org.epic.debug; do
  PVERSION=_`ls -1 | grep $p | sed -r 's/.*_(.*)\.jar$/\1/'`
  mv org.epic.source_%{version}/src/$p org.epic.source_%{version}/src/$p$PVERSION
done
popd

%{gcj_compile}

%clean
rm -rf %{buildroot}

%if %{gcj_support}
%post
%{update_gcjdb}
%postun
%{clean_gcjdb}
%endif

%files
%defattr(-,root,root,-)
%doc org.epic.feature.main/license.html
%{_datadir}/eclipse/dropins/epic
%{gcj_files}

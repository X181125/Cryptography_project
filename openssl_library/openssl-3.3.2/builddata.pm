package OpenSSL::safe::installdata;

use strict;
use warnings;
use Exporter;
our @ISA = qw(Exporter);
our @EXPORT = qw(
    @PREFIX
    @libdir
    @BINDIR @BINDIR_REL_PREFIX
    @LIBDIR @LIBDIR_REL_PREFIX
    @INCLUDEDIR @INCLUDEDIR_REL_PREFIX
    @APPLINKDIR @APPLINKDIR_REL_PREFIX
    @ENGINESDIR @ENGINESDIR_REL_LIBDIR
    @MODULESDIR @MODULESDIR_REL_LIBDIR
    @PKGCONFIGDIR @PKGCONFIGDIR_REL_LIBDIR
    @CMAKECONFIGDIR @CMAKECONFIGDIR_REL_LIBDIR
    $VERSION @LDLIBS
);

our @PREFIX                     = ( 'D:\Visual_Studio_Code_Workspace\ThucHanhMatMaHoc\Lab4\openssl-3.3.2' );
our @libdir                     = ( 'D:\Visual_Studio_Code_Workspace\ThucHanhMatMaHoc\Lab4\openssl-3.3.2' );
our @BINDIR                     = ( 'D:\Visual_Studio_Code_Workspace\ThucHanhMatMaHoc\Lab4\openssl-3.3.2\apps' );
our @BINDIR_REL_PREFIX          = ( 'apps' );
our @LIBDIR                     = ( 'D:\Visual_Studio_Code_Workspace\ThucHanhMatMaHoc\Lab4\openssl-3.3.2' );
our @LIBDIR_REL_PREFIX          = ( '' );
our @INCLUDEDIR                 = ( 'D:\Visual_Studio_Code_Workspace\ThucHanhMatMaHoc\Lab4\openssl-3.3.2\include', 'D:\Visual_Studio_Code_Workspace\ThucHanhMatMaHoc\Lab4\openssl-3.3.2\include' );
our @INCLUDEDIR_REL_PREFIX      = ( 'include', './include' );
our @APPLINKDIR                 = ( 'D:\Visual_Studio_Code_Workspace\ThucHanhMatMaHoc\Lab4\openssl-3.3.2\ms' );
our @APPLINKDIR_REL_PREFIX      = ( 'ms' );
our @ENGINESDIR                 = ( 'D:\Visual_Studio_Code_Workspace\ThucHanhMatMaHoc\Lab4\openssl-3.3.2\engines' );
our @ENGINESDIR_REL_LIBDIR      = ( 'engines' );
our @MODULESDIR                 = ( 'D:\Visual_Studio_Code_Workspace\ThucHanhMatMaHoc\Lab4\openssl-3.3.2\providers' );
our @MODULESDIR_REL_LIBDIR      = ( 'providers' );
our @PKGCONFIGDIR               = ( 'D:\Visual_Studio_Code_Workspace\ThucHanhMatMaHoc\Lab4\openssl-3.3.2' );
our @PKGCONFIGDIR_REL_LIBDIR    = ( '.' );
our @CMAKECONFIGDIR             = ( 'D:\Visual_Studio_Code_Workspace\ThucHanhMatMaHoc\Lab4\openssl-3.3.2' );
our @CMAKECONFIGDIR_REL_LIBDIR  = ( '.' );
our $VERSION                    = '3.3.2';
our @LDLIBS                     =
    # Unix and Windows use space separation, VMS uses comma separation
    $^O eq 'VMS'
    ? split(/ *, */, 'ws2_32.lib gdi32.lib advapi32.lib crypt32.lib user32.lib ')
    : split(/ +/, 'ws2_32.lib gdi32.lib advapi32.lib crypt32.lib user32.lib ');

1;

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

our @PREFIX                     = ( 'D:\VISUAL_STUDIO_CODE_WORKSPACE\ThucHanhMatMaHoc\Lab4' );
our @libdir                     = ( 'D:\VISUAL_STUDIO_CODE_WORKSPACE\ThucHanhMatMaHoc\Lab4\lib' );
our @BINDIR                     = ( 'D:\VISUAL_STUDIO_CODE_WORKSPACE\ThucHanhMatMaHoc\Lab4\bin' );
our @BINDIR_REL_PREFIX          = ( 'bin' );
our @LIBDIR                     = ( 'D:\VISUAL_STUDIO_CODE_WORKSPACE\ThucHanhMatMaHoc\Lab4\lib' );
our @LIBDIR_REL_PREFIX          = ( 'lib' );
our @INCLUDEDIR                 = ( 'D:\VISUAL_STUDIO_CODE_WORKSPACE\ThucHanhMatMaHoc\Lab4\include' );
our @INCLUDEDIR_REL_PREFIX      = ( 'include' );
our @APPLINKDIR                 = ( 'D:\VISUAL_STUDIO_CODE_WORKSPACE\ThucHanhMatMaHoc\Lab4\include\openssl' );
our @APPLINKDIR_REL_PREFIX      = ( 'include/openssl' );
our @ENGINESDIR                 = ( 'D:\VISUAL_STUDIO_CODE_WORKSPACE\ThucHanhMatMaHoc\Lab4\lib\engines-3' );
our @ENGINESDIR_REL_LIBDIR      = ( 'engines-3' );
our @MODULESDIR                 = ( 'D:\VISUAL_STUDIO_CODE_WORKSPACE\ThucHanhMatMaHoc\Lab4\lib\ossl-modules' );
our @MODULESDIR_REL_LIBDIR      = ( 'ossl-modules' );
our @PKGCONFIGDIR               = ( 'D:\VISUAL_STUDIO_CODE_WORKSPACE\ThucHanhMatMaHoc\Lab4\lib' );
our @PKGCONFIGDIR_REL_LIBDIR    = ( '' );
our @CMAKECONFIGDIR             = ( 'D:\VISUAL_STUDIO_CODE_WORKSPACE\ThucHanhMatMaHoc\Lab4\lib\cmake\OpenSSL' );
our @CMAKECONFIGDIR_REL_LIBDIR  = ( 'cmake\OpenSSL' );
our $VERSION                    = '3.3.2';
our @LDLIBS                     =
    # Unix and Windows use space separation, VMS uses comma separation
    $^O eq 'VMS'
    ? split(/ *, */, 'ws2_32.lib gdi32.lib advapi32.lib crypt32.lib user32.lib ')
    : split(/ +/, 'ws2_32.lib gdi32.lib advapi32.lib crypt32.lib user32.lib ');

1;

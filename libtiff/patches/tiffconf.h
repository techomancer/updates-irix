/*
  Configuration defines for installed libtiff on IRIX 6.5 (MIPSpro).
*/

#ifndef _TIFFCONF_
#define _TIFFCONF_

/* 64-bit integer types */
#define TIFF_INT64_T signed long long
#define TIFF_UINT64_T unsigned long long

#define SIZEOF_INT 4

#if defined(_MIPS_SZLONG) && _MIPS_SZLONG == 64
#define SIZEOF_LONG 8
#else
#define SIZEOF_LONG 4
#endif

#define HAVE_IEEEFP 1

/* Native cpu byte order: 1 if big-endian (Motorola/MIPS) or 0 if little-endian
   (Intel) */
#define HOST_FILLORDER FILLORDER_MSB2LSB
#define HOST_BIGENDIAN 1
#define WORDS_BIGENDIAN 1

/* Codec and format support matching IRIX 6.5.22m */
#define CCITT_SUPPORT 1
#define JPEG_SUPPORT 1
#define LOGLUV_SUPPORT 1
#define LZW_SUPPORT 1
#define NEXT_SUPPORT 1
#define PACKBITS_SUPPORT 1
#define THUNDER_SUPPORT 1
#define STRIPCHOP_DEFAULT 1
#define SUBIFD_SUPPORT 1
#define DEFAULT_EXTRASAMPLE_AS_ALPHA 1
#define CHECK_JPEG_YCBCR_SUBSAMPLING 1

/* Feature support definitions */
#define COLORIMETRY_SUPPORT
#define YCBCR_SUPPORT
#define CMYK_SUPPORT
#define ICC_SUPPORT
#define PHOTOSHOP_SUPPORT

#endif /* _TIFFCONF_ */

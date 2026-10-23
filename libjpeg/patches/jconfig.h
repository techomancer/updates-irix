/* jconfig.h for IRIX 6.5 */
#ifndef JCONFIG_H
#define JCONFIG_H

/* Version ID for the JPEG library: SGI IRIX 6.5.22m ABI is 61 (6a) */
#define JPEG_LIB_VERSION  61

/* libjpeg-turbo version */
#define LIBJPEG_TURBO_VERSION  "2.1.5.1"
#define LIBJPEG_TURBO_VERSION_NUMBER  2001005

/* Support arithmetic encoding & decoding */
#define C_ARITH_CODING_SUPPORTED 1
#define D_ARITH_CODING_SUPPORTED 1

/* Support in-memory source/destination managers */
#define MEM_SRCDST_SUPPORTED 1

/* Plain C implementation without MIPS DSPr2/MSA SIMD */
#undef WITH_SIMD

/* Data precision */
#define BITS_IN_JSAMPLE  8

#undef RIGHT_SHIFT_IS_UNSIGNED

#define HAVE_PROTOTYPES 1
#define HAVE_UNSIGNED_CHAR 1
#define HAVE_UNSIGNED_SHORT 1
#define CHAR_IS_UNSIGNED 1
#define HAVE_STDDEF_H 1
#define HAVE_STDLIB_H 1
#undef NEED_BSD_STRINGS
#undef NEED_SYS_TYPES_H
#undef NEED_FAR_POINTERS
#undef NEED_SHORT_EXTERNAL_NAMES
#undef INCOMPLETE_TYPES_BROKEN

/* SGI ICC profile support */
#define ICC_SUPPORT 1

#include <stddef.h>
#ifndef SIZE_MAX
#define SIZE_MAX  ((size_t)-1)
#endif

#endif /* JCONFIG_H */

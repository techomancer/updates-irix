/* jconfigint.h for IRIX 6.5 */
#ifndef JCONFIGINT_H
#define JCONFIGINT_H

#define BUILD  "20261020"

#undef inline
#define INLINE  __inline

#define THREAD_LOCAL

#define PACKAGE_NAME  "libjpeg-turbo"
#define VERSION  "2.1.5.1"

#if defined(_MIPS_SZLONG) && _MIPS_SZLONG == 64
#define SIZEOF_SIZE_T  8
#else
#define SIZEOF_SIZE_T  4
#endif

#undef HAVE_BUILTIN_CTZL
#undef HAVE_INTRIN_H

#define FALLTHROUGH

#endif /* JCONFIGINT_H */

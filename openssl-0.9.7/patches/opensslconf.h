/* crypto/opensslconf.h */
/* Multi-ABI opensslconf.h for IRIX 6.5.22m (o32, n32, n64) */

#ifndef OPENSSL_DOING_MAKEDEPEND

#ifndef OPENSSL_NO_IDEA
# define OPENSSL_NO_IDEA
#endif
#ifndef OPENSSL_NO_RC5
# define OPENSSL_NO_RC5
#endif
#ifndef OPENSSL_NO_MDC2
# define OPENSSL_NO_MDC2
#endif
#ifndef OPENSSL_NO_ENGINE
# define OPENSSL_NO_ENGINE
#endif
#ifndef OPENSSL_NO_KRB5
# define OPENSSL_NO_KRB5
#endif

#endif /* OPENSSL_DOING_MAKEDEPEND */

#ifndef OPENSSL_THREADS
# define OPENSSL_THREADS
#endif

#ifdef OPENSSL_ALGORITHM_DEFINES
# if defined(OPENSSL_NO_IDEA) && !defined(NO_IDEA)
#  define NO_IDEA
# endif
# if defined(OPENSSL_NO_RC5) && !defined(NO_RC5)
#  define NO_RC5
# endif
# if defined(OPENSSL_NO_MDC2) && !defined(NO_MDC2)
#  define NO_MDC2
# endif
# if defined(OPENSSL_NO_ENGINE) && !defined(NO_ENGINE)
#  define NO_ENGINE
# endif
# if defined(OPENSSL_NO_KRB5) && !defined(NO_KRB5)
#  define NO_KRB5
# endif
#endif

#undef I386_ONLY

#if !(defined(VMS) || defined(__VMS))
# if defined(HEADER_CRYPTLIB_H) && !defined(OPENSSLDIR)
#  define OPENSSLDIR "/usr/openssl"
# endif
#endif

#undef OPENSSL_UNISTD
#define OPENSSL_UNISTD <unistd.h>

#undef OPENSSL_EXPORT_VAR_AS_FUNCTION

#if defined(HEADER_IDEA_H) && !defined(IDEA_INT)
# define IDEA_INT unsigned int
#endif

#if defined(HEADER_MD2_H) && !defined(MD2_INT)
# define MD2_INT unsigned int
#endif

#if defined(HEADER_RC2_H) && !defined(RC2_INT)
# define RC2_INT unsigned int
#endif

#if defined(HEADER_RC4_H)
# if !defined(RC4_INT)
#  define RC4_INT unsigned int
# endif
#endif

#if (defined(HEADER_NEW_DES_H) || defined(HEADER_DES_H)) && !defined(DES_LONG)
# ifndef DES_LONG
#  define DES_LONG unsigned long
# endif
#endif

#if defined(HEADER_BN_H) && !defined(CONFIG_HEADER_BN_H)
# define CONFIG_HEADER_BN_H

# if defined(_MIPS_SZLONG) && _MIPS_SZLONG == 64
/* 64-bit ABI (n64) */
#  undef BN_LLONG
#  define SIXTY_FOUR_BIT_LONG
#  undef SIXTY_FOUR_BIT
#  undef THIRTY_TWO_BIT
#  define BN_DIV3W

# elif defined(_MIPS_SIM) && _MIPS_SIM == _ABIN32
/* N32 ABI */
#  undef BN_LLONG
#  undef SIXTY_FOUR_BIT_LONG
#  define SIXTY_FOUR_BIT
#  undef THIRTY_TWO_BIT
#  define BN_DIV3W

# else
/* O32 ABI */
#  define BN_LLONG
#  undef SIXTY_FOUR_BIT_LONG
#  undef SIXTY_FOUR_BIT
#  define THIRTY_TWO_BIT
#  undef BN_DIV3W
# endif

#endif

#if defined(HEADER_RC4_LOCL_H) && !defined(CONFIG_HEADER_RC4_LOCL_H)
# define CONFIG_HEADER_RC4_LOCL_H

# if defined(_MIPS_SZLONG) && _MIPS_SZLONG == 64
#  define RC4_CHUNK unsigned long
# elif defined(_MIPS_SIM) && _MIPS_SIM == _ABIN32
#  define RC4_CHUNK unsigned long long
# else
#  undef RC4_CHUNK
# endif

# undef RC4_INDEX
#endif

#if defined(HEADER_BF_LOCL_H) && !defined(CONFIG_HEADER_BF_LOCL_H)
# define CONFIG_HEADER_BF_LOCL_H
# define BF_PTR
#endif

#if defined(HEADER_DES_LOCL_H) && !defined(CONFIG_HEADER_DES_LOCL_H)
# define CONFIG_HEADER_DES_LOCL_H
# define DES_PTR
# define DES_RISC2
# define DES_UNROLL
#endif

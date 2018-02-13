/*
 * Definitions etc. for regexp(3) routines.
 *
 * Caveat:  this is V8 regexp(3) [actually, a reimplementation thereof],
 * not the System V one.
 */
#include <stdint.h>
#define NSUBEXP  10
typedef struct regexp {
	char *startp[NSUBEXP];
	char *endp[NSUBEXP];
	char regstart;		/* Internal use only. */
	char reganch;		/* Internal use only. */
	char *regmust;		/* Internal use only. */
	int regmlen;		/* Internal use only. */
	char program[1];	/* Unwarranted chumminess with compiler. */
} regexp;

typedef struct {
	uint16_t location;
	uint8_t op;
	uint16_t offset;

	// @HACK: This could be a union, but because of the way i free the str we
	// can't right now
	uint16_t cmd;
	char* str;
} regpart;

extern regexp *regcomp(const char *re);
extern int regexec(regexp *rp, const char *s);
extern void regsub(const regexp *rp, const char *src, char *dst);
extern void regerror(char *message);
extern char* regchk(char* prog);
extern char *regnext(char *node);

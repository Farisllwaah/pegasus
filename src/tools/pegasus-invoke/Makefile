#
# Makefile 
#
INSTALL	= install	# use /usr/ucb/install on Solaris
RM	= rm -f
CC	= gcc
LD	= $(CC)
SYSTEM  = $(shell uname -s | tr '[a-z]' '[A-Z]' | tr -d '_ -/')
VERSION = $(shell uname -r)
MARCH   = $(shell uname -m | tr '[A-Z]' '[a-z]')
MAJOR   = $(firstword $(subst ., ,$(VERSION)))
MINOR   = $(strip $(word 2,$(subst ., ,$(VERSION))))

ifndef ${prefix}
prefix = $(PEGASUS_HOME)
endif

ifndef ${datadir}
datadir = $(prefix)/share 
endif

NROFF   = groff -mandoc
TEXT    = -Tutf8
HTML    = -Thtml

ifeq (SUNOS,${SYSTEM})
ifeq (5,${MAJOR})
# use these for the SUN CC compiler
CC	= cc
LD	= $(CC)
## SPARCv7
V7FLAGS	= -xtarget=generic
V9FLAGS	= -xtarget=ultra -xarch=v9
CFLAGV7FLAGS = -xtarget=generic
V9FLAGS = -xtarget=ultra -xarch=v9
CFLAGS  = -dalign -ftrap=%none -fsimple -xlibmil $(EXTRACFLAGS)
#EXTRACFLAGS = $(V7FLAGS)
CFLAGS := -DSOLARIS $(CFLAGS) -xO4 -D__EXTENSIONS__=1
LOADLIBES += -lnsl -lsocket
INSTALL = /usr/ucb/install
else
# old Solaris 1 not supported!
endif
endif

ifeq (IRIX64,${SYSTEM})
# The regular 64bit Irix stuff is just too slow, use n32!
SYSTEM        := IRIX
endif

ifeq (IRIX,${SYSTEM})
CC      = cc -n32 -mips3 -r4000
LD      = $(CC)
OPT_NORM = -O3 -IPA -LNO:opt=1
endif

ifeq (AIX,${SYSTEM})
CXX     = xlC_r
CC      = xlc_r
endif

ifeq (LINUX,${SYSTEM})
ifeq (ia64,${MARCH})
CFLAGS  = -Wall -O2 -ggdb
else
ifeq (x86_64,${MARCH})
CFLAGS  = -Wall -O2 -ggdb -m64
else
ifeq (armv7l,${MARCH})
CFLAGS	= -Wall -02 -ggdb
else
CFLAGS  = -Wall -O2 -march=i686 -ggdb
#EXTRA_LDFLAGS += -static
endif
endif
endif
#CFLAGS += -D__USE_POSIX=199309
endif

#
# === [3] ======================================================= rules section
# There is no need to change things below this line.
CFLAGS += -D${SYSTEM} -DMAJOR=${MAJOR} -DMINOR=${MINOR}
#CFLAGS += -D_POSIX_C_SOURCE=199506 -D__USE_XOPEN_EXTENDED
GENDOC = pegasus-invoke.html pegasus-invoke.txt pegasus-invoke.ps

%.html : %.1 ;
	$(NROFF) $(HTML) $< > $@
%.ps : %.1 ;
	$(NROFF) $< > $@
%.txt : %.1 ;
	$(NROFF) $(TEXT) $< > $@
%.o : %.c
	$(CC) $(CFLAGS) $< -c -o $@

all : pegasus-invoke $(GENDOC)

pegasus-invoke: pegasus-invoke.o main.o
	$(LD) $(LDFLAGS) $(CFLAGS) $(OBJS) $^ -o $@ $(LOADLIBES)

pegasus-invoke.o: pegasus-invoke.c pegasus-invoke.h
main.o: main.c

$(GENDOC): pegasus-invoke.1

install: pegasus-invoke
	$(INSTALL) -m 0755 pegasus-invoke $(prefix)/bin

install.doc: $(GENDOC)
	$(INSTALL) -m 0644 $(GENDOC) $(datadir)/man

install.man: pegasus-invoke.1
	$(INSTALL) -m 0644 pegasus-invoke.1 $(datadir)/man/man1

install.all: install install.man install.doc

doc : $(GENDOC)

clean:
	$(RM) *.o $(GENDOC) core core.*

distclean: clean
	$(RM) pegasus-invoke
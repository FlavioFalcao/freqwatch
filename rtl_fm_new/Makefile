all: rtl_fm

rtl_fm: rtl_fm.c convenience/convenience.c
	gcc -lpthread -l rtlsdr -lm -lmysqlclient -o rtl_fm rtl_fm.c convenience/convenience.c

clean:
	rm rtl_fm


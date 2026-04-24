LATEXMK := latexmk
MAIN := main.tex
PDF := $(MAIN:.tex=.pdf)

.PHONY: all clean distclean

all:
	$(LATEXMK) -pdf $(MAIN)

clean:
	$(LATEXMK) -c $(MAIN)

distclean:
	$(LATEXMK) -C $(MAIN)
	rm -f $(PDF)

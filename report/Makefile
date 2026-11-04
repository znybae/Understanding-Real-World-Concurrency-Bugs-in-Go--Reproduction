# Build the report PDF: run `make` inside report/
MAIN = main

all: $(MAIN).pdf

$(MAIN).pdf: $(MAIN).tex sections/*.tex references.bib
	latexmk -pdf -interaction=nonstopmode $(MAIN).tex

clean:
	latexmk -C

.PHONY: all clean

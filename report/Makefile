MAIN = main
WEEK3 = results/week3_full_suite/run-20261116T150500Z-ixxI8j
PYTHON ?= $(if $(wildcard ../.venv/bin/python),../.venv/bin/python,python3)

all: figures $(MAIN).pdf

figures:
	$(PYTHON) ../analysis/plot_reproduction.py $(WEEK3)/summary.tsv
	$(PYTHON) ../analysis/plot_race_detection.py $(WEEK3)/race_warning_counts.tsv
	$(PYTHON) ../analysis/plot_shared_memory.py data/test_record.csv

plot-env:
	python3 -m venv ../.venv
	../.venv/bin/python -m pip install -r ../analysis/requirements.txt

$(MAIN).pdf: $(MAIN).tex sections/*.tex tables/*.tex references.bib figures/*.pdf
	@if command -v latexmk >/dev/null 2>&1; then \
		latexmk -pdf -interaction=nonstopmode $(MAIN).tex; \
	elif command -v tectonic >/dev/null 2>&1; then \
		tectonic $(MAIN).tex --keep-logs; \
	else \
		echo "Install latexmk or Tectonic to build the report." >&2; exit 1; \
	fi

clean:
	@if command -v latexmk >/dev/null 2>&1; then latexmk -C; fi
	rm -f $(MAIN).aux $(MAIN).bbl $(MAIN).blg $(MAIN).log $(MAIN).out $(MAIN).toc $(MAIN).pdf

.PHONY: all figures plot-env clean

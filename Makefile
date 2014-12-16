all: gen tex

gen:
	./generate.py

tex:
	pdflatex booklet_sat && pdflatex booklet_sun

booklet: all
	pdfbook booklet_sat.pdf && pdfbook booklet_sun.pdf

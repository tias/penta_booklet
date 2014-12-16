all: gen tex

gen:
	./generate.py

tex:
	pdflatex booklet_sat && pdflatex booklet_sun

booklet: all
	pdfbook booklet_sat.pdf && pdfbook booklet_sun.pdf

gen_2015:
	./generate.py xml.2015

2015: gen_2015 tex

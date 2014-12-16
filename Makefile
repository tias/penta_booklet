all: gen tex

gen:
	./generate.py

tex:
	pdflatex booklet_sat && pdflatex booklet_sun

booklet:
	pdfbook booklet_sat.pdf && pdfbook booklet_sun.pdf

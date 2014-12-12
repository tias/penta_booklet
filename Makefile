all: gen tex

gen:
	./generate.py

tex:
	pdflatex booklet_sat && pdflatex booklet_sun

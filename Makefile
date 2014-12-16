all: gen tex

gen:
	./generate.py

tex:
	pdflatex booklet_sat && pdflatex booklet_sun

booklet: all
	pdfbook booklet_sat.pdf && pdfbook booklet_sun.pdf


fetch:
	wget -O xml https://fosdem.org/2015/schedule/xml


gen_2014:
	./generate.py xml.2014

2014: gen_2014 tex

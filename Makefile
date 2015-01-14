all: gen tex

gen:
	./generate.py

tex:
	pdflatex booklet_sat && pdflatex booklet_sun

booklet:
	pdfbook --booklet 'true' --suffix 'print' booklet_sat.pdf && pdfbook --booklet 'true' --suffix 'print' booklet_sun.pdf

clean:
	rm -f *.aux *.log *.out

distclean: clean
	rm -f gen-*.tex generated/*.tex booklet_sat*.pdf booklet_sun*.pdf


fetch:
	wget -nv --no-check-certificate -O xml https://fosdem.org/2015/schedule/xml


gen_2014:
	./generate.py xml.2014

2014: gen_2014 tex

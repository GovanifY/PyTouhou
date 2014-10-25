all: ST.DAT CM.DAT

ST:
	make -C ST

ST.DAT: ST
	thdat c6 ST.DAT ST/*


CM.DAT: ST
	thdat c6 CM.DAT ST/etama* ST/face00* ST/player*


clean:
	make -C ST/ clean


mrproper:
	rm -f ST.DAT CM.DAT

.PHONY: clean mrproper ST

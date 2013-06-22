all: stg1bg.png stg1bg.anm stage1.std face03a.anm face03b.anm face42.png eff01.png eff01.anm stg1enm2.anm ecldata1.ecl stg1enm.png stg1enm.anm stg1enm2.anm msg1.dat etama3.anm etama3.png etama4.anm etama4.png

face42.png: face.svg
	inkscape -e face42.png face.svg


stg1bg.png: stg1bg.svg
	inkscape -e stg1bg.png stg1bg.svg


stg1enm.png: stg1enm.svg
	inkscape -e stg1enm.png stg1enm.svg


eff01.png: eff01.svg
	inkscape -e eff01.png eff01.svg


stg1bg.anm: stg1bg.script
	thanm c stg1bg.anm stg1bg.script


stg1enm.anm: stg1enm.script
	thanm c stg1enm.anm stg1enm.script


face03a.anm: face03a.script
	thanm c face03a.anm face03a.script


face03b.anm: face03a.script
	thanm c face03b.anm face03a.script


eff01.anm: eff01.script
	thanm c eff01.anm eff01.script


etama3.anm: etama3.script
	thanm c etama3.anm etama3.script


etama4.anm: etama4.script
	thanm c etama4.anm etama4.script


etama3.png: etama3.svg
	inkscape -e etama3.png etama3.svg


etama4.png: etama4.svg
	inkscape -e etama4.png etama4.svg


stg1enm2.anm: stg1enm2.script
	thanm c stg1enm2.anm stg1enm2.script


ecldata1.ecl: make_ecl.py
	PYTHONPATH=../../ python2 make_ecl.py


stage1.std: make_stage.py
	PYTHONPATH=../../ python2 make_stage.py


msg1.dat: msg1.script
	thmsg c6 msg1.script msg1.dat


clean:
	rm -f stg1bg.png stg1bg.anm stage1.std face03a.anm face03b.anm face42.png eff01.png eff01.anm stg1enm2.anm ecldata1.ecl stg1enm.png stg1enm.anm stg1enm2.anm msg1.dat etama3.anm etama3.png etama4.anm etama4.png

.PHONY: all clean

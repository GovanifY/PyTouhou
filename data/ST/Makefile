PNG := stg1bg.png face.png eff01.png stg1enm.png etama3.png etama4.png player00.png
ANM := stg1bg.anm face00a.anm face00b.anm face00c.anm face03a.anm face03b.anm eff01.anm stg1enm2.anm stg1enm.anm stg1enm2.anm etama3.anm etama4.anm player00.anm
OTHER := stage1.std ecldata1.ecl msg1.dat

all: $(PNG) $(ANM) $(OTHER)

%.png: %.svg
	inkscape -e $@ $<

%.anm: %.script
	thanm c $@ $<

ecldata1.ecl: make_ecl.py
	PYTHONPATH=../../ python3 make_ecl.py

stage1.std: make_stage.py
	PYTHONPATH=../../ python3 make_stage.py

msg1.dat: msg1.script
	thmsg c6 msg1.script msg1.dat

# Those should have their own script.
face00b.anm: face03a.script
	thanm c $@ $<

face00c.anm: face03a.script
	thanm c $@ $<

face03b.anm: face03a.script
	thanm c $@ $<

clean:
	$(RM) $(PNG) $(ANM) $(OTHER)

.PHONY: all clean

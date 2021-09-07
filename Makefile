ANDYDIR="tmp_andybot"
pwman: src/pwman.py src/libpwman.py
	python -m zipapp src -m "pwman:cli" -o pwman -p "/usr/bin/env python3"
andyprivatebot: src/andyprivatebot.py src/libpwman.py
	rm -rf ${ANDYDIR}
	mkdir ${ANDYDIR}
	install src/andyprivatebot.py src/libpwman.py ${ANDYDIR}
	python -m zipapp ${ANDYDIR} -o andyprivatebot.pyz -m "andyprivatebot:main"
andyprivatebot_install:
	install andyprivatebot.pyz /usr/local/libexec

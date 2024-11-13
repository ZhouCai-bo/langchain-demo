all: install

PROJECT_NAME=langchain_demo
PROJECT_HOME=~/project/$(PROJECT_NAME)
VENV_HOME=$(PROJECT_HOME)/virtualenv

install:
	mkdir -p $(PROJECT_HOME)/var/run; \
	mkdir -p $(PROJECT_HOME)/var/www; \
	mkdir -p $(PROJECT_HOME)/var/log; \
	if [ ! -d $(VENV_HOME) ]; \
	then \
		/usr/bin/python3 -m venv $(VENV_HOME); \
		$(VENV_HOME)/bin/pip3 install -U distribute; \
		$(VENV_HOME)/bin/pip3 install -U uwsgi==2.0.24; \
	fi
	source $(VENV_HOME)/bin/activate; \
	$(VENV_HOME)/bin/pip install --index-url https://mirrors.aliyun.com/pypi/simple -r requirements.txt; \
	rsync -av --delete src $(PROJECT_HOME)/; \
	rsync -av --delete static/* $(PROJECT_HOME)/var/www/; \
	touch $(PROJECT_HOME)/var/run/reload; \

init:
	pre-commit install --install-hooks;

codeformat:
	pre-commit run -a;

gitblame:
	git config blame.ignoreRevsFile .git-blame-ignore-revs;
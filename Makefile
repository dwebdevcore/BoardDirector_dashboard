DB_NAME = "boarddocuments_db"
TEST_APPS = "accounts" "billing" "committees" "common" "customer_io" "dashboard" "documents" "meetings" "news" "profiles" "registration"

default: info

info:
	@echo "Set up development environment using 'make install'"
	@echo "Do Not Use on production server!"

install: _settings requirements db end

_settings:
	@echo "Emitting local development settings module"
	@cp settings/local.py.example settings/local.py

requirements:
	@echo "Installing requirements"
	@pip install --exists-action=s -r requirements-dev.txt

db: dropdb createdb syncdb migrate loaddata

createdb:
	@echo "Creating PostgreSQL database $(DB_NAME)"
	@make -i _createdb >> /dev/null

_createdb:
	@createdb $(DB_NAME)

dropdb:
	@echo "Destroying PostgreSQL database $(DB_NAME)"
	@make -i _dropdb >> /dev/null

_dropdb:
	@dropdb $(DB_NAME)

syncdb:
	@echo "Syncing database"
	@python manage.py syncdb --noinput -v 0

migrate:
	@echo "Running migrations"
	@python manage.py migrate -v 0

loaddata:
	@echo "Applying patch to croppy fields module for use with PostgreSQL database"
	@echo "Loading additional data fixtures"
	@python manage.py loaddata initial_data
	@echo "Loading flatpages"
	@python manage.py loaddata flatpages
	@python manage.py filldb

end:
	@echo "You can now run development server using 'make run' command"

run:
	@python manage.py runserver

test:
	@python manage.py test $(TEST_APPS)

makemessages:
	python manage.py makemessages -a

makemessagesjs:
	python manage.py makemessages -d djangojs -a

compilemessages:
	python manage.py compilemessages

clean:
	@echo "Cleaning *.pyc files"
	@find . -name "*.pyc" -exec rm -f {} \;

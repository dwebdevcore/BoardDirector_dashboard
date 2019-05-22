#!/bin/bash

# Build virtualenv

if [ -d ".env" ]; then
  echo "**> virtualenv exists"
else
  echo  "**> creating virtualenv"
  virtualenv --no-site-packages .env
fi

# Vitrualenv actiovation
source .env/bin/activate

# Installig requirements
pip install --exists-action=s -r jenkins/requirements.txt

# Copy local settings
echo "**>copy local.py"
cp settings/jenkins.py.example settings/local.py

# Drop and create database

DB_NAME="boarddocumentsdb"

RESULT=`psql --list | grep $DB_NAME`

if [ -n "$RESULT" ] ; then
  echo "drop databse $DB_NAME"
  dropdb $DB_NAME
  echo "create database $DB_NAME"
  createdb $DB_NAME
else
  echo "create database $DB_NAME"
  createdb $DB_NAME
fi

export DJANGO_SETTINGS_MODULE=settings.base

find . -name "*.pyc" -exec rm -f {} \;
./manage.py jenkins --pep8-max-line-length=160

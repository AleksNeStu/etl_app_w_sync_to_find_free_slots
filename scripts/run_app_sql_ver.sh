#set -x

cd ../meet_app
pwd
set -o allexport && source ../configs/local.env && source ../configs/flask.env && set +o allexport
source ../.venv/bin/activate
#flask run --port=5000 --without-threads

export IS_DEPLOY='0' IS_SQL_VERSION='1' && python3 app.py run --port=5000 --host=0.0.0.0 --without-threads

# env FLASK_APP=app.py flask run
#set +x
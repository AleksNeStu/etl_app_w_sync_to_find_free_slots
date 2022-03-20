#set -x
#TODO: Add forced run options
cd ../meet_app
pwd
set -o allexport && source ../configs/local.env && source ../configs/flask.env && set +o allexport

source .venv/bin/activate
python3 bin/load_data.py

#set +x
"""Flask application run."""

import logging
import sys
import os
import flask


app = flask.Flask(__name__)
app.deploying = bool(int(os.getenv('IS_DEPLOY', '0')))

def main():
    configure()

    if not app.testing and not app.deploying:
        app.run(debug=True, host='localhost')

def configure():
    global admin, email, toolbar

    init_logging()


def init_logging():
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    # logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)
    # logging.getLogger("sqlalchemy.pool").setLevel(logging.DEBUG)


if __name__ in ('__main__', 'pypi_org.app'):
    main()

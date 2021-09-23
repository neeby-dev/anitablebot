import os
from boto.s3.connection import S3Connection

# Heroku
TELEGRAM_TOKEN = S3Connection(os.environ['TELEGRAM_TOKEN'])
DATABASE_URL = S3Connection(os.environ['DATABASE_URL'])

# Local
# TELEGRAM_TOKEN = ''
# DATABASE_URL = ''

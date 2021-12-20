class config(object):
    DEBUG = False
    TESTING = False

class DevelopmentConfig(config):
    DEBUG = True
    SECRET_KEY = '1289348290jfd921ncks213'
    USERS_FILE_PATH = 'static/Users'

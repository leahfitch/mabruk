import os
import shutil

MABRUK_HOME = '/tmp/mabruk-test-home'


def setup():
    if os.path.exists(MABRUK_HOME):
        raise Exception, "Test environment directory, %s already exists" % MABRUK_HOME
    os.mkdir(MABRUK_HOME)


def teardown():
    shutil.rmtree(MABRUK_HOME)
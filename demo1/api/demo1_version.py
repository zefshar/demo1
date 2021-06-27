AUTHORS_EMAILS = 'ivict@rambler.ru'
AUTHORS = 'Ivan Usalko'


class Demo1Version(object):
    MAJOR = 0
    MINOR = 1
    BUILD = 2  # BUILD ON BAMBOO CAN CHANGE THAT, AFTER CALL buildew_deploy.py

    @staticmethod
    def standard():
        return '.'.join([str(Demo1Version.MAJOR),
                         str(Demo1Version.MINOR),
                         str(Demo1Version.BUILD)])

    @staticmethod
    def category():
        return 'Demo1'

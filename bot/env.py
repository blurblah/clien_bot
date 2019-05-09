# from flask-env https://github.com/mattupstate/flask-environments/issues/7
import os
import yaml


class Singleton(object):
    __instance = None

    @classmethod
    def __get_instance(cls):
        return cls.__instance

    @classmethod
    def instance(cls, *args, **kwargs):
        cls.__instance = cls(*args, **kwargs)
        cls.instance = cls.__get_instance
        return cls.__instance


class Environments(Singleton):

    def __init__(self, var_name=None, default_env=None):
        self.var_name = var_name or 'BOT_ENV'
        self.default_env = default_env or 'LOCAL'
        self.env = os.environ.get(self.var_name, self.default_env)
        self.config = dict()
        self.config['ENVIRONMENT'] = self.env
        self.from_yaml('config.yml')

    def from_yaml(self, path):
        with open(path) as f:
            c = yaml.safe_load(f)

        for name in self._possible_names():
            try:
                c = c[name]
            except:
                pass

        for key in c.keys():
            if key.isupper():
                self.config[key] = c[key]

    def _possible_names(self):
        return (self.env, self.env.capitalize(), self.env.lower())

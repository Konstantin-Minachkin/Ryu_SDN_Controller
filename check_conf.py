# -*- coding: utf-8 -*-

from config import Config

if __name__ == '__main__':
    print('Config changed: ', Config().check_config_for_difference('conf_old.yaml'))
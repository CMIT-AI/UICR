import json
import os
import yaml
from consul import Consul

def get_kv(key):
    consul_host = configs['CONSUL']["HOST"]
    consul_port = configs['CONSUL']["PORT"]
    if consul_host and consul_port:
        consul_client = Consul(consul_host, consul_port)
        index, data = consul_client.kv.get(key)
        try:
            config = json.loads(data['Value'])
            return config
        except Exception:
            pass

        config = yaml.load(data['Value'], Loader=yaml.FullLoader)
        return config
    else:
        return None

def reload_config(config_file:str):
    configs = {}
    if os.path.exists(config_file):
        configs = json.load(open(config_file, 'r', encoding='utf-8'))
    return configs

__all__ = ["configs"]
configs = {
    "SERVICE": "uicr",
    "PORT": 39060,
    "DATA_DIR": "data",
    "LOG_DIR": "logs",
}
configs.update(reload_config(os.path.join("config", "config.json")))
configs.update(reload_config(os.path.join(configs["DATA_DIR"], "config.json")))

print(configs)

if configs['SAVE_IMG_DIR'] and not os.path.exists(configs['SAVE_IMG_DIR']):
    os.makedirs(configs['SAVE_IMG_DIR'])
import os
import sys
sys.path.append(os.path.abspath('.'))
import time
from consul import Consul, Check
from config import configs
from services.logger import Logger

logger = Logger("uicr")

consul_default_rest_port = 8500
consul_host = configs['CONSUL']["HOST"]
consul_port = configs['CONSUL']["PORT"]

def register_service(name, service_id, host, port, tags=None):
    if consul_host and consul_port:
        try:
            consul_client = Consul(consul_host, consul_port)
            tags = tags or []
            consul_client.agent.service.register(
                name,
                service_id,
                host,
                port,
                tags,
                # 健康检查ip端口，检查时间：5,超时时间：30，注销时间：30s
                check=Check().http('http://%s:%s'%(host, port), '10s', '1s', '1s'))
            return True
        except Exception as err:
            logger.exception(err.__str__())
            return False
    else:
        return False

def get_service_by_id(service_id):
    if consul_host and consul_port:
        try:
            consul_client = Consul(consul_host, consul_port)
            service = consul_client.agent.services().get(service_id)
            # if service:
            #     pass
            # else:
            #     servers = consul_client.agent.members()
            #     for server in servers:
            #         service = Consul(server['Addr'], consul_default_rest_port).agent.services().get(service_id)
            #         if service:
            #             break
            return service
        except Exception as err:
            logger.exception(err.__str__())
            return None
    else:
        return None

def get_service_by_name(service_name):
    services = []
    if consul_host and consul_port:
        consul_client = Consul(consul_host, consul_port)
        servers = consul_client.agent.members()
        for server in servers:
            services += Consul(server['Addr'], consul_default_rest_port).agent.services().values()
        return [s for s in services if s['Service'] == service_name]
    else:
        return services

def reg_daemon():
    service_name = configs['SERVICE']
    host = configs['HOST']
    port = configs['PORT']
    service_id = '%s:%s' % (host, port)

    while True:
        try:
            service = get_service_by_id(service_id)
            if service:
                pass
            else:
                if register_service(service_name, service_id, host, port):
                    logger.info('%s has been registered to reg server %s' % (service_id, consul_host))
        except Exception as err:
            logger.exception(err.__str__())
        finally:
            time.sleep(300)

if __name__ == '__main__':
    reg_daemon()
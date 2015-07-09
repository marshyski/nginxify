from flask import Flask, request, jsonify
from flask_limiter import Limiter
from jinja2 import Environment
from jinja2.loaders import FileSystemLoader
from werkzeug.contrib.fixers import ProxyFix
from subprocess import call
import sys
import os
import psutil
import yaml

config_yaml = yaml.load(file('config.yaml', 'r'))

nginx_sites_enabled = config_yaml['nginx_sites_enabled']

if config_yaml['config_limit']:
    config_limit = int(config_yaml['config_limit'])
else:
    config_limit = 'None'

if config_yaml['request_limit']:
    request_limit = config_yaml['request_limit']
else:
    request_limit = '7200 per hour'

app = Flask(__name__)
limiter = Limiter(app)

env = Environment(loader=FileSystemLoader('templates'))
template = env.get_template('nginx')

def config_count():
    return int(len([name for name in os.listdir(nginx_sites_enabled) if os.path.isfile(os.path.join(nginx_sites_enabled, name))]))

@app.route('/api/<string:server>/<string:port>', methods=['POST'])
@limiter.limit(request_limit)
def create_nginx_config(server, port):
    """Create NGINX config in sites-enabled directory"""

    if config_count() >= config_limit:
       return jsonify(message='reached max configuration limit', config_limit=config_limit, config_count=config_count(), status=400)

    ip = request.remote_addr
    nginx_config = nginx_sites_enabled + '/' + server
    temp = sys.stdout
    sys.stdout = open(nginx_config, 'w')
    print template.render(server_name=server, proxy_addr=ip, port=port)
    sys.stdout.close()
    sys.stdout = temp

    call(["/usr/sbin/service", "nginx", "restart"])

    processes = [proc.name() for proc in psutil.process_iter()]

    if 'nginx' in processes:
       return jsonify(server_name=server, proxy_address=ip, port=port, config_count=config_count(), status=200)
    else:
       os.remove(nginx_config)
       call(["/usr/sbin/service", "nginx", "restart"])
       return jsonify(message='configuration could not be generated', status=500)

@app.route('/api/count')
@limiter.limit(request_limit)
def get_config_count():
    """Get NGINX sites-enabled configs count"""
    return jsonify(config_count=config_count(), config_limit=config_limit, status=200)

app.wsgi_app = ProxyFix(app.wsgi_app)

if __name__ == '__main__':
    app.run()

from flask import Flask, request, jsonify, make_response, abort
from flask_limiter import Limiter
from jinja2 import Environment
from jinja2.loaders import FileSystemLoader
from werkzeug.contrib.fixers import ProxyFix
from subprocess import call
from datetime import datetime, timedelta
from psutil import cpu_percent, process_iter
import sys
import os
import yaml
import time

start_time = time.time()

hostname = os.uname()[1]

template_dir = os.getcwd() + '/nginxify/templates'

config_file = os.getcwd() + '/nginxify/config.yaml'

config_yaml = yaml.load(file(config_file, 'r'))

nginx_sites_enabled = config_yaml['nginx_sites_enabled']

nginx_template = config_yaml['nginx_template']

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

env = Environment(loader=FileSystemLoader(template_dir))
template = env.get_template(nginx_template)

def config_count():
    """Return count of files in NGINX sites-enabled directory"""
    return int(len([name for name in os.listdir(nginx_sites_enabled) if os.path.isfile(os.path.join(nginx_sites_enabled, name))]))

def uptime():
    """Return uptime about nginxify for health check"""
    seconds = timedelta(seconds=int(time.time() - start_time))
    d = datetime(1,1,1) + seconds
    return("%dD:%dH:%dM:%dS" % (d.day-1, d.hour, d.minute, d.second))

@app.route('/api/<string:server>/<string:port>', methods=['POST'])
@limiter.limit(request_limit)
def create_nginx_config(server, port):
    """Create NGINX config in sites-enabled directory"""

    if config_count() >= config_limit:
       abort(400)

    ip = request.remote_addr
    nginx_config = nginx_sites_enabled + '/' + server
    temp = sys.stdout
    sys.stdout = open(nginx_config, 'w')
    print template.render(server_name=server, proxy_addr=ip, port=port)
    sys.stdout.close()
    sys.stdout = temp

    call(["/usr/sbin/service", "nginx", "restart"])

    processes = [proc.name() for proc in process_iter()]

    if 'nginx' in processes:
       return jsonify(server_name=server, proxy_address=ip, port=port, config_count=config_count(), status=200)
    else:
       os.remove(nginx_config)
       call(["/usr/sbin/service", "nginx", "restart"])
       abort(500)

@app.route('/api/<string:config>', methods=['DELETE'])
@limiter.limit(request_limit)
def delete_nginx_config(config):
    """Delete NGINX config in sites-enabled directory"""
    nginx_config = nginx_sites_enabled + '/' + config
    os.remove(nginx_config)
    call(["/usr/sbin/service", "nginx", "restart"])
    return jsonify(message="site deleted", config_count=config_count(), status=200)

@app.route('/api/count')
@limiter.limit(request_limit)
def get_config_count():
    """Get NGINX sites-enabled configs count"""
    return jsonify(config_count=config_count(), config_limit=config_limit, status=200)

@app.route('/api/health')
def health():
    """Get NGINXify health check"""
    return jsonify(hostname=hostname, uptime=uptime(), cpu_percent=int(cpu_percent(interval=None, percpu=False)), status=200)

@app.errorhandler(400)
def bad_request(error):
    """400 BAD REQUEST"""
    return make_response(jsonify({"error": "reached max configuration limit", "config_limit": config_limit, "config_count": config_count()}), 400)

@app.errorhandler(500)
def internal_error(error):
    """500 INTERNAL SERVER ERROR"""
    return make_response(jsonify({"error": "configuration could not be generated"}), 500)

app.wsgi_app = ProxyFix(app.wsgi_app)

if __name__ == '__main__':
    app.run()

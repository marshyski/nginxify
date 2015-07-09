from flask import Flask, request, jsonify
from flask_limiter import Limiter
from jinja2 import Environment
from jinja2.loaders import FileSystemLoader
from werkzeug.contrib.fixers import ProxyFix
from subprocess import call
import sys
import os
import psutil

app = Flask(__name__)
limiter = Limiter(app)

env = Environment(loader=FileSystemLoader('templates'))
template = env.get_template('nginx')

@app.route('/api/<string:server>/<string:port>', methods=['POST'])
@limiter.limit("1 per second")
def create_nginx_config(server, port):
    temp = sys.stdout
    ip = request.remote_addr
    nginx_config = '/etc/nginx/sites-enabled/' + server
    print nginx_config
    sys.stdout = open(nginx_config, 'w')
    print template.render(server_name=server, proxy_addr=ip, port=port)
    sys.stdout.close()
    sys.stdout = temp
    call(["/usr/sbin/service", "nginx", "restart"])
    processes = [proc.name() for proc in psutil.process_iter()]

    if 'nginx' in processes:
       return jsonify(server_name=server, proxy_address=ip, port=port, status=200)
    else:
       os.remove(nginx_config)
       call(["/usr/sbin/service", "nginx", "restart"])
       return jsonify(message='configuration could not be generated', status=500)

app.wsgi_app = ProxyFix(app.wsgi_app)

if __name__ == '__main__':
    app.run()

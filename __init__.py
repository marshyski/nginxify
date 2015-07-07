from flask import Flask, request, jsonify
from jinja2 import Environment
import sys
from subprocess import call
from werkzeug.contrib.fixers import ProxyFix

app = Flask(__name__)

env = Environment(loader=FileSystemLoader('templates'))
template = env.get_template('nginx')

@app.route('/api/<string:server>/<string:port>', methods=['POST'])
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

    return jsonify(server_name=server, proxy_address=ip, port=port, status=200)

app.wsgi_app = ProxyFix(app.wsgi_app)

if __name__ == '__main__':
    app.run()

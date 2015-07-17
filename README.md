# nginxify

Make a site-enable config for NGINX via an API


What the heck is this thing?
----------------------------

I wanted to be able to automatically add a reverse proxy entry to NGINX.  Ideal if you want a subdomain and docker container per customer instantly in-service.


**Flow**

![Diagram](https://s3.amazonaws.com/timski-pictures/nginxify.jpg)


Getting Started
---------------

**From host with app listening on 0.0.0.0:8080**

    curl -XPOST 'http://nginxify/api/sub1.domain.com/8080'
    {
      "config_count": 3,
      "port": "8080",
      "proxy_address": "10.177.0.55",
      "server_name": "sub1.domain.com",
      "status": 200
    }

**If basic auth is enabled on NGINX for API (recommended)**

    curl -u yourusername:yourpassword -XPOST 'http://nginxify/api/sub1.domain.com/8080'

**Delete site-enabled configuration**

    curl -XDELETE 'http://nginxify/api/sub1.domain.com'
    {
      "config_count": 3,
      "message": "sub1.domain.com site deleted",
      "status": 200
    }

**Get count of files in NGINX sites-enabled directory**

    curl -XGET http://nginxify/api/count
    {
      "config_count": 3,
      "config_limit": "None",
      "status": 200
    }

**Health check endpoint**

    curl -XGET http://nginxify/api/health
    {
      "cpu_percent": 12,
      "hostname": "nginxify01",
      "status": 200,
      "uptime": "2D:5H:3M:55S"
    }


Configurations
--------------

**config.yaml**

    # NGINX's sites enabled directory
    nginx_sites_enabled: '/etc/nginx/sites-enabled'

    # NGINX jinja2 template name in templates directory
    nginx_template: 'nginx'

    # Limit the max number of NGINX sites enabled configurations
    config_limit:

    # API request rate limit
    # http://flask-limiter.readthedocs.org/en/stable/
    request_limit: '1 per second'


Recommendations
---------------

 1. Have the API not listen on port 80
 2. Create IPTables/FirewallD/Security Group rules to only allow inbound traffic from CIDR or IP Ranges of Docker hosts
 3. Use SSL and Basic Auth in NGINX for the API
 4. If you load balance NGINXify, containers will have to send a POST request to all NGINXify servers.


Default NGINX Template
----------------------

    server {
      listen       80;
      server_name  {{ server_name }};

      location ~ /(.git|.svn|README.md) {
        deny all;
        log_not_found off;
        access_log off;
        return 404;
      }

      location = /favicon.ico {
        log_not_found off;
        access_log off;
      }

      location / {
        try_files $uri @service;
      }

      location @service {
        proxy_pass http://{{ proxy_addr }}:{{ port }};
        proxy_redirect off;
        proxy_buffering off;

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
	    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;

        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
      }
    }

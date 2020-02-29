FROM registry.corp.imdada.cn:5000/env/python-uwsgi-nginx:2.7.15

WORKDIR /data/apps

COPY ./requirements.txt /requirements.txt

RUN pip install -r /requirements.txt

COPY ./ /data/apps

ENTRYPOINT ["/usr/bin/dumb-init", "-v", "--rewrite", "15:2", "--", "/docker-entrypoint.sh"]

CMD ["/usr/local/bin/uwsgi", "-y", "/data/apps/uwsgi.yaml"]
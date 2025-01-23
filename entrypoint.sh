#!/bin/bash
# $python services/consul_service.py &
$python -m gunicorn --preload -c config/gunicorn.py main:app
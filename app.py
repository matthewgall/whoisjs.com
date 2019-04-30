#!/usr/bin/env python3

import os, socket, json
from bottle import route, run, response

def enable_cors(fn):
    def _enable_cors(*args, **kwargs):
        # set CORS headers
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Origin, Accept, Content-Type, X-Requested-With, X-CSRF-Token'

        if bottle.request.method != 'OPTIONS':
            # actual request; reply with the actual response
            return fn(*args, **kwargs)

    return _enable_cors

def lookup(domain, server="whois.cloudflare.com"):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((server, 43))

        #convert string to bytes, socket need bytes
        s.send((domain + "\r\n").encode())

        #declares a bytes
        response = b""
        while True:
            data = s.recv(4096)
            response += data
            if not data:
                break
        s.close()

        return response.decode()
    except:
        return None

@enable_cors
@route('/api/v1/<domain>')
@route('/api/v1/<domain>/<server>')
def get_domain(domain, server='whois.cloudflare.com'):
    data = {
        'success': false
    }

    try:
        l = lookup(domain, server)     
        data['success'] = True
        data['data'] = l
    except:
        pass
    response.content_type = 'application/json'
    return json.dumps(data)

if __name__ == "__main__":
    run(host=os.getenv('HOST', '0.0.0.0'), port=os.getenv('PORT', 8000))
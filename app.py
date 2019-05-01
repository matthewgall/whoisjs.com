#!/usr/bin/env python3

import os, socket, json
from bottle import route, run, response, request, static_file

def enable_cors(fn):
    def _enable_cors(*args, **kwargs):
        # set CORS headers
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Origin, Accept, Content-Type, X-Requested-With, X-CSRF-Token'

        if request.method != 'OPTIONS':
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

@route('/favicon.ico')
def favicon():
    response.content_type = 'image/x-icon'
    return static_file('favicon.ico', './')

@enable_cors
@route('/api/v1/<domain>')
@route('/api/v1/<domain>/<server>')
def get_domain(domain, server='whois.cloudflare.com'):
    data = {
        'success': False
    }

    try:
        l = lookup(domain, server)

        # now we look to try and parse it
        output = list(filter(None, l.split('\n')))
        for o in output:
            parsed_data = o.lower().split(':')
            key = parsed_data[0].split(' ')
            if key[0] in ['domain', 'registry', 'registrar', 'tech', 'admin', 'billing', 'updated', 'creation']:
                elm = parsed_data[0].replace("{} ".format(key[0]), "").replace(' ', '_').replace('/', '_')
                val = o.lower().split(':', 1)[1].strip()
                if not data.get(key[0]):
                    data[key[0]] = {}
                    if not val == '': 
                        data[key[0]][elm] = val
                else:
                    if not val == '':
                        data[key[0]][elm] = val

        # remove erroneous keys
        del data['domain']['status']
        data['success'] = True
        data['raw'] = l
    except:
        pass
    response.content_type = 'application/json'
    return json.dumps(data)

if __name__ == "__main__":
    run(host=os.getenv('HOST', '0.0.0.0'), port=os.getenv('PORT', 8000))
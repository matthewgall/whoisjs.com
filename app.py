#!/usr/bin/env python3

import os, socket, json
from bottle import route, run, response

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

@route('/api/v1/get/<domain>')
def get_domain(domain):
    try:
        l = lookup(domain)     
        data = {
            'success': 'true',
            'data': l
        }
    except:
        data = {
            'success': 'false'
        }
    response.content_type = 'application/json'
    return json.dumps(data)

if __name__ == "__main__":
    run(host=os.getenv('HOST', '0.0.0.0'), port=os.getenv('PORT', 8000))
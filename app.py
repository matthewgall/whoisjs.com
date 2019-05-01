#!/usr/bin/env python3

import os, socket, json, logging, argparse
from bottle import default_app, route, run, response, request, redirect, template, static_file

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

@route('/static/<filepath:path>')
def static(filepath):
	return static_file(filepath, root='views/static')

@route('/', ('GET', 'POST'))
def index():
	if request.method == "POST":
		domain = request.forms.get('domain')
		return redirect("/{}".format(domain))

	return template("home")

@route('/<domain>', ('GET'))
def record(domain):
	try:
		l = lookup(domain)
		return template("whois", {
			'name': domain,
			'data': l
		})
	except:
		return "We encountered an error completing your request"

@enable_cors
@route('/api/v1/<domain>')
@route('/api/v1/<domain>/<server>')
@route('/api/v1/<domain>/<server>/<raw>')
def get_domain(domain, server='whois.cloudflare.com', raw=None):
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
				val = o.split(':', 1)[1].strip()
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
		if not raw == None:
			data['raw'] = l
	except:
		pass
	response.content_type = 'application/json'
	return json.dumps(data)

if __name__ == '__main__':

	parser = argparse.ArgumentParser()

	# Server settings
	parser.add_argument("-i", "--host", default=os.getenv('IP', '127.0.0.1'), help="server ip")
	parser.add_argument("-p", "--port", default=os.getenv('PORT', 5000), help="server port")

	# Redis settings
	parser.add_argument("--redis-host", default=os.getenv('REDIS_HOST', 'redis'), help="redis hostname")
	parser.add_argument("--redis-port", default=os.getenv('REDIS_PORT', 6379), help="redis port")
	parser.add_argument("--redis-pw", default=os.getenv('REDIS_PW', ''), help="redis password")
	parser.add_argument("--redis-ttl", default=os.getenv('REDIS_TTL', 60), help="redis time to cache records")

	# Application settings
	parser.add_argument("-s", "--server", default=os.getenv('SERVER', 'whois.cloudflare.com'), help="whois server hostname")

	# Verbose mode
	parser.add_argument("--verbose", "-v", help="increase output verbosity", action="store_true")
	args = parser.parse_args()

	if args.verbose:
		logging.basicConfig(level=logging.DEBUG)
	else:
		logging.basicConfig(level=logging.INFO)
	log = logging.getLogger(__name__)

	try:
		app = default_app()
		app.run(host=args.host, port=args.port, server='tornado')
	except:
		log.error("Unable to start server on {}:{}".format(args.host, args.port))
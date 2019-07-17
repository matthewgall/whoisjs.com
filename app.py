#!/usr/bin/env python3

import os, socket, json, logging, argparse, re
from bottle import default_app, route, run, response, request, redirect, template, static_file
from tldextract import extract
import validators, redis

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

def get_whois(domain):
	try:
		tld = extract(domain).suffix
		# next we do a lookup against whois.iana.org
		d = lookup(tld, "whois.iana.org")
		# and find the whois server
		r = re.findall(r"whois:\s*(.*)", d)
		return r[0]
	except:
		return None

@route('/robots.txt')
def robots():
	response.content_type = 'text/plain'
	return template("robots")

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
@route('/<domain>/<server>', ('GET'))
def record(domain, server=None):
	try:
		try:
			if not validators.domain(domain):
				raise ValueError
		except:
			return template("error", {
				'message': 'The domain name provided is not valid. Please check and try again'
			})
		
		global red
		try:
			if red.get(request.path):
				log.info("Using cached value for {}".format(request.path))
				return template("whois", {
					'path': request.path,
					'name': domain,
					'data': red.get(request.path)
				})
		except:
			pass

		# Now, if they haven't set a server, we'll default to the TLD one
		if not server:
			server = get_whois(domain)

		log.info("Using server: {} for domain: {}".format(server, domain))
		
		l = lookup(domain, server)
		red.set(request.path, l, ex=3600)
		return template("whois", {
			'path': request.path,
			'name': domain,
			'data': l
		})
	except:
		return template("error", {
			'message': "We encountered an error completing your request"
		})

@route('/api/v1/whois/<domain>')
@enable_cors
def get_whois_server(domain):
	data = {
		'success': False
	}

	response.content_type = 'application/json'
	try:
		if not validators.domain(domain):
			raise ValueError
	except:
		data['error'] = "The domain name provided is not valid"
		return json.dumps(data)

	# Now, if they haven't set a server, we'll default to the TLD one
	data['server'] = get_whois(domain)
	data['success'] = True
	return json.dumps(data)
	
@route('/api/v1/<domain>')
@route('/api/v1/<domain>/<server>')
@enable_cors
def get_domain(domain, server=None):
	data = {
		'success': False
	}

	response.content_type = 'application/json'
	
	try:
		if not validators.domain(domain):
			raise ValueError
	except:
		data['error'] = "The domain name provided is not valid"
		return json.dumps(data)

	global red
	try:
		if red.get(request.path):
			log.info("Using cached value for {}".format(request.path))
			return red.get(request.path)
	except:
		pass

	# Now, if they haven't set a server, we'll default to the TLD one
	if not server:
		server = get_whois(domain)

	log.info("Using server: {} for domain: {}".format(server, domain))
	l = lookup(domain, server)

	# now we look to try and parse it
	output = list(filter(None, l.split('\n')))
	for o in output:
		m = re.findall(r"^((domain|registry|registrar|creation|updated|admin|tech|billing)\s([\w\s]*)):(.*)", o.lower().strip())
		if len(m) > 0:
			r = m[0]
			if not data.get(r[1]):
				data[r[1]] = {}
			val = r[2].replace(' ', '_')
			data[r[1]][val] = r[3].strip()
	
	try:
		del data['domain']['status']
	except:
		pass
	
	data['success'] = True
	data['raw'] = l
	
	# and now we cache it in redis
	red.set(request.path, json.dumps(data), ex=3600)
	return json.dumps(data)

if __name__ == '__main__':

	parser = argparse.ArgumentParser()

	# Server settings
	parser.add_argument("-i", "--host", default=os.getenv('HOST', '127.0.0.1'), help="server ip")
	parser.add_argument("-p", "--port", default=os.getenv('PORT', 5000), help="server port")

	# Redis settings
	parser.add_argument("--redis-url", default=os.getenv('REDIS_URL', None), help="redis url")
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
		if args.redis_url:
			global red
			red = redis.from_url(args.redis_url)
	except:
		log.fatal("Unable to connect to redis: {}".format(args.redis_url))

	try:
		app = default_app()
		app.run(host=args.host, port=args.port, server='tornado')
	except:
		log.error("Unable to start server on {}:{}".format(args.host, args.port))
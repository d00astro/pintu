
from flask import Flask, send_file, redirect
import RPi.GPIO as GPIO
import datetime
import time
import subprocess


# TODO: Put in config
listen_port = 10000
gate_pin = 7
signal_duration = 0.6
repetitions = 3
scheme = 'https'
net_location = 'astrom.sg'
prefix = '/home/door'
base_endpoint = "%s://%s%s" % (scheme, net_location, prefix)

log = []


def endpoint(path=""):
	return prefix + path


def link(path=""):
	return base_endpoint + path


GPIO.setmode(GPIO.BOARD)
GPIO.setup(gate_pin, GPIO.OUT)

app = Flask(__name__)


@app.route(endpoint("/reboot"))
def reboot():
	subprocess.call(["reboot", "now"])


@app.route(endpoint())
def gate():
	timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
	open_url = link("open_view")
	refresh_url = link()
	image_url = link("image_%s.jpg" % timestamp)
	return """
<html>
	<body bgcolor="#000000" text="#FFFFFF">
		<h1>[ <a href='%s'>Open</a> ]</h1><br/>
		<a href='%s'>
			<img src='%s' alt='Open Gate'>
		</a>
	</body>
</html>
""" % (open_url, refresh_url, image_url)


@app.route(endpoint("open_view"))
def open_view():
	open_gate()
	return redirect(link(), code=302)


@app.route(endpoint("/image<ts>.jpg"))
def image(ts):
	return send_file("fruits.png", mimetype='image/png')


@app.route(endpoint("/open"))
def open_gate():
	status = "%s : Entry " % datetime.datetime.now()
	try:
		GPIO.setmode(GPIO.BOARD)
		GPIO.setup(gate_pin, GPIO.OUT)
	except Exception as ex:
		status += "(GPIO failure: %s) " % ex

	try:
		for x in range(repetitions):
			GPIO.output(gate_pin,True)
			time.sleep(signal_duration)
			GPIO.output(gate_pin,False)
			time.sleep(signal_duration)
		status += "OK "
	except Exception as ex:
		status += "(Signal failure: %s) " % ex

	log.append(status)

	return 'Door Open!' + '<br/><br/>' + '<br/>'.join(log[::-1])


if __name__ == '__main__':
	app.run(debug=True, host="0.0.0.0", port=listen_port)

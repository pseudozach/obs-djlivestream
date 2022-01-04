import obspython as obs
# import urllib.request
import urllib.error
from urllib.request import Request, urlopen
# import qrcode
import os 
# from PIL import Image
import json
# import sseclient
from contextlib import contextmanager

url         = ""
invoicekey  = ""
interval    = 30
source_name = "djlscomment"
animation_one = os.path.dirname(__file__) + "/images/bitcoin.gif"
animation_two = os.path.dirname(__file__) + "/images/rocket.gif"
tip_threshold = 100

# ------------------------------------------------------------

def update_text():
	global url
	global invoicekey
	global interval
	global source_name

	if invoicekey == "":
		print("invoicekey is required")
		return

	try:
		livestreamurl = url + "/livestream/api/v1/livestream"
		req = Request(livestreamurl)
		req.add_header('X-Api-Key', invoicekey)

		response = urlopen(req)
		data = response.read()
		text = data.decode('utf-8')
		# print("got response text " + text)
		data = json.loads(text)

		settings = obs.obs_data_create()
		lnurlqrfilelocation = os.path.dirname(__file__) + "/lnurlqr.png"

		# Instead of using qrcode library use this with https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=Example
		qrserverurl = "https://api.qrserver.com/v1/create-qr-code/?size=250x250&margin=10&data=" + data['lnurl']
		qrcoderesponse = urlopen(qrserverurl)
		qrfile = qrcoderesponse.read()
		with open(lnurlqrfilelocation, 'wb') as output:
			output.write(qrfile)

		# set image to image source - old method for DJ Livestream via qrcode library
		# img = qrcode.make(data['lnurl'])
		# img.save(lnurlqrfilelocation)
		# # print("img created at " + lnurlqrfilelocation)

		obs.obs_data_set_string(settings, "file", lnurlqrfilelocation)
		
		# add new source
		current_scene = obs.obs_frontend_get_current_scene()
		scene = obs.obs_scene_from_source(current_scene)
		source = obs.obs_source_create_private("image_source", "djlsqrcode", settings)
		obs.obs_scene_add(scene, source)
		# print("lnurl QR Code added to scene")
		obs.obs_scene_release(scene)
		obs.obs_source_release(source)
		obs.obs_data_release(settings)

		# update existing source
		# obs.obs_source_update(source, settings)
		# obs.obs_data_release(settings)

	except urllib.error.URLError as err:
		obs.script_log(obs.LOG_WARNING, "Error opening URL '" + url + "': " + err.reason)
		obs.remove_current_callback()

# fetch latest comment from lnbits 
def update_comment():
	global url
	global invoicekey
	global interval
	global source_name
	global animation_one
	global animation_two
	global tip_threshold

	try:
		livestreamurl = url + "/api/v1/payments"
		req = Request(livestreamurl)
		req.add_header('X-Api-Key', invoicekey)

		response = urlopen(req)
		data = response.read()
		text = data.decode('utf-8')
		# TODO payments endpoint returns huge amount of invoices - find a way to limit it
		# print("update_comment got response text " + text)
		invoices = json.loads(text)
		print("invoices[0] " + str(invoices[0]))

		# get comment of last payment
		lastcomment = ""
		animationtoshow = animation_one
		for invoice in invoices:
			if invoice["amount"] > 0 and invoice["pending"] == False and invoice["extra"] and invoice["extra"]["comment"] and len(invoice["extra"]["comment"]) > 0:
				print("found an incoming invoice with comment: " + invoice["extra"]["comment"])
				lastcomment = str(int(invoice["amount"]/1000)) + " sats\n" + invoice["extra"]["comment"]
				if invoice["amount"]/1000 > tip_threshold:
					animationtoshow = animation_two
				break

		print("setting comment text to " + lastcomment)
		create_text_source(lastcomment)

		print("setting tip animation to " + animationtoshow)
		show_image_source(animationtoshow)

	except urllib.error.URLError as err:
		obs.script_log(obs.LOG_WARNING, "Error opening URL '" + url + "': " + err.reason)
		obs.remove_current_callback()

def refresh_pressed(props, prop):
	update_text()
	update_comment()

# ------------------------------------------------------------

def script_description():
	return "Shows LNBits QR Code from DJ Livestream plugin."

def script_update(settings):
	global url
	global invoicekey
	global interval
	global source_name
	global animation_one
	global animation_two
	global tip_threshold

	url         = obs.obs_data_get_string(settings, "url")
	invoicekey  = obs.obs_data_get_string(settings, "invoicekey")
	interval    = obs.obs_data_get_int(settings, "interval")
	source_name = obs.obs_data_get_string(settings, "source")
	animation_one = obs.obs_data_get_string(settings, "animationone")
	animation_two = obs.obs_data_get_string(settings, "animationtwo")
	tip_threshold  = obs.obs_data_get_int(settings, "tipthreshold")

	obs.timer_remove(update_comment)
	obs.timer_add(update_comment, interval * 1000)

def script_defaults(settings):
	obs.obs_data_set_default_string(settings, "url", "https://legend.lnbits.com")
	obs.obs_data_set_default_int(settings, "interval", 30)
	obs.obs_data_set_default_int(settings, "tip_threshold", 100)
	obs.obs_data_set_default_string(settings, "animation_one", os.path.dirname(__file__) + "/images/bitcoin.gif")
	obs.obs_data_set_default_string(settings, "animation_two", os.path.dirname(__file__) + "/images/rocket.gif")

def script_properties():
	props = obs.obs_properties_create()

	obs.obs_properties_add_text(props, "url", "LNBits URL", obs.OBS_TEXT_DEFAULT)
	obs.obs_properties_add_text(props, "invoicekey", "LNBits Invoice Key", obs.OBS_TEXT_DEFAULT)
	obs.obs_properties_add_int(props, "interval", "Update Interval (seconds)", 5, 3600, 1)
	obs.obs_properties_add_text(props, "animationone", "Regular Tip Animation File Location", obs.OBS_TEXT_DEFAULT)
	obs.obs_properties_add_int(props, "tipthreshold", "Large Tip Threshold (sats)", 1, 1000000, 1)
	obs.obs_properties_add_text(props, "animationtwo", "Large Tip Animation File Location", obs.OBS_TEXT_DEFAULT)

	obs.obs_properties_add_button(props, "button", "Add to Scene", refresh_pressed)
	return props

def create_text_source(lastcomment):
	previouscomment = print_private_data("private1")
	if previouscomment == lastcomment:
		print("same comment so don't do anything")
		return

	source = obs.obs_get_source_by_name("djlscomment")
	if source is None:
		print("djlscomment source does not exist so create it")
		current_scene = obs.obs_frontend_get_current_scene()
		scene = obs.obs_scene_from_source(current_scene)

		# set the text
		settings = obs.obs_data_create()
		obs.obs_data_set_string(settings, "text", lastcomment)

		# obs_source_create_private not
		newsource = obs.obs_source_create("text_ft2_source", "djlscomment", settings, None)
		obs.obs_scene_add(scene, newsource)
		print("djlscomment comment added to scene")
		obs.obs_scene_release(scene)
		obs.obs_source_release(newsource)
		obs.obs_data_release(settings)
	else:
		# print("djlscomment already exists setting the text")
		settings = obs.obs_data_create()
		obs.obs_data_set_string(settings, "text", lastcomment)
		obs.obs_source_update(source, settings)
		obs.obs_data_release(settings)
		obs.obs_source_release(source)
		
	write_private_data(lastcomment, "private1")

def show_image_source(animationtoshow):
	if animationtoshow == "":
		print("no animation file to show")
		return

	previousanimation = print_private_data("private2")
	if previousanimation == animationtoshow:
		print("same animation so don't do anything")
		return

	source_name = "djlsanimation"
	source = obs.obs_get_source_by_name(source_name)
	if source is None:
		print(source_name + " source does not exist so create it")
		current_scene = obs.obs_frontend_get_current_scene()
		scene = obs.obs_scene_from_source(current_scene)

		# set the image
		settings = obs.obs_data_create()
		obs.obs_data_set_string(settings, "file", animationtoshow)

		# obs_source_create_private not
		newsource = obs.obs_source_create("image_source", source_name, settings, None)
		obs.obs_scene_add(scene, newsource)
		print(source_name + " added to scene")
		obs.obs_scene_release(scene)
		obs.obs_source_release(newsource)
		obs.obs_data_release(settings)
	else:
		print(source_name + " already exists setting it")
		source_id = obs.obs_source_get_unversioned_id(source)
		settings = obs.obs_data_create()
		obs.obs_data_set_string(settings, "file", animationtoshow)
		obs.obs_source_update(source, settings)
		obs.obs_data_release(settings)
		obs.obs_source_release(source)

	write_private_data(animationtoshow, "private2")

def send_to_private_data(data_type, field, result):
    settings = obs.obs_data_create()
    set = getattr(obs, f"obs_data_set_{data_type}")
    set(settings, field, result)
    obs.obs_apply_private_data(settings)
    obs.obs_data_release(settings)

def write_private_data(datatowrite, field):
    result = datatowrite
    send_to_private_data("string", field, result)

@contextmanager
def p_data_ar(data_type, field):
    settings = obs.obs_get_private_data()
    get = getattr(obs, f"obs_data_get_{data_type}")
    try:
        yield get(settings, field)
    finally:
        obs.obs_data_release(settings)

def print_private_data(field):
	data = ""
	with p_data_ar("string", field) as value:
		# print("got data " + field + " " + value)
		data = value
	return data
import obspython as obs
# import urllib.request
import urllib.error
from urllib.request import Request, urlopen
# import qrcode
import os 
# from PIL import Image
import json
# import sseclient

url         = "https://legend.lnbits.com"
invoicekey  = ""
interval    = 30
source_name = "djlscomment"

# ------------------------------------------------------------

def update_text():
	global url
	global invoicekey
	global interval
	global source_name

	# source = obs.obs_get_source_by_name(source_name)
	# if source is not None:
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
		# set text to text source - original method
		# obs.obs_data_set_string(settings, "text", data['lnurl'])

		lnurlqrfilelocation = os.path.dirname(__file__) + "/lnurlqr.png"

		# Instead of using qrcode library use this with https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=Example
		qrserverurl = "https://api.qrserver.com/v1/create-qr-code/?size=250x250&margin=10&data=" + data['lnurl']
		qrcoderesponse = urlopen(qrserverurl)
		qrfile = qrcoderesponse.read()
		with open(lnurlqrfilelocation, 'wb') as output:
			output.write(qrfile)

		# set image to image source - new method for DJ Livestream via qrcode library
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

	# obs.obs_source_release(source)

# fetch latest comment from lnbits 
def update_comment():
	global url
	global invoicekey
	global interval
	global source_name

	try:
		livestreamurl = url + "/api/v1/payments"
		req = Request(livestreamurl)
		req.add_header('X-Api-Key', invoicekey)

		response = urlopen(req)
		data = response.read()
		text = data.decode('utf-8')
		print("update_comment got response text " + text)
		invoices = json.loads(text)
		print("invoices[0] " + str(invoices[0]))

		# get comment of last payment
		lastcomment = ""
		for invoice in invoices:
			if invoice["amount"] > 0 and invoice["pending"] == False and invoice["extra"] and invoice["extra"]["comment"] and len(invoice["extra"]["comment"]) > 0:
				print("found an incoming invoice with comment: " + invoice["extra"]["comment"])
				lastcomment = invoice["extra"]["comment"]
				break

		settings = obs.obs_data_create()
		# set text to text source - original method
		print("should be setting the text to " + lastcomment)
		create_text_source(lastcomment)
		# obs.obs_data_set_string(settings, "text", lastcomment)

		# update existing source
		# source = obs.obs_get_source_by_name("djlscomment")
		# obs.obs_source_update(source, settings)
		# obs.obs_data_release(settings)
		# obs.obs_source_release(source)

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

	url         = obs.obs_data_get_string(settings, "url")
	invoicekey  = obs.obs_data_get_string(settings, "invoicekey")
	interval    = obs.obs_data_get_int(settings, "interval")
	source_name = obs.obs_data_get_string(settings, "source")

	obs.timer_remove(update_comment)
	# no need to keep writing the QR code as it does not change!
	# if url != "" and source_name != "":
	print("starting timer to update lnurl-pay comments every " + str(interval) + " seconds")
	obs.timer_add(update_comment, interval * 1000)

def script_defaults(settings):
	obs.obs_data_set_default_int(settings, "interval", 30)

def script_properties():
	props = obs.obs_properties_create()

	obs.obs_properties_add_text(props, "url", "LNBits URL", obs.OBS_TEXT_DEFAULT)
	obs.obs_properties_add_text(props, "invoicekey", "LNBits Invoice Key", obs.OBS_TEXT_DEFAULT)
	obs.obs_properties_add_int(props, "interval", "Update Interval (seconds)", 5, 3600, 1)

	# p = obs.obs_properties_add_list(props, "source", "Text Source", obs.OBS_COMBO_TYPE_EDITABLE, obs.OBS_COMBO_FORMAT_STRING)
	# sources = obs.obs_enum_sources()
	# print("init sources length " + str(len(sources)))
	# if sources is not None:
	# 	for source in sources:
	# 		source_id = obs.obs_source_get_unversioned_id(source)
	# 		# if source_id == "text_gdiplus" or source_id == "text_ft2_source":
	# 		if source_id == "image_source":
	# 			name = obs.obs_source_get_name(source)
	# 			obs.obs_property_list_add_string(p, name, name)

	# 	obs.source_list_release(sources)

	obs.obs_properties_add_button(props, "button", "Add to Scene", refresh_pressed)
	return props

def create_text_source(lastcomment):
	sources = obs.obs_enum_sources()
	print("create_text_source sources length " + str(len(sources)))

	# if sources is not None:
	source = obs.obs_get_source_by_name("djlscomment")
	# print("djlscomment source exists? " + str(source))
	# print(source)
	if source is None:
		print("djlscomment source does not exist so create it")
		current_scene = obs.obs_frontend_get_current_scene()
		scene = obs.obs_scene_from_source(current_scene)

		# set the placeholder text
		settings = obs.obs_data_create()
		obs.obs_data_set_string(settings, "text", lastcomment)

		# obs_source_create_private not
		newsource = obs.obs_source_create("text_ft2_source", "djlscomment", settings)
		obs.obs_scene_add(scene, newsource)
		print("djlscomment comment added to scene")
		obs.obs_scene_release(scene)
		obs.obs_source_release(newsource)
		obs.obs_data_release(settings)
	else:
		print("djlscomment already exists setting the text")
		settings = obs.obs_data_create()
		obs.obs_data_set_string(settings, "text", lastcomment)
		obs.obs_source_update(source, settings)
		obs.obs_data_release(settings)
		obs.source_list_release(sources)

	# obs is insane - thinks a source exists even when removed.
	# djlssource = obs.obs_get_source_by_name("djlscomment")
	# print("by_name " + str(djlssource))
	# if djlssource is None:
	# 	print("djlscomment does NOT exist")
	# else:
	# 	print("djlscomment EXISTS")

	# for source in sources:
	# 	print("1sources loop ")
	# 	print(source)
	# 	source_id = obs.obs_source_get_unversioned_id(source)
	# 	print("2sources loop " + source_id)
	# 	name = obs.obs_source_get_name(source)
	# 	print("3sources loop " + name)

		# if source_id == "text_gdiplus" or source_id == "text_ft2_source":
		# 	name = obs.obs_source_get_name(source)
		# 	print("sources loop " + name)
		# 	# obs.obs_property_list_add_string(p, name, name)

	
import asyncio
import json
from tornado.httputil import HTTPHeaders, ResponseStartLine
from tornado.ioloop import IOLoop
from tornado.routing import PathMatches, Rule, RuleRouter
from tornado.web import HTTPServer

html_head = '<html><head><meta charset="utf-8"></head><body>'
html_tail = '</body></html>'


async def hdd_info(request):
	command_in = request.path.split("/")
	request.connection.write_headers(
		ResponseStartLine(version="HTTP/1.1", code=200, reason="OK"),
		HTTPHeaders({"content-type": "text/html", "content-encoding": "utf-8"})
	)
	hdd_list = await ask_host_cmd("hddlist")
	if command_in[3] == "list":
		request.connection.write(str("<p>" + str(hdd_list)).encode())
	elif command_in[3] in hdd_list:
		cmd = command_in[4]
		info = await ask_host_cmd("hdd " + cmd + " " + command_in[3])
		if request.headers["User-Agent"].find("Mozilla") >= 0:
			if cmd == "smart":
				request.connection.write(pretty_smart(info).encode())
			else:
				request.connection.write(str("<p>" + str(info)).encode())
		else:
			request.connection.write(str("<p>" + str(info)).encode())
	request.connection.finish()


async def get_list(request):
	hdds = await ask_host_cmd("list void")
	request.connection.write_headers(
		ResponseStartLine(version="HTTP/1.1", code=200, reason="OK"),
		HTTPHeaders({"content-type": "text/html", "content-encoding": "utf-8"})
	)
	request.connection.write(str("<p>User-Agent: " + request.headers["User-Agent"]).encode())
	request.connection.write(str("<p>" + request.path).encode())
	request.connection.write(str("<p>" + str(hdds)).encode())
	request.connection.finish()


async def get_status(request):
	pool_name = request.path.split("/")[-1]
	pool_status = await ask_host_cmd("status " + pool_name)
	if pool_status.find("Error") == 0:
		request.connection.write_headers(
			ResponseStartLine(version="HTTP/1.1", code=404, reason="Pool not found"),
			HTTPHeaders(dict())
			)
	else:
		request.connection.write_headers(
			ResponseStartLine(version="HTTP/1.1", code=200, reason="OK"),
			HTTPHeaders({"content-type": "text/html", "content-encoding": "utf-8"})
			)
		cua = request.headers["User-Agent"]
		if cua.find("Mozilla") >= 0 or cua.find("Chrome") >= 0:
			request.connection.write(
				(html_head + pretty_print(pool_status) + html_tail).encode())
		else:
			request.connection.write(pool_status.encode())
	request.connection.finish()


async def get_status_all(request):
	pool_list = await ask_host_cmd("list void")
	request.connection.write_headers(
		ResponseStartLine(version="HTTP/1.1", code=200, reason="OK"),
		HTTPHeaders({"content-type": "text/html", "content-encoding": "utf-8"})
		)
	request.connection.write(html_head.encode())
	for pool in eval(pool_list):
		status = await ask_host_cmd("status " + pool)
		request.connection.write(pretty_print(status).encode())
	request.connection.write(html_tail.encode())
	request.connection.finish()


async def ask_host_cmd(message):
	reader, writer = await asyncio.open_connection("127.0.1.2", 8080)
	writer.write(message.encode())
	data = await reader.read()
	writer.close()
	return data.decode()


def pretty_print(pool_status):
	html_page = ''
	for k, v in eval(pool_status).items():
		html_page += '<p><h4>' + k + '</h4>'
		if k == "config":
			html_page += '<table border=1>'
			for cStr in v.split('\t'):
				html_page += '<tr>'
				for val in cStr.split():
					html_page += '<td>' + val + '</td>'
				html_page += '</tr>'
			html_page += '</table>'
		else:
			html_page += '<br>' + v
	return html_page


def pretty_smart(info_in):
	info = json.loads(info_in)
	html_page = '<html><head><meta charset="utf-8"><title>' + info["device"]["name"] + '</title><body>'
	html_page += '<table border=1>'
	for attribute in info["ata_smart_attributes"]["table"]:
		html_page += '<tr><td>' + str(attribute["id"]) + '</td>'
		html_page += '<td>' + attribute["name"] + '</td>'
		html_page += '<td>' + attribute["raw"]["string"] + '</td></tr>'
	html_page += '</table></body></html>'
	return html_page


def hdd_hdd_callable(request):
	IOLoop.current().spawn_callback(hdd_info, request)


def rule_list_callable(request):
	IOLoop.current().spawn_callback(get_list, request)


def rule_status_callable(request):
	IOLoop.current().spawn_callback(get_status, request)


def rule_status_all_callable(request):
	IOLoop.current().spawn_callback(get_status_all, request)


router = RuleRouter([
	Rule(PathMatches("/sysinfo/hdd/.*"), hdd_hdd_callable),
	Rule(PathMatches("/sysinfo/list"), rule_list_callable),
	Rule(PathMatches("/sysinfo/status"), rule_status_all_callable),
	Rule(PathMatches("/sysinfo/status/.*"), rule_status_callable)
])


server = HTTPServer(router)
server.listen(8888)
IOLoop.current().start()

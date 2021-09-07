import asyncio
import json
import logging
from re import match


async def get_pools():
	proc = await asyncio.create_subprocess_shell(
		"zpool list -H -o name", stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
	stdout, stderr = await proc.communicate()
	logging.info("zpool list retcode " + str(proc.returncode))
	if proc.returncode != 0:
		raise OSError(proc.returncode, "zpool list returned non-zero value.")
	else:
		return stdout.decode().splitlines()


async def get_status(poolname):
	pools = await get_pools()
	if poolname not in pools:
		return "Error. Wrong pool name."
	proc = await asyncio.create_subprocess_shell(
		"zpool status " + poolname, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
	logging.info("zpool returned " + str(proc.returncode))
	stdout, stderr = await proc.communicate()
	answer = dict()
	key = "void"
	for cStr in stdout.decode().splitlines():
		m = match(" *[a-z]+:", cStr)
		if m is not None:
			key = m.group(0)[0:-1]
			answer[key] = cStr[m.end(0):]
		else:
			answer[key] = answer[key] + cStr
	return json.dumps(answer)


async def get_hdd_list():
	proc = await asyncio.create_subprocess_shell(
		"geom disk list", stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
	logging.info("hddlist returned " + str(proc.returncode))
	stdout, stderr = await proc.communicate()
	hdd_list = []
	for cStr in stdout.decode().splitlines():
		if cStr.startswith("Geom name"):
			hdd_list.append(cStr.split()[2])
	return json.dumps(hdd_list)


async def get_hdd_info(action, device):
	cmd_name = "smartctl"
	if action == "info":
		cmd = cmd_name + " -i -j "
	elif action == "smart":
		cmd = cmd_name + " -A -j "
	else:
		return "No action."
	proc = await asyncio.create_subprocess_shell(
		cmd + "/dev/" + device, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
	logging.info("smartctl returned " + str(proc.returncode))
	stdout, stderr = await proc.communicate()
	return stdout.decode()


async def run_command(reader, writer):
	data = await reader.read(80)
	cmd_in = data.decode().split()
	cmd_name = cmd_in[0]
	if cmd_name == "status":
		pool_name = cmd_in[1]
		answer = await get_status(pool_name)
	elif cmd_name == "list":
		answer = await get_pools()
		answer = json.dumps(answer)
	elif cmd_name == "hdd":
		action = cmd_in[1]
		device = cmd_in[2]
		answer = await get_hdd_info(action, device)
	elif cmd_name == "hddlist":
		answer = await get_hdd_list()
	else:
		logging.info("run_command error. " + cmd_name)
		answer = "Wrong command."
	writer.write(answer.encode())
	await writer.drain()
	writer.close()


async def main():
	logging.basicConfig(filename="/var/log/zfscmd.log", format="%(asctime)s %(message)s", level="DEBUG")
	server = await asyncio.start_server(run_command, "127.0.1.2", 8080)
	async with server:
		await server.serve_forever()


asyncio.run(main())

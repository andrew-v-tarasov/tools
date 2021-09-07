#!/usr/bin/env python3.8

from daemons.prefab import run
import json
import hashlib
import libpwman
import logging
from logging.handlers import WatchedFileHandler

from inspect import getmembers
from os import popen
from telegram.error import NetworkError
from telegram.ext import CommandHandler, Updater  # CallbackContext
from time import sleep


class AndyBot(run.RunDaemon):
	logger = ""
	doSendFortunes = False
	sendFortunesInterval = 60
	'''
	@staticmethod
	def send_message(context, chat_id, msg_text):
		return context.bot.send_message(chat_id=chat_id, text=msg_text)
	'''
	def rand_msg_cb(self, context):
		if self.doSendFortunes is False:
			return
		# lo_context = cb_context.job.context[0]
		chat_id = context.job.context[0]
		prev_id = context.job.context[1]
		# self.logger.info("job.bot " + str(job.bot) + "ctx.bot: " + str(context.bot))
		if prev_id is not None:
			context.bot.delete_message(chat_id, prev_id)
		message = popen("fortune /usr/share/games/fortune/limerick").read()
		if len(message) > 0:
			s_mess = context.bot.send_message(chat_id=chat_id, text=message)
			context.job_queue.run_once(self.rand_msg_cb, self.sendFortunesInterval, context=[chat_id, s_mess.message_id])
		else:
			self.logger.error("rand_msg_cb. Got no message from popen.")

	@staticmethod		
	def pw_cb(context):
		chat_id = context.job.context[0]
		mess_id = context.job.context[1]
		context.bot.delete_message(chat_id, mess_id)

	@staticmethod
	def get_db_fname(update):
		db_hash = hashlib.new("sha256")
		user = update.message.from_user.__dict__
		user_name = str(user["username"])
		# first_name = str(user["first_name"])
		user_id = str(user["id"])
		db_hash.update((user_name + user_id).encode("utf-8"))
		db_fn = "/usr/local/var/db/andyprivatebot/" + db_hash.hexdigest() + ".sqlite"
		return db_fn

	def cmd_add(self, update, context):
		cur_cmd = update.message.text.split()
		cname = cur_cmd[1]
		try:
			ctable = cur_cmd[2]
		except IndexError:
			ctable = ""
		db_fn = self.get_db_fname(update)
		libpwman.adduser(db_fn, ctable, cname, 'sha256', '1', '5', 'slt', 'some_text')
		context.bot.send_message(chat_id=update.effective_chat.id, text="Added successfully.")

	def cmd_pw(self, update, context):
		cur_cmd = update.message.text.split()
		try:
			cname = cur_cmd[1]
			ctable = cur_cmd[2]
		except IndexError:
			context.bot.send_message(chat_id=update.effective_chat.id, text="Usage: /pw name table")
			return
		db_hash = hashlib.new("sha256")
		user = update.message.from_user.__dict__
		user_name = str(user["username"])
		# first_name = str(user["first_name"])
		user_id = str(user["id"])
		db_hash.update((user_name + user_id).encode("utf-8"))
		db_fn = "/usr/local/var/db/andyprivatebot/" + db_hash.hexdigest() + ".sqlite"
		users = libpwman.pwusers(db_fn, ctable, cname)
		context.bot.delete_message(update.effective_chat.id, update.message.message_id)
		for user in users:
			s_mess = context.bot.send_message(chat_id=update.effective_chat.id,	text=str(user))
			context.job_queue.run_once(self.pw_cb, 60, context=[s_mess.chat.id, s_mess.message_id])

	def cmd_sf(self, update, context):
		if not hasattr(update.message, "text"):
			self.logger.warning("cmd_sf. Got message with no text.")
			return
		cur_cmd = update.message.text.split()
		cc_len = len(cur_cmd)
		if cc_len != 2 and cc_len != 3:
			context.bot.send_message(chat_id=update.effective_chat.id, text="Usage: /sf start|stop")
			return
		if cur_cmd[1] == "start":
			if cc_len == 3:
				self.sendFortunesInterval = int(cur_cmd[2])
			context.job_queue.run_once(
				self.rand_msg_cb,
				self.sendFortunesInterval,
				context=[update.effective_chat.id, None])
			self.doSendFortunes = True
			message = "Fortunes started, interval " + str(self.sendFortunesInterval)
			context.bot.send_message(chat_id=update.effective_chat.id, text=message)
		else:
			self.doSendFortunes = False

	@staticmethod
	def cmd_fortune(update, context):
		stream = popen("fortune")
		message = stream.read()
		context.bot.send_message(chat_id=update.effective_chat.id, text=message)

	def cmd_mirror(self, update, context):
		user_id = update.message.from_user.__dict__['id']
		self.logger.info("Mirror request from " + str(user_id))
		for cPhoto in context.bot.get_user_profile_photos(user_id).photos[0]:
			context.bot.send_photo(chat_id=update.effective_chat.id, caption=cPhoto.file_id, photo=cPhoto)
			
	def cmd_hello(self, update, context):
		self.logger.debug(update.message.from_user)
		user = update.message.from_user.__dict__
		for key in user:
			m_text = str(key) + ": " + str(user[key])
			context.bot.send_message(chat_id=update.effective_chat.id, text=m_text)

	def error_handler(self, update, context):
		self.logger.debug("Entering gray zone.")
		self.logger.error(msg="Error handing update.", exc_info=context.error)

	def run(self):
		with open('/usr/local/var/db/andyprivatebot/config.json', 'r', encoding='utf-8') as cfg_file:
			config = json.load(cfg_file)
		fh = WatchedFileHandler(config["log"])
		mess_fmt = "%(asctime)s %(levelname)s %(message)s" 
		log_level = eval("logging."+config["loglevel"])
		logging.basicConfig(handlers=[fh], format=mess_fmt, level=log_level)
		self.logger = logging.getLogger(__name__)
		max_retries = int(config["MaxRetries"])
		up = Updater(token=config["token"], use_context=True)
		disp = up.dispatcher
		disp.add_error_handler(self.error_handler)
		for k, v in disp.error_handlers.items():
			self.logger.debug("Error handler " + str(k) + " --- " + str(v))
		for member in [cMem[0] for cMem in getmembers(self) if cMem[0][0:3] == "cmd"]:
			hdl = CommandHandler(member[4:], getattr(self, member))
			disp.add_handler(hdl)
			self.logger.debug("Added handler: " + member[4:])
		do_recon = True
		conn_attempt = 1
		while do_recon:
			try:
				self.logger.debug("Connection attempt " + str(conn_attempt))
				up.start_polling()
				up.idle()
			except ConnectionRefusedError:
				self.logger.error("Connection refused error. ")
			except NetworkError as netErr:
				self.logger.error("Network error. " + netErr.message)
				self.logger.debug("Network error. pause for 3 seconds and restart.")
				up.stop()
				if conn_attempt > max_retries:
					self.logger.error("Max retries exceeded. Exiting.")
					do_recon = False
				else:
					sleep(3)
			except BaseException as e:
				self.logger.error("Unknown error in start polling. " + str(type(e)))
			else:
				do_recon = False
				self.logger.debug("Polling started.")
			finally:
				conn_attempt += 1


def main():
	bot = AndyBot(pidfile="/var/run/andyprivatebot.pid")
	bot.start()


if __name__ == "__main__":
	AndyBot(pidfile="/var/run/andyprivatebot.pid").start()

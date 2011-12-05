
import sys
import socket
import string
import time
import random
import re

HOST="irc.quakenet.org"
PORT=6667
NICK="rouletteboss"
IDENT="roulette"
REALNAME="ROULETTE!!!1"
CHANNEL="#ddrace"
MODE=sys.argv[1]

readbuffer=""

s=socket.socket()
s.connect((HOST, PORT))
s.send("NICK %s\r\n" % NICK)
s.send("USER %s %s * :%s\r\n" % (IDENT, HOST, REALNAME))
s.setblocking(0)

while 1:
	mode = None
	try:
		readbuffer += readbuffer + s.recv(4096)
		temp = readbuffer.split('\n')
		readbuffer = temp.pop()
		for line in temp:
			line = line.rstrip()
			sline = line.split()

			if sline[0] == 'PING':
				s.send('PONG %s\r\n' % sline[1])
			elif sline[1] == '376':
				s.send('JOIN %s\r\n' % CHANNEL)
				s.send('PRIVMSG %s :!roulette\r\n' % CHANNEL)
				print 'logged on (%s)' % NICK
			elif sline[1] == 'PRIVMSG':
				if re.search('.*Nimda3.*\+click\+', line):
					if re.search(NICK, line):
						mode = None
					else:
						mode = 'click'
				elif re.search('.*Nimda3.*\+BANG\+', line):
					if re.search(NICK, line):
						mode = None
					else:
						mode = 'bang'


	except socket.error:
		pass

	if mode == MODE:
		s.send('PRIVMSG %s :!roulette\r\n' % CHANNEL)
		if mode == 'click':
			time.sleep(random.randrange(10,20))
		print 'played (%s)' % NICK

	time.sleep(0.05)


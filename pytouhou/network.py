import socket
from struct import Struct
from select import select
from time import time

from pytouhou.utils.helpers import get_logger

logger = get_logger(__name__)

MSG_STRUCT = Struct('!HHH')

class Network(object):
    def __init__(self, port=8080, dest=None, selected_player=0):
        self.frame = 0
        self.keystate = 0
        self.old_keystate = 0
        self.remote_keystate = 0

        self.selected_player = selected_player

        self.remote_addr = dest
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.sock.bind(('', port))


    def read_message(self):
        message = None

        start_time = time()
        delta = 1./60.

        rlist, _, _ = select([self.sock], [], [], delta)
        while rlist:
            msg, addr = rlist[0].recvfrom(MSG_STRUCT.size)
            # Check whether the message comes from the right address
            if self.frame == 0 or addr == self.remote_addr:
                self.remote_addr = addr

                frame, keystate, old_keystate = MSG_STRUCT.unpack(msg)

                # Check for well-formedness
                if frame in (self.frame, self.frame + 1):
                    message = (frame, keystate, old_keystate)
            else:
                logger.error('Mismatch, got a message from %s, waiting for %s.', self.remote_addr, addr)

            # If no valid message has been read, wait for one as long as possible
            # else, read as much as we can without blocking.
            delta = 0 if message else max(0, 1./60. - (time() - start_time))
            rlist, _, _ = select(rlist, [], [], delta)

        return message


    def send_message(self):
        if self.remote_addr is not None:
            self.sock.sendto(MSG_STRUCT.pack(self.frame, self.keystate, self.old_keystate), self.remote_addr)


    def run_game_iter(self, game, keystate, other_keystate):
        keystates = [other_keystate, other_keystate]
        keystates[self.selected_player] = keystate
        game.run_iter(keystates)


    def run_iter(self, game, keystate):
        if game.frame % 3 == 0:
            # Phase 1: Update game with old data
            self.run_game_iter(game, self.keystate, self.remote_keystate)
        elif game.frame % 3 == 1:
            # Phase 2: Update data, send new data, update game with old data
            self.old_keystate, self.keystate = self.keystate, keystate
            self.frame = game.frame // 3
            self.send_message()
            self.run_game_iter(game, self.old_keystate, self.remote_keystate)
        elif game.frame % 3 == 2:
            # Phase 3: Send new data, get remote data, update game with new data
            self.send_message()
            # Follow one valid update
            message = self.read_message()
            if message:
                frame, keystate, old_keystate = message
                if frame == self.frame:
                    self.remote_keystate = keystate
                elif frame == self.frame + 1:
                    self.remote_keystate = old_keystate
                else:
                    raise Exception #TODO
                self.run_game_iter(game, self.keystate, self.remote_keystate)
            elif game.frame > 2:
                logger.warn('Message not received in time, dropping frame.')



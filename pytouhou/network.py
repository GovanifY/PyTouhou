import socket
import struct
from select import select
import time

MSG_STRUCT = struct.Struct('!IHH')

class Network(object):
    def __init__(self, port=8080, dest=None, selected_player=0):
        self.frame = 0
        self.keystate = 0
        self.old_keystate = 0

        self.selected_player = selected_player

        self.remote_addr = dest
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.sock.bind(('', port))


    def read_messages(self):
        messages = []

        start_time = time.time()
        delta = 1./60.

        rlist, wlist, xlist = select([self.sock], [], [], delta)
        while rlist:
            msg, addr = rlist[0].recvfrom(MSG_STRUCT.size)
            # Check whether the message comes from the right address
            if self.remote_addr is None or addr == self.remote_addr:
                self.remote_addr = addr

                frame, keystate, old_keystate = MSG_STRUCT.unpack(msg)

                # Check for well-formedness
                if frame in (self.frame, self.frame + 1):
                    messages.append((frame, keystate, old_keystate))
            else:
                print('Mismatch', self.remote_addr, addr)

            delta = 0 if messages else max(0, 1./60. - (time.time() - start_time))
            rlist, wlist, xlist = select(rlist, [], [], delta)

            #TODO: self.send_message()

        return messages


    def send_message(self):
        frame, keystate, old_keystate = self.frame, self.keystate, self.old_keystate
        if self.remote_addr is not None:
            self.sock.sendto(MSG_STRUCT.pack(frame, keystate, old_keystate), self.remote_addr)


    def run_game_iter(self, game, keystate, other_keystate):
        keystates = [other_keystate, other_keystate]
        keystates[self.selected_player] = keystate
        game.run_iter(keystates)


    def run_iter(self, game, keystate):
        if self.frame < game.frame:
            self.old_keystate, self.keystate = self.keystate, keystate
            self.frame = game.frame

        self.send_message()

        for frame, keystate, old_keystate in self.read_messages():
            if frame == game.frame:
                self.run_game_iter(game, self.keystate, keystate)
            elif frame == game.frame + 1:
                self.run_game_iter(game, self.keystate, old_keystate)


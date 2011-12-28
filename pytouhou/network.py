import socket
import struct
from select import select

MSG_STRUCT = struct.Struct('!IHHB')

class Network(object):
    def __init__(self, port=8080, dest=None):
        self.frame = 0
        self.keystate = 0
        self.old_keystate = 0

        self.remote_addr = dest
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.sock.setblocking(0)
        self.sock.bind(('', port))


    def read_messages(self):
        messages = []

        rlist, wlist, xlist = select([self.sock], [], [], 0)
        while rlist:
            msg, addr = rlist[0].recvfrom(MSG_STRUCT.size)
            # Check whether the message comes from the right address
            if self.remote_addr is None or addr == self.remote_addr:
                self.remote_addr = addr

                frame, keystate, old_keystate, checksum = MSG_STRUCT.unpack(msg)

                # Check for well-formedness
                if checksum == sum(ord(c) for c in msg[:-1]) & 0xFF:
                    messages.append((frame, keystate, old_keystate, checksum))
            else:
                print('Mismatch', self.remote_addr, addr)

            rlist, wlist, xlist = select(rlist, [], [], 0)

        return messages


    def send_message(self):
        frame, keystate, old_keystate = self.frame, self.keystate, self.old_keystate
        if self.remote_addr is not None:
            checksum = frame + (frame >> 8) + (frame >> 16) + (frame >> 24)
            checksum += keystate + (keystate >> 8)
            checksum += old_keystate + (old_keystate >> 8)
            checksum &= 0xFF
            self.sock.sendto(MSG_STRUCT.pack(frame, keystate, old_keystate, checksum), self.remote_addr)


    def run_iter(self, game, keystate):
        if self.frame < game.frame:
            self.old_keystate, self.keystate = self.keystate, keystate
            self.frame = game.frame

        for frame, keystate, old_keystate, checksum in self.read_messages():
            if frame == game.frame:
                game.run_iter([self.keystate, keystate])
            elif frame == game.frame + 1:
                print('Skipped')
                game.run_iter([self.keystate, old_keystate])
                game.run_iter([self.keystate, keystate])

        self.send_message()


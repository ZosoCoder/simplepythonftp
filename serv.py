#!/user/bin/env python
import socket
import sys
import os
# from pprint import pprint

if len(sys.argv) != 2:
    print "Usage: <PORT NUMBER>"
    exit(-1)

SERVER_ADDRESS = ('127.0.0.1', int(sys.argv[1]))
BUFFER_SIZE = 1024

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(SERVER_ADDRESS)
s.listen(1)

while True:
    print >>sys.stderr, 'waiting for a connection...'
    conn, addr = s.accept()
    print >>sys.stderr, 'Connected to %s:%d' % addr

    try:
        while True:
            print >>sys.stderr, 'Waiting for next command...'
            cmd = conn.recv(BUFFER_SIZE)
            if cmd:
                print >>sys.stderr, 'Command received: %s' % cmd
                if cmd == 'ls':  # Print current directory
                    f = os.listdir('.')
                    conn.sendall(str(len(f)))
                    s = conn.recv(BUFFER_SIZE)
                    print 'Size: %s Sending directory list...' % s
                    for i in f:
                        conn.sendall(i)
                        conn.recv(BUFFER_SIZE)
                    print 'List sent'  # LS command
                elif cmd[:3] == 'get':  # Send specified file
                    params = cmd.split(' ')
                    if len(params) == 2:
                        f = params[1]
                        print >>sys.stderr, 'File: %s' % f
                        try:
                            req_file = open(f, 'rb')
                            data = req_file.read()
                            conn.sendall('ok')
                            print 'File found. Sending file to client.'
                            # Create temp_socket using ephemeral port from client
                            port = int(conn.recv(BUFFER_SIZE))
                            temp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                            temp_socket.connect((addr[0], port))
                            # Send file over temp socket
                            temp_socket.sendall('%d' % len(data))
                            temp_socket.recv(2)
                            temp_socket.sendall(data)
                            temp_socket.recv(2)
                            temp_socket.close()
                            print 'File sent successfully'
                        except IOError:
                            print >>sys.stderr, 'Specified file does not exist'
                            conn.sendall('no')

                    else:
                        print >>sys.stderr, 'Invalid syntax'
                        conn.sendall('Invalid syntax. Usage: get <FILE NAME>')
                # End get response
                elif cmd[:3] == 'put':  # Accept specified file
                    params = cmd.split(' ')
                    if len(params) == 2:
                        conn.sendall('ok')
                        if conn.recv(2) == 'ok':
                            port = int(conn.recv(BUFFER_SIZE))
                            conn.sendall('ok')
                            print 'File transfer has begun, accepting from client.'
                            temp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                            temp_socket.connect((addr[0], port))
                            temp_socket.sendall('ok')
                            file_size = int(temp_socket.recv(BUFFER_SIZE))
                            temp_socket.sendall('ok')
                            # Begin file transfer
                            recvd = ''
                            while file_size > len(recvd):
                                data = temp_socket.recv(BUFFER_SIZE)
                                if not data:
                                    break
                                recvd += data
                            temp_socket.sendall('ok')
                            print 'File data received. Writing to file.'
                            temp_socket.close()
                            # Write data to file
                            file_name = cmd.split(' ')[1].split('/')[-1]
                            new_file = open(file_name, 'wb')
                            new_file.write(recvd)
                            new_file.close()
                            print >>sys.stderr, "File %s received successfully." % file_name
                        else:
                            print 'Client-side error'
                    else:
                        print 'Invalid syntax'
                        conn.sendall('no')
                # End put response
                else:
                    print >>sys.stderr, 'Invalid command: %s' % cmd

            else:
                print >>sys.stderr, 'No data from ', addr
                break
    finally:
        conn.close()

#!/user/bin/env python
import socket
import sys
# from pprint import pprint

if len(sys.argv) != 3:
    print 'Usage: <SERVER NAME> <SERVER PORT>'
    exit(-1)

TCP_IP = socket.getaddrinfo(sys.argv[1], sys.argv[2], 0, 0, socket.SOL_TCP)[0][-1][0]
SERVER_ADDRESS = (TCP_IP, int(sys.argv[2]))
BUFFER_SIZE = 1024

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
print >>sys.stderr, "connecting to %s port %s" % SERVER_ADDRESS
s.connect(SERVER_ADDRESS)

try:
    while True:
        cmd = raw_input('ftp> ')
        s.sendall(cmd)
        if cmd == 'ls':
            size = int(s.recv(BUFFER_SIZE))
            s.sendall(str(size))
            for i in range(size):
                x = s.recv(BUFFER_SIZE)
                s.sendall('ok')
                print x
        elif cmd[:3] == 'get':
            status = s.recv(2)
            if status == 'ok':
                # Create new temp_socket with ephemeral port and send to server
                temp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                temp_socket.bind((SERVER_ADDRESS[0], 0))
                temp_socket.listen(1)
                temp_port = temp_socket.getsockname()[1]
                s.sendall(str(temp_port))
                temp_conn, temp_addr = temp_socket.accept()
                #Begin file transfer
                file_size = int(temp_conn.recv(BUFFER_SIZE))
                temp_conn.send('ok')
                recvd = ''
                while file_size > len(recvd):
                    data = temp_conn.recv(BUFFER_SIZE)
                    if not data:
                        break
                    recvd += data
                temp_conn.sendall('ok')
                temp_conn.close()
                file_name = cmd.split(' ')[1].split('/')[-1]
                new_file = open(file_name, 'wb')
                new_file.write(recvd)
                new_file.close()
                print 'File %s received successfully' % file_name
            else:
                print >>sys.stderr, 'File does not exist.'
        elif cmd[:3] == 'put':
            status = s.recv(2)
            params = cmd.split(' ')
            data = ''
            if status == 'ok':  # Begin transfer sequence
                try:
                    send_file = open(params[1], 'rb')
                    data = send_file.read()
                    s.sendall('ok')
                except IOError:
                    print >>sys.stderr, 'Specified file does not exist.'
                    s.sendall('no')
                    pass
                if data:
                    temp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    temp_socket.bind((SERVER_ADDRESS[0], 0))
                    temp_socket.listen(1)
                    temp_port = temp_socket.getsockname()[1]
                    s.sendall(str(temp_port))
                    s.recv(2)
                    # Establish connection with server using ephemeral port
                    temp_conn, temp_addr = temp_socket.accept()
                    temp_conn.recv(2)
                    # Send file size
                    temp_conn.sendall('%d' % len(data))
                    temp_conn.recv(2)
                    # Begin file transfer
                    temp_conn.sendall(data)
                    temp_conn.recv(2)
                    print 'File sent'
                    temp_conn.close()

            else:
                print >>sys.stderr, 'Usage: put <FILE NAME>'

        elif cmd == 'exit':
            print >>sys.stderr, 'Exiting program'
            s.close()

        elif cmd == '':
            pass
        else:
            print >>sys.stderr, 'Options: ls, get [FILENAME], put [FILENAME]'

finally:
    print >>sys.stderr, 'closing connection'
    s.close()

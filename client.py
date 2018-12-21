import asyncio
import sys
import time

server_list = {'Goloman':11680, 'Hands':11681, 'Holiday':11682, 'Welsh':11683, 'Wilkes':11684}

msg = 'msg not defined'

def main():
    #print(sys.argv[1])
    """
    if len(sys.argv) != 4:
        print('Missing Server or Msg')
        return
    """
    if sys.argv[1] not in server_list:
        print('Invalid Server.')
        return
    # elif sys.argv[2] not in ['IAMAT', 'WHATSAT']:
    #     print('Invalid command.')
    #     return

    #standard input: Server_ID COMMAND Client_ID Location/Radius+UpperBound
    global msg
    if sys.argv[2] == 'IAMAT':
        msg = sys.argv[2] + ' ' + sys.argv[3] + ' ' + str(sys.argv[4]) + ' ' + str(time.time())
    else:
        msg = ''
        for i in range(2, len(sys.argv)):
            msg += str(sys.argv[i])
            msg += ' '
        #msg = sys.argv[2] + ' ' + sys.argv[3] + ' ' + str(sys.argv[4]) + ' ' + str(sys.argv[5])

    print("\n-->Msg sent:\n\n{}".format(msg))

    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(connect(loop))
    except Exception as e:
        print(e)
    loop.close()

async def connect(loop):
    #str1 = str(sys.argv[1])
    reader, writer = await asyncio.open_connection('127.0.0.1', server_list[sys.argv[1]], loop=loop)
    writer.write((msg+"\n").encode())
    data = await reader.read()
    print('\n-->Msg Received:\n\n{}'.format(data.decode()))
    writer.close()

if __name__ == '__main__':
    main()

import aiohttp
import json
import asyncio
import sys
import time

server_list = {'Goloman':11680, 'Hands':11681, 'Holiday':11682, 'Welsh':11683, 'Wilkes':11684}
current_server = ""
client_AT = {}
client_time = {}
client_location = {}
client_time_difference = {}
communication = []

async def handle_connection(reader, writer):
    data = await reader.readline()
    name = data.decode()

    global client_time
    global client_location

    ###Debug
    #print("encoded data is: {}".format(data))
    print("\n#########\ndecoded data is: {}".format(name))
    print("current server is: {}".format(current_server))
    ###

    #log:
    f = open(current_server,"a")
    f.write("Input:\t" + name)
    f.close()

    #Standard respond
    msg_return = "? " + name

    ###
    #Convert the input string into a list:
    temp_list = name.split()

    #Allocate according its command
    if len(temp_list) < 4:
        print('Invalid msg format1')

    elif temp_list[0] != 'COMMUNICATION' and len(temp_list) > 4:
        print('Invalid msg format2')

    #IAMAT
    elif temp_list[0] == 'IAMAT':
        print("IAMAT found")

        #Check format
        format_check = 0
        try:
            location = temp_list[2]
            location_lat = ''
            location_lng = 'location_lng not specified'
            location_lat += location[0]

            ind = 0
            for i in range(1, len(location)):
                #print(location[i])
                if (location[i] == '+' or location[i] == '-') and ind == 0:
                    ind = 1
                    location_lng = ''
                if ind == 0:
                    location_lat += location[i]
                elif ind == 1:
                    location_lng += location[i]
            l1 = float(location_lat)
            l2 = float(location_lng)
            float(temp_list[3])
            if l1>=100 or l1<=-100 or l2>=1000 or l2<=-1000:
                format_check = 1
        except Exception as e:
            # print(e)
            format_check = 1

        if format_check == 1:
            print('Format Check failed')
            # pass
        elif (temp_list[1] in client_time) and (client_time[temp_list[1]] >= temp_list[3]):
                print('IAMAT not updated due to not outdated stamp.')
        else:
            #Update time and location
            client_AT[temp_list[1]] = current_server
            client_time[temp_list[1]] = temp_list[3]
            client_location[temp_list[1]] = temp_list[2]
            time_diff = float(time.time()) - float(temp_list[3])
            sign = ""
            if time_diff>0:
                sign = "+"
            client_time_difference[temp_list[1]] = sign + str(time_diff)
            print('{} updated'.format(temp_list[1]))
            #Form the respond string
            msg_return = "AT " + current_server + ' ' + str(client_time_difference[temp_list[1]]) + ' ' + temp_list[1] + ' ' + client_location[temp_list[1]] + ' ' + client_time[temp_list[1]]

            #Transfer to other servers:
            msg_comm = "COMMUNICATION " + ' ' + temp_list[1] + ' ' + client_location[temp_list[1]] + ' ' + client_time[temp_list[1]] + ' ' + str(client_time_difference[temp_list[1]]) + ' ' + current_server

            global communication
            for server_id in communication:
                print('Attempt to communicate server {}'.format(server_id))

                #log:
                f = open(current_server,"a")
                f.write("To " + server_id + ":\t" + msg_comm + "\n")
                f.close()

                loop1 = asyncio.new_event_loop()
                asyncio.set_event_loop(loop1)
                temp_loop = asyncio.get_event_loop()
                try:
                    temp_loop.run_until_complete(connect(msg_comm, server_id, temp_loop))
                except Exception as e:
                    #print(e)
                    pass
                loop1.close()


    #WHATSAT
    elif temp_list[0] == 'WHATSAT':
        print('WHATSAT found')

        #API:
        API = '_PUT_YOUR_API_HERE_'

        format_check = 0
        try:
            radius = float(temp_list[2])
            upper_bound = int(temp_list[3])
        except Exception as e:
            # print(e)
            format_check = 1

        if format_check == 1:
            print('Format Check failed.')
        else:
            if temp_list[1] not in client_time:
                print('Client info not found in database')
                #pass
            elif radius > 50 or upper_bound > 20:
                print('Over limit of Google API.')
            else:
                # Analyze input:
                location = client_location[temp_list[1]]
                location_lat = ''
                location_lng = 'location_lng not specified'

                location_lat += location[0]

                ind = 0
                for i in range(1, len(location)):
                    if location[i] == '+' or location[i] == '-':
                        ind = 1
                        location_lng = ''
                    if ind == 0:
                        location_lat += location[i]
                    elif ind == 1:
                        location_lng += location[i]
                print("location_lat is {}".format(location_lat))
                print("location_lng is {}".format(location_lng))

                API_url = 'https://maps.googleapis.com/maps/api/place/nearbysearch/json?location=' + location_lat + ',' + location_lng + '&radius=' + str(radius*1000) + '&key=' + API
                print("My API request: " + API_url)
                #Obtain JSON from Google API
                RAW_Str = ""
                async with aiohttp.ClientSession() as session:
                    html = await fetch(session, API_url)
                    RAW_Str = html

                print("Raw API JSON:\n{}".format(RAW_Str))

                #Analyze JSON
                JSON_list = json.loads(RAW_Str)
                new_result = []
                for i in JSON_list["results"]:
                    if upper_bound == 0:
                        break
                    new_result.append(i)
                    upper_bound -= 1

                JSON_list["results"] = new_result
                Google_API_JSON_str = json.dumps(JSON_list, indent=3, separators=(' , ', ' : '))

                #Edit JSON according to upper_bound
                #Google_API_JSON_str = 'TODO: Adjust RAW_Str according to upper_bound'
                msg_return = "AT " + client_AT[temp_list[1]] + ' ' + str(client_time_difference[temp_list[1]]) + ' ' + temp_list[1] + ' ' + client_location[temp_list[1]] + ' ' + client_time[temp_list[1]] + '\n' + Google_API_JSON_str
                print("Returned msg:\n{}".format(msg_return))


    #COMMUNICATION
    elif temp_list[0] == 'COMMUNICATION':
        if (temp_list[1] in client_time) and (client_time[temp_list[1]] >= temp_list[3]):
            print('COMM not updated due to outdated time stamp.')
        else:
            source_server = temp_list[5:]
            print('COMMUNICATION found')
            client_AT[temp_list[1]] = temp_list[5]
            client_time[temp_list[1]] = temp_list[3]
            client_location[temp_list[1]] = temp_list[2]
            client_time_difference[temp_list[1]] = temp_list[4]
            msg_return = current_server + " updated (Msg to source server)"
            print('{} updated'.format(temp_list[1]))

            #Transfer to other servers:
            msg_comm = ''
            for word in temp_list:
                msg_comm += word
                msg_comm += ' '
            msg_comm += current_server
            #global communication
            for server_id in communication:
                if server_id in source_server:
                    print('This is source server: {}'.format(server_id))
                    #pass
                else:
                    print('Attempt to communicate server {}'.format(server_id))

                    #log:
                    f = open(current_server,"a")
                    f.write("To " + server_id + ":\t" + msg_comm + "\n")
                    f.close()

                    loop1 = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop1)
                    temp_loop = asyncio.get_event_loop()
                    try:
                        temp_loop.run_until_complete(connect(msg_comm, server_id, temp_loop))
                    except Exception as e:
                        #print(e)
                        pass
                    loop1.close()
    ###
    else:
        print('Invalid command')


    #log:
    f = open(current_server,"a")
    f.write("Output:\t" + msg_return + "\n")
    f.close()

    #Respond
    writer.write(msg_return.encode())
    await writer.drain()
    writer.close()

#Communication
async def connect(msg_comm, server_id, loop):
    try:
        reader, writer = await asyncio.open_connection('127.0.0.1', server_list[server_id], loop=loop)
        writer.write((msg_comm+"\n").encode())
        data = await reader.readline()
        print('Received: {}'.format(data.decode()))
        writer.close()
    except Exception as e:
        #print(e)
        pass

#Google API
async def fetch(session, url):
    async with session.get(url) as response:
        return await response.text()
"""
async def API(l1, l2, rad):
    async with aiohttp.ClientSession() as session:
        html = await fetch(session, 'https://api.datausa.io/api/?show=geo&sumlevel=nation&required=pop')
        return html
"""


def main():
    ###Debug

    ###
    #Check if server is valid
    if len(sys.argv) < 2:
        print("Missing Server Input.")
        return
    elif len(sys.argv)>2:
        print("Only one input allowed.")
        return
    elif sys.argv[1] not in server_list:
        print("Invalid Server.")
        return

    print("This is server {}".format(sys.argv[1]))

    #Declare current_server in global scope
    global current_server
    current_server = sys.argv[1]

    #log:
    f = open(current_server,"a")
    f.write("\n\nServer started.\n")
    f.close()

    #Add communication servers:
    global communication
    if current_server == 'Goloman':
        communication = ['Hands', 'Holiday', 'Wilkes']
    elif current_server == 'Hands':
        communication = ['Goloman', 'Wilkes']
    elif current_server == 'Holiday':
        communication = ['Goloman', 'Welsh', 'Wilkes']
    elif current_server == 'Welsh':
        communication = ['Holiday']
    elif current_server == 'Wilkes':
        communication = ['Goloman', 'Hands', 'Holiday']

    ###Debug
    print('Valid Server Found: {}.'.format(current_server))
    print('Port assigned: {}.'.format(server_list[current_server]))
    ###

    #Set up server & Close server
    loop = asyncio.get_event_loop()
    server = asyncio.start_server(handle_connection, host='127.0.0.1', port=server_list[current_server], loop=loop)
    server_loop = loop.run_until_complete(server)
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        print('Server Interrupted, Shutting down...')
        #pass

    f = open(current_server,"a")
    f.write("Server closed.\n")
    f.close()
    server_loop.close()
    loop.run_until_complete(server_loop.wait_closed())
    loop.close()


if __name__ == '__main__':
    main()

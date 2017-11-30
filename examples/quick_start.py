import mfclient

if __name__ == '__main__':
    # create connection object (NOTE: You need to substitute with your server details.)
    connection = mfclient.MFConnection(host='localhost', port=8080, transport='http', domain='system',
                                       user='manager', password='change_me')
    try:
        # connect to mediaflux server
        connection.open()

        # run server.version service
        result = connection.execute('server.version')

        # print result xml
        print(result)

        # print server version
        print(result.value('version'))
    finally:
        connection.close()
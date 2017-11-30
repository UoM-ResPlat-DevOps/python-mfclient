import mfclient

""" This example shows how to 
             1) create an asset with content (upload);
             2) get the asset content (download);
"""


def create_asset_with_content(connection, name, namespace, input_file_path):
    """ Create an asset with specified name in the given namespace.

    :param connection: Mediaflux server connection object
    :type connection: mfclient.MFConnection
    :param name: Name of the asset
    :type name: str
    :param namespace: Destination asset namespace
    :type namespace: str
    :param input_file_path: Input file path
    :type input_file_path: str
    :return: id of the asset
    :rtype: long
    """
    # compose service arguments
    w = mfclient.XmlStringWriter('args')
    w.add('namespace', namespace, attributes={'create': True})  # the destination namespace where the asset is created
    w.add('name', name)
    w.push('meta')
    w.push('mf-name')
    w.add('name', name)
    w.pop()
    w.pop()

    input = mfclient.MFInput(path=input_file_path)

    # run asset.create service
    result = connection.execute('asset.create', w.doc_text(), inputs=[input])

    # return asset id
    asset_id = result.long_value('id')
    return asset_id


def get_asset_content(connection, asset_id, output_file_path):
    """ Gets asset metadata.

    :param connection: Mediaflux server connection object
    :type connection: mfclient.MFConnection
    :param asset_id: Asset id
    :type asset_id: long, int or str
    :return:
    """
    # compose service arguments
    w = mfclient.XmlStringWriter('args')
    w.add('id', asset_id)

    output = mfclient.MFOutput(path=output_file_path)

    # run asset.get service
    result = connection.execute('asset.get', w.doc_text())

    asset_metadata = result.element('asset')
    return asset_metadata


##
## NOTE: replace the file paths below
INPUT_FILE = '/tmp/1.txt'
OUTPUT_FILE = '/tmp/2.txt'

if __name__ == '__main__':
    # create connection object (NOTE: You need to substitute with your server details.)
    connection = mfclient.MFConnection(host='localhost', port=8086, transport='http', domain='system',
                                       user='manager', password='change_me')
    try:
        # connect to mediaflux server
        connection.open()

        # create asset
        asset_id = create_asset_with_content(connection, 'Test1', 'test', INPUT_FILE)
        print('created asset %s' % asset_id)

        # get asset content
        asset_metadata = get_asset_content(connection, asset_id, OUTPUT_FILE)
        print('asset content downloaded to: %s' % OUTPUT_FILE)

    finally:
        connection.close()

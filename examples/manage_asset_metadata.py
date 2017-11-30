import mfclient

""" This example shows how to 
             1) create an asset with metadata;
             2) get the asset metadata
             3) change asset metadata
"""


def create_asset(connection, name, namespace, note):
    """ Create an asset with specified name in the given namespace.

    :param connection: Mediaflux server connection object
    :type connection: mfclient.MFConnection
    :param name: Name of the asset
    :type name: str
    :param namespace: Destination asset namespace
    :type namespace: str
    :param note: Note for the asset
    :type note: str
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
    w.push('mf-note')
    w.add('note', note)
    w.pop()
    w.pop()

    # run asset.create service
    result = connection.execute('asset.create', w.doc_text())

    # return asset id
    asset_id = result.long_value('id')
    return asset_id


def get_asset_metadata(connection, asset_id):
    """ Gets asset metadata.

    :param connection: Mediaflux server connection object
    :type connection: mfclient.MFConnection
    :param asset_id: Asset id
    :type asset_id: long, int or str
    :return: asset metadata XmlElement object
    :rtype: mfclient.XmlElement
    """
    # compose service arguments
    w = mfclient.XmlStringWriter('args')
    w.add('id', asset_id)

    # run asset.get service
    result = connection.execute('asset.get', w.doc_text())

    asset_metadata = result.element('asset')
    return asset_metadata


def set_asset_metadata(connection, asset_id, new_name, new_note):
    """ Sets asset metadata

    :param connection: Mediaflux server connection object
    :param asset_id: Asset id
    :type asset_id: long, int or str
    :param new_name: New name for the asset
    :type new_name: str
    :param new_note:  New note for the asset
    :type new_note: str
    :return:
    """
    # compose service arguments
    w = mfclient.XmlStringWriter('args')
    w.add('id', asset_id)
    w.add('name', new_name)
    w.push('meta')
    w.push('mf-name')
    w.add('name', new_name)
    w.pop()
    w.push('mf-note')
    w.add('note', new_note)
    w.pop()
    w.pop()

    # run asset.set service
    result = connection.execute('asset.set', w.doc_text())

if __name__ == '__main__':
    # create connection object (NOTE: You need to substitute with your server details.)
    connection = mfclient.MFConnection(host='localhost', port=8080, transport='http', domain='system',
                                       user='manager', password='change_me')
    try:
        # connect to mediaflux server
        connection.open()

        # create asset
        asset_id = create_asset(connection, 'Test1', 'test', 'Test note 1')
        print('created asset %s' % asset_id)

        # get asset metadata
        asset_metadata = get_asset_metadata(connection, asset_id)
        print('asset metadata:\n%s' % asset_metadata)

        # change asset metadata
        set_asset_metadata(connection,asset_id, 'Test2', 'Test note 2')
        print('updated asset %s' % asset_id)

        # get asset metadata
        asset_metadata = get_asset_metadata(connection, asset_id)
        print('asset metadata:\n%s' % asset_metadata)

    finally:
        connection.close()

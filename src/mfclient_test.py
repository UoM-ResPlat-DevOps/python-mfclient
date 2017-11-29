import mfclient
import unittest

_HOST = 'localhost'
_PORT = 8080
_TRANSPORT = 'http'
_DOMAIN = 'system'
_USER = 'manager'
_PASSWORD = 'XXXXXXXXX'
_INPUT_FILE = '/tmp/test1.upload.txt'
_OUTPUT_FILE = '/tmp/test1.download.txt'


class ServerConnectionTest(unittest.TestCase):
    def setUp(self):
        self._connection = mfclient.MFConnection(host=_HOST, port=_PORT, transport=_TRANSPORT, domain=_DOMAIN,
                                                 user=_USER, password=_PASSWORD)
        self._connection.open()

    def test_asset_create(self):
        print self._connection.execute('server.version')
        id = self._connection.execute('asset.create', args=None,
                                      inputs=[mfclient.MFInput(_INPUT_FILE)]).value('id')
        ae = self._connection.execute('asset.get', '<args><id>' + id + '</id></args>', None,
                                      mfclient.MFOutput(_OUTPUT_FILE)).element('asset')
        print ae
        self._connection.execute('asset.destroy', '<args><id>' + id + '</id></args>')

    def tearDown(self):
        self._connection.close()


if __name__ == '__main__':
    # unittest.main()
    xml = '<a b="123">456</a>'
    e = mfclient.XmlElement.parse(xml)
    print e.value('@b')

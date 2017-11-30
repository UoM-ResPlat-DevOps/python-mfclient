# python-mfclient
Python Mediaflux Client.

### 1. Quick Start

  - 1.1. Check out [mfclient.py](https://raw.githubusercontent.com/UoM-ResPlat-DevOps/python-mfclient/master/src/mfclient.py) from [github](https://github.com/UoM-ResPlat-DevOps/python-mfclient)

  - 1.2. import mfclient module into your python code and use the API to communicate with Mediaflux server.

  - 1.3. simple example below shows how to import the module, connect to mediaflux server and execute a service:
```python
import mfclient

if __name__ == '__main__':
    # create connection object
    connection = mfclient.MFConnection(host='mediaflux.your.org', port=443, transport='https', domain='your-domain',
                                       user='your-username', password='your-password')
    try:
        # connect to mediaflux server
        connection.open()

        # run server.version service
        result = connection.execute('server.version')

        # print result xml
        print(result)

        # print Mediaflux server version
        print(result.value('version'))
    finally:
        connection.close()
```

### 2. Examples

  - 2.1. [quick-start example](https://github.com/UoM-ResPlat-DevOps/python-mfclient/blob/master/examples/quick_start.py)
  - 2.2. [create asset with metadata](https://github.com/UoM-ResPlat-DevOps/python-mfclient/blob/master/examples/manage_asset_metadata.py)
  - 2.3. [get asset metadata](https://github.com/UoM-ResPlat-DevOps/python-mfclient/blob/master/examples/manage_asset_metadata.py)
  - 2.4. [change asset metadata](https://github.com/UoM-ResPlat-DevOps/python-mfclient/blob/master/examples/manage_asset_metadata.py)
  - 2.5. [create asset with content (upload a file as an asset)](https://github.com/UoM-ResPlat-DevOps/python-mfclient/blob/master/examples/manage_asset_with_content.py)
  - 2.6. [get asset content (download asset content to local file system)](https://github.com/UoM-ResPlat-DevOps/python-mfclient/blob/master/examples/manage_asset_with_content.py)
  
  * See [more exmamples](https://github.com/UoM-ResPlat-DevOps/python-mfclient/tree/master/examples)

### 3. API Documentation
  * See [API documentation on readthedocs.io](http://python-mfclient.readthedocs.io/en/latest/source/mfclient.html#module-mfclient)

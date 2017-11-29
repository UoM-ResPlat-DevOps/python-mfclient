# python-mfclient
Python Mediaflux Client.

### 1. Quick Start

```python
import mfclient
# create connection object
connection = mfclient.MFConnection(host='mediaflux.your.org', port=443, transport='https', domain='your-domain', user='your-username', password='your-password')
try:
    # connect to mediaflux server
    connection.open()
    
    # run server.version service
    result = connection.execute('server.version')
    
    # print server version
    print(result.value('version')
finally:
    connection.close()
```

### 2. Examples

### 3. [API Documentation](http://python-mfclient.readthedocs.io/en/latest/source/mfclient.html#module-mfclient)

import base64
import datetime
import os
import re
import socket
import ssl
import struct
import threading
import time
import urllib
import xml.etree.ElementTree as ElementTree


##############################################################################
# XML                                                                        #
##############################################################################

def _get_xml_declaration(version='1.0', encoding='UTF-8'):
    """Gets XML declaration (for the specified version and encoding).

    :param version: XML version
    :param encoding: encoding
    :return: XML declaration
    :rtype: str

    """
    return '<?xml version="' + version + '" encoding="' + encoding + '"?>'


class XmlElement(object):
    """The class for XML element. It wraps ElementTree.Element object.
    It has methods to resolve XML element(s) and value(s) for the specified XPATH string.
    """

    def __init__(self, elem=None, name=None, attrib=None, value=None):
        """

        :param elem: ElementTree.Element object to wrap
        :type elem: ElementTree.Element
        :param name: name/tag of the element
        :type name: str
        :param attrib: attributes of the element
        :type attrib: dict
        :param value: value of the element
        """
        if elem is not None:
            if name is not None:
                raise ValueError("Expecting 'elem' or 'name'. Found both.")
            if not isinstance(elem, ElementTree.Element):
                raise TypeError("'elem' must be an instance of xml.etree.ElementTree.Element.")
            self._elem = elem
        else:
            if name is None:
                raise ValueError("Expecting 'elem' or 'name'. Found none.")
            if attrib is None:
                attrib = {}
            else:
                if isinstance(attrib, dict):  # dictionary
                    attrib = {str(k): str(attrib[k]) for k in attrib.keys()}
                else:
                    raise ValueError("'attrib' must be an instance of dictionary.")
            idx = name.find(':')
            if idx >= 0:
                ns = name[0:idx]
                self._elem = ElementTree.Element('{' + ns + '}' + name[idx + 1:], attrib=attrib)
            else:
                self._elem = ElementTree.Element(name, attrib=attrib)
            if value is not None:
                self._elem.text = str(value)
        self._nsmap = {}
        self._register_namespace(self._elem)

    def _register_namespace(self, elem):
        """Register the namespace of the element if exists.

        :param elem: the element to register its namespace
        :return:
        """
        tag = elem.tag
        if tag.startswith('{'):
            ns = tag[1:tag.rfind('}')]
            self._nsmap[ns] = ns
        for subelem in list(elem):
            self._register_namespace(subelem)

    @property
    def tag(self):
        """ The tag of the element.

        :return: the tag of the element
        :rtype: str
        """
        if self._elem.tag.startswith('{'):
            idx = self._elem.tag.find('}')
            ns = self._elem.tag[1:idx]
            name = self._elem.tag[idx + 1:]
            return ns + ':' + name
        else:
            return self._elem.tag

    @property
    def attrib(self):
        """Get attributues of the element.

        :return: attributes of the element
        :rtype: dict

        """
        return self._elem.attrib.copy()

    @property
    def text(self):
        """ The text value of the element.

        :return: value of the element
        :rtype: str

        """
        return self._elem.text

    def name(self):
        """The name/tag of the element.

        :return: the name/tag of the element
        :rtype: str
        """
        return self.tag

    def attributes(self):
        """Gets the attributes of the element.

        :return: the attributes of the element
        :rtype: dictionary

        """
        return self.attrib

    def attribute(self, name):
        """Gets the value of the specified attribute.

        :param name: name of the attribute
        :return: value of the attribute
        :rtype: str

        """
        return self.attrib.get(name)

    def set_attribute(self, name, value):
        """ Sets the value of the specified attribute.

        :param name: the name of the attribute
        :param value: the value for the attribute
        :return:

        """
        self._elem.attrib.set(name, str(value))

    def _contains_unregistered_namespace(self, xpath):
        """ Checks if the xpath string contains any unregistered namespaces.

        :param xpath: the xpath string
        :return: True if the xpath string contains namespace that is not registered. False if none.
        :rtype: bool

        """
        nss = re.findall(r'[$/]?([^/]+?):', xpath)
        if nss:
            for ns in nss:
                if ns not in self._nsmap:
                    return True
        return False

    def value(self, xpath=None, default=None):
        """Gets the value at the specified xpath. If xpath argument is not given, return the value of the current element.

        :param xpath: xpath
        :type xpath: str
        :param default: value to return if node does not exist at the specified xpath
        :type default: str
        :return: value of the given xpath, or value of the element if xpath is not given.
        :rtype: str

        """
        if xpath is None:
            return self._elem.text
        else:
            if self._contains_unregistered_namespace(xpath):
                return None
            if xpath and xpath.startswith('@'):
                return self._elem.attrib.get(xpath[1:], default)
            idx = xpath.rfind('/@')
            if idx == -1:
                return self._elem.findtext(xpath, default=default, namespaces=self._nsmap)
            else:
                se = self._elem.find(xpath[:idx], namespaces=self._nsmap)
                if se is not None:
                    value = se.attrib.get(xpath[idx + 2:])
                    return value if value is not None else default

    def int_value(self, xpath=None, default=None, base=10):
        """Gets the integer value at the specified xpath. If xpath argument is not given, return the value of the
        current element.

        :param xpath: xpath
        :type xpath: str
        :param default: value to return if node does not exist at the specified xpath
        :type default: int
        :param base: the radix base to use.
        :type base: int
        :return: value of the given xpath, or value of the element if xpath is not given.
        :rtype: int

        """
        assert default is None or isinstance(default, int)
        value = self.value(xpath)
        if value is not None:
            return int(value, base)
        else:
            return default

    def float_value(self, xpath=None, default=None):
        """Gets the float value at the specified xpath. If xpath argument is not given, return the value of the current element.

        :param xpath: xpath
        :type xpath: str
        :param default: value to return if node does not exist at the specified xpath
        :type default: float
        :return: value of the given xpath, or value of the element if xpath is not given.
        :rtype: float

        """
        assert default is None or isinstance(default, float)
        value = self.value(xpath)
        if value is not None:
            return float(value)
        else:
            return default

    def boolean_value(self, xpath=None, default=None):
        """Gets the bool value at the specified xpath. If xpath argument is not given, return the value of the current element.

        :param xpath: xpath
        :type xpath: str
        :param default: value to return if node does not exist at the specified xpath
        :type default: bool
        :return: value of the given xpath, or value of the element if xpath is not given.
        :rtype: bool

        """
        assert default is None or isinstance(default, bool)
        value = self.value(xpath)
        if value is not None:
            return value.lower() in ('yes', 'true', '1')
        else:
            return default

    def date_value(self, xpath=None, default=None):
        """Gets the datetime value at the specified xpath. If xpath argument is not given, return the value of the
        current element.

        :param xpath: xpath
        :type xpath: str
        :param default: value to return if node does not exist at the specified xpath
        :type default: datetime.datetime
        :return: value of the given xpath, or value of the element if xpath is not given.
        :rtype: datetime.datetime

        """
        assert default is None or isinstance(default, datetime.datetime)
        value = self.value(xpath)
        if value is not None:
            return time.strptime(value, '%d-%b-%Y %H:%M:%S')
        else:
            return default

    def set_value(self, value):
        """Sets value of the element.

        :param value: the element value.
        :return:

        """
        if value is not None:
            if isinstance(value, datetime.datetime):
                self._elem.text = time.strftime('%d-%b-%Y %H:%M:%S', value)
            elif isinstance(value, bool):
                self._elem.text = str(value).lower()
            else:
                self._elem.text = str(value)

    def values(self, xpath=None):
        """Returns values for the given xpath.

        :param xpath: xpath
        :type xpath: str
        :return: values for the give xpath
        :rtype: list

        """
        if xpath is None:
            if self._elem.text is not None:
                return [self._elem.text]
            else:
                return None
        if self._contains_unregistered_namespace(xpath):
            return None
        idx = xpath.rfind('/@')
        if idx == -1:
            ses = self._elem.findall(xpath, self._nsmap)
            if ses is not None:
                return [se.text for se in ses]
        else:
            ses = self._elem.findall(xpath[:idx], self._nsmap)
            if ses is not None:
                return [se.attrib.get(xpath[idx + 2:]) for se in ses]

    def element(self, xpath=None):
        """Returns the element identified by the given xpath.

        :param xpath: xpath
        :type xpath: str
        :return: the element identified by the given xpath
        :rtype: XmlElement

        """
        if xpath is None:
            ses = list(self._elem)
            return XmlElement(elem=ses[0]) if ses else None
        else:
            if self._contains_unregistered_namespace(xpath):
                return None
            idx = xpath.rfind('/@')
            if idx != -1:
                raise ValueError('Invalid element xpath: ' + xpath)
            se = self._elem.find(xpath, self._nsmap)
            if se is not None:
                return XmlElement(elem=se)

    def elements(self, xpath=None):
        """Returns the elements identified by the given xpath.

        :param xpath: xpath
        :type xpath: str
        :return: the elements identified by the given xpath
        :rtype: list

        """
        if xpath is None:
            ses = list(self._elem)
            if ses:
                return [XmlElement(elem=se) for se in ses]
        else:
            if self._contains_unregistered_namespace(xpath):
                return None
            idx = xpath.rfind('/@')
            if idx != -1:
                raise SyntaxError('invalid element xpath: ' + xpath)
            ses = self._elem.findall(xpath, self._nsmap)
            if ses:
                return [XmlElement(elem=se) for se in ses]
            else:
                return None

    def add_element(self, elem, index=None):
        assert elem is not None and isinstance(elem, (ElementTree.Element, XmlElement))
        if isinstance(elem, ElementTree.Element):
            if index is None:
                self._elem.append(elem)
            else:
                self._elem.insert(index, elem)
            self._register_namespace(elem)
        elif isinstance(elem, XmlElement):
            self.add_element(elem._elem, index)

    def tostring(self):
        """Returns the XML string of this element.

        :return: the XML string of the element.
        :rtype: str

        """
        for ns in self._nsmap.keys():
            ElementTree.register_namespace(ns, self._nsmap.get(ns))
        te = ElementTree.Element('temp')
        te.append(self._elem)
        ts = ElementTree.tostring(te)
        ts = ts[ts.find('>') + 1:len(ts) - 7]
        for nsk in self._nsmap.keys():
            nsv = self._nsmap.get(nsk)

            def replacement(match):
                token = match.group(0)
                if token.endswith(' '):  # ends with space
                    return token + 'xmlns:' + nsk + '="' + nsv + '" '
                else:  # ends with >
                    return token[0:-1] + ' xmlns:' + nsk + '="' + nsv + '">'

            ts = re.sub(r'<' + nsk + ':[a-zA-Z0-9_-]+[\s>]', replacement, ts)
        return ts

    def __str__(self):
        return self.tostring()

    def __getitem__(self, index):
        se = self._elem.__getitem__(index)
        return XmlElement(se) if se is not None else None

    def __len__(self):
        return self._elem.__len__()

    @classmethod
    def parse(cls, source):
        """Parses the specified XML document string or file, which must contains a well formed XML document.

        :param source: the source XML string or file.
        :type source: str or file object
        :return:
        """
        assert source is not None
        if os.path.isfile(source):  # text is a file
            tree = ElementTree.parse(source)
            if tree is not None:
                root = tree.getroot()
                if root is not None:
                    return XmlElement(elem=root)
            else:
                raise ValueError('Failed to parse XML file: ' + source)
        else:
            return XmlElement(ElementTree.fromstring(str(source)))


def _process_xml_attributes(name, attributes):
    attrib = {}
    # add namespace attribute
    idx = name.find(':')
    if idx >= 0:
        ns = name[0:idx]
        ns_attr = 'xmlns:' + ns
        if ns_attr not in attrib:
            attrib[ns_attr] = ns
    # conver to str and remove attribute with value==None
    if attributes is not None:
        for name in attributes.keys():
            value = attributes[name]
            if value is not None:
                attrib[str(name)] = str(value)
    return attrib


class XmlStringWriter(object):
    """The XML string writer is a high-speed creator for XML documents that encodes the output as a string of UTF-8
    characters.

    """

    def __init__(self, root=None):
        """

        :param root: the name of the root element
        :type root: str
        """
        self._stack = []
        self._items = []
        if root is not None:
            self.push(str(root))

    def doc_text(self):
        """Returns the complete XML document string, automatically popping active elements.

        :return: the complete XML document string
        :rtype: str
        """
        self.pop_all()
        return ''.join(self._items)

    def doc_elem(self):
        """ Returns the complete XML document element, authomatically popping active elements.

        :return: the complement XML document element.
        :rtype: XmlElement
        """
        return XmlElement.parse(self.doc_text())

    def push(self, name, attributes=None):
        """Pushes an element with attributes and value onto the stack.

        :param name: The name of the element
        :type name: str
        :param attributes: The attributes of the element
        :type attributes: dict
        :return:
        """
        attributes = _process_xml_attributes(name, attributes)
        self._stack.append(name)
        self._items.append('<')
        self._items.append(name)
        for a in attributes.keys():
            self._items.append(' ')
            self._items.append(a)
            self._items.append('="')
            self._items.append(attributes[a])
            self._items.append('"')
        self._items.append('>')

    def pop(self):
        """Pops the current element from the stack.

        :return:
        """
        name = self._stack.pop()
        self._items.append('</')
        self._items.append(name)
        self._items.append('>')

    def pop_all(self):
        """Pops all the open elements.

        :return:
        """
        while len(self._stack) > 0:
            self.pop()

    def add(self, name, value, attributes=None):
        """ Add the element with specified value, and attributes.

        :param name: name of the element
        :type name: str
        :param value: value of the element
        :param attributes: attributes of the element
        :type attributes: dict
        :return:
        """
        attributes = _process_xml_attributes(name, attributes)
        self._items.append('<')
        self._items.append(name)
        for a in attributes.keys():
            self._items.append(' ')
            self._items.append(a)
            self._items.append('="')
            self._items.append(attributes[a])
            self._items.append('"')
        self._items.append('>')
        self._items.append(str(value))
        self._items.append('</')
        self._items.append(name)
        self._items.append('>')

    def add_element(self, element, parent=True):
        """Adds the given element, associated attributes and all sub-elements.

        :param element: the element. Can be XmlElement object, ElementTree.Element object or str of XML element.
        :type element: XmlElement or ElementTree.Element or str
        :param parent: Controls whether the element itself should be written. If true, then the element is included,
                        otherwise, only sub-elements are written.
        :type parent: bool
        :return:
        """
        if element is None:
            raise ValueError('element is not specified.')
        if isinstance(element, ElementTree.Element) or isinstance(element, XmlElement):
            if parent is True:
                if isinstance(element, ElementTree.Element):
                    self._items.append(XmlElement(element).tostring())
                else:
                    self._items.append(element.tostring())
            else:
                for sub_element in list(element):
                    self.add_element(sub_element, parent=True)
        else:
            elem = XmlElement.parse(str(element))
            self.add_element(elem, parent)


class XmlDocWriter(object):
    """This class wraps ElementTree.TreeBuilder to build a XML document.

    """

    def __init__(self, root=None):
        """

        :param root: The name/tag of the root element.
        :type root: str
        """
        self._stack = []
        self._tb = ElementTree.TreeBuilder()
        if root is not None:
            self.push(root)

    def doc_text(self):
        """Returns the complete XML document string, automatically popping active elements.

        :return: the complete XML document string.
        :rtype: str

        """
        return str(self.doc_elem())

    def doc_elem(self):
        """ Returns the complete XML document element, authomatically popping active elements.

        :return: the complement XML document element.
        :rtype: XmlElement
        """
        self.pop_all()
        return XmlElement(self._tb.close())

    def push(self, name, attributes=None):
        """Pushes an element with attributes and value onto the stack.

        :param name: The name of the element
        :type name: str
        :param attributes: The attributes of the element
        :type attributes: dict
        :return:
        """
        attributes = _process_xml_attributes(name, attributes)
        self._stack.append(name)
        self._tb.start(name, attributes)

    def pop(self):
        """Pops the current element from the stack.

        :return:
        """
        name = self._stack.pop()
        if name is not None:
            self._tb.end(name)

    def pop_all(self):
        """Pops all the open elements.

        :return:
        """
        while len(self._stack) > 0:
            self.pop()

    def add(self, name, value, attributes=None):
        """ Add the element with specified value, and attributes.

        :param name: name of the element
        :type name: str
        :param value: value of the element
        :param attributes: attributes of the element
        :type attributes: dict
        :return:
        """
        attributes = _process_xml_attributes(name, attributes)
        self._tb.start(name, attributes)
        self._tb.data(str(value))
        self._tb.end(name)

    def add_element(self, element, parent=True):
        """Adds the given element, associated attributes and all sub-elements.

        :param element: the element
        :type element: XmlElement or ElementTree.Element
        :param parent: Controls whether the element itself should be written. If true, then the element is included,
                        otherwise, only sub-elements are written.
        :type parent: bool
        :return:
        """
        if element is None:
            raise ValueError('element is not specified.')
        if isinstance(element, ElementTree.Element) or isinstance(element, XmlElement):
            if parent is True:
                self._tb.start(element.tag, element.attrib)
                if element.text is not None:
                    self._tb.data(element.text)
            for sub_element in list(element):
                self.add_element(sub_element, parent=True)
            if parent is True:
                self._tb.end(element.tag)
        else:
            self.add_element(ElementTree.fromstring(str(element)), parent)


##############################################################################
# Mediaflux Client                                                           #
##############################################################################

BUFFER_SIZE = 8192
RECV_TIMEOUT = 10.0
SVC_URL = '/__mflux_svc__/'


class MFConnection(object):
    """ Mediaflux server connection class.
    """

    _SEQUENCE_GENERATOR = 0
    _SEQUENCE_ID = 0
    _LOCK = threading.RLock()

    @classmethod
    def sequence_generator(cls):
        with cls._LOCK:
            return cls._SEQUENCE_GENERATOR

    @classmethod
    def set_sequence_generator(cls, sequence_generator):
        with cls._LOCK:
            cls._SEQUENCE_GENERATOR = sequence_generator

    @classmethod
    def _next_sequence_id(cls):
        with cls._LOCK:
            cls._SEQUENCE_ID += 1
            return cls._SEQUENCE_ID

    def __init__(self, host, port, transport='https', proxy=None, domain=None, user=None, password=None, token=None,
                 token_type=None, timeout=None,
                 recv_timeout=RECV_TIMEOUT, app=None, protocols=None, compress=False, cookie=None):
        """ Constructor.

        :param host: Mediaflux server host address
        :type host: str
        :param port: Mediaflux server port
        :type port: int
        :param transport: Mediaflux server transport protocol
        :type transport: str
        :param proxy: Proxy server details, in a tuple (host, port, username, password)
        :type proxy: tuple
        :param domain: Mediaflux authentication domain
        :type domain: str
        :param user: Mediaflux username
        :type user: str
        :param password: Mediaflux password
        :type password: str
        :param token: Mediaflux secure identity token
        :type token: str
        :param token_type: Type of secure identity token
        :type token_type: str
        :param timeout: socket timeout
        :type timeout: float
        :param recv_timeout: receive timeout. Defaults to 10.0 seconds
        :type recv_timeout: float
        :param app: application name. Optional, can be used to restrict the secure identity tokens.
        :type app: str
        :param protocols: optional
        :type protocols:
        :param compress: compress the packets.
        :type compress: bool
        :param cookie:
        :type cookie: str
        """
        self._host = host
        self._port = port
        self._transport = transport
        self._proxy = proxy
        self._domain = domain
        self._user = user
        self._password = password
        self._token = token
        self._token_type = token_type
        self._timeout = timeout
        self._recv_timeout = recv_timeout
        self._app = app
        self._protocols = protocols
        self._compress = compress
        self._cookie = cookie
        self._session = None
        self._session_id = None
        self._session_timeout = -1
        self._last_send_time = -1
        self._lock = threading.RLock()
        self._sock = None

    @property
    def host(self):
        """ Mediaflux server host address
        """
        return self._host

    @property
    def port(self):
        """ Mediaflux server port
        """
        return self._port

    @property
    def transport(self):
        """ Mediaflux transport protocol. Selection of http or https
        """
        return self._transport

    @property
    def encrypt(self):
        """ Is transport encrypted with https?
        """
        return self._transport.lower() == 'https'

    @property
    def http(self):
        """ Is transport http?
        """
        return self._transport.startswith('http')

    @property
    def proxy(self):
        """ Proxy server details in a tuple (host, port, username, password)
        """
        return self._proxy

    @property
    def session(self):
        """ Mediaflux session code. Only available after authentication
        """
        return self._session

    @property
    def app(self):
        """ Application name. Can be used to restrict secure identity code.
        """
        return self._app

    @property
    def domain(self):
        """ Mediaflux authentication domain
        """
        return self._domain

    @property
    def user(self):
        """ Mediaflux username
        """
        return self._user

    @property
    def token(self):
        """ Mediaflux secure identity token. If given, it will be used for authentication
        """
        return self._token

    @property
    def protocols(self):
        return self._protocols

    @property
    def timeout(self):
        return self._timeout

    @property
    def recv_timeout(self):
        """ Receive timeout. Defaults to 10.0 seconds
        """
        return self._recv_timeout

    def _open_socket(self):
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.settimeout(self._timeout)
        if self.proxy is not None:
            (proxy_host, proxy_port, proxy_user, proxy_password) = self.proxy
            self._sock.connect((proxy_host, proxy_port))
            f = self._sock.makefile('r+')
            try:
                f.write('CONNECT ' + self.host + ':' + self.port + ' HTTP/1.1\r\n')
                f.write('Host: ' + self.host + ':' + self.port + '\r\n')
                if proxy_user is not None and proxy_password is not None:
                    f.write(
                        'Proxy-Authorization: Basic ' + base64.b64encode(
                            proxy_user + ':' + proxy_password) + '\r\n')
                f.write('\r\n')
                f.flush()
                line = f.readline().rstrip('\r\n').strip()
                if len(line) == 0 or not line.startswith('HTTP/') or line.count(' ') < 2:
                    raise ExHttpResponse('Invalid HTTP response: ' + line)
                (version, status, message) = line.split()
                version = version[5:]
                if status != '200':
                    raise ExHttpResponse('Unexpected HTTP ' + version + ' response: ' + status + ' ' + message)
            except:
                f.close()
                self._sock.close()
                raise  # re-throw exception
            finally:
                f.close()
        else:
            self._sock.connect((self.host, self.port))
        if self.encrypt:
            self._sock = ssl.wrap_socket(self._sock)

    def _close_socket(self):
        if self._sock is not None:
            self._sock.close()
            self._sock = None

    def open(self):
        """ Connect to mediaflux server and authenticate
        """
        if not (self._domain and self._user and self._password) and not self._token and not self._session:
            raise ValueError('Cannot open connection: No user credentials or secure identity token is specified.')
        with self._lock:
            w = XmlStringWriter('args')
            if self._app is not None:
                w.add('app', self._app)
            w.add('host', self.host)
            if self._domain and self._user and self._password:
                w.add('domain', self._domain)
                w.add('user', self._user)
                w.add('password', self._password)
            elif self._token:
                w.add('token', self._token)
            else:
                w.add('sid', self._session)
            rxe = self.execute('system.logon', args=w.doc_text())
            self._session = rxe.value('session')
            self._session_id = rxe.int_value('session/@id')
            self._session_timeout = rxe.int_value('session/@timeout', 600000) * 1000
            self._last_send_time = int(round(time.time() * 1000))
            return self._session

    def close(self):
        """ Disconnect from server
        """
        if not self._session:
            return
        with self._lock:
            try:
                self.execute('system.logoff')
            finally:
                self._session = None

    def execute(self, service, args=None, inputs=None, outputs=None, route=None, emode=None):
        """ Execute the specified service on Mediaflux server.
        :param service: name of the service
        :type service: str
        :param args: service arguments. Can be str of XML element, XmlElement object or ElementTree.Element object
        :type args: str or XmlElement or ElementTree.Element
        :param inputs: list of service inputs (MFInput objects)
        :type inputs: list of MFInput objects
        :param outputs: list of service outputs (MFOutput objects)
        :type outputs: list of MFOutput objects
        :param route: server route. Used for distributed service calls in federated server environment.
        :type route: str
        :param emode: execute mode for distributed service calls. select from 'distributed-first' or 'distributed-all'
        :type emode: str
        :return: service result XML (XmlElement object).
        :rtype: XmlElement
        """
        sgen = MFConnection.sequence_generator()
        seq = MFConnection._next_sequence_id()
        # create request message
        request = _MFRequest(sgen, seq, service, args, inputs, outputs, route, emode, self._session,
                             (self._token, self._token_type), self._app, self._protocols, self._compress)
        try:
            # open socket
            self._open_socket()
            # send http header
            self._send_http_header(request.length)
            # send http request
            request.send(self._sock)
            # receive http response
            response = _MFResponse(outputs)
            response.recv(self._sock)
            if response.error is not None:
                raise ExHttpResponse(str(response.error))
            return response.result
        finally:
            self._close_socket()

    def _send_http_header(self, content_length):
        header = 'POST '
        if self.encrypt:
            header += 'https://'
        else:
            header += 'http://'
        if self.host.find(':') != -1:
            header = header + '[' + self.host + ']' + ':' + self.port + SVC_URL + ' HTTP/1.1\r\n'
        else:
            header = header + self.host + ':' + str(self.port) + SVC_URL + ' HTTP/1.1\r\n'
        header += 'Host: ' + self.host + ':' + str(self.port) + '\r\n'
        header += 'User-Agent: Mediaflux/3.0\r\n'
        header += 'Connection: keep-alive\r\n'
        header += 'Keep-Alive: 300\r\n'
        if self.proxy is not None:
            header += 'Proxy-Connection: keep-alive\r\n'
            (proxy_host, proxy_port, proxy_user, proxy_password) = self.proxy
            if proxy_user:
                header += 'Proxy-Authorization: Basic ' + base64.b64encode(proxy_user + '.' + proxy_password) + '\r\n'
        if self._cookie is not None:
            header += 'Cookie: ' + self._cookie + '\r\n'
        header += 'Content-Type: application/mflux\r\n'
        if content_length == -1:
            header += 'Transfer-Encoding: chunked\r\n'
        else:
            header += 'Content-Length: ' + str(content_length) + '\r\n'
        header += '\r\n'
        self._sock.sendall(header)


class MFInput(object):
    """ Mediaflux service input class.
    """

    def __init__(self, path=None, url=None, mime_type=None, calc_csum=False):
        """ Constructor

        :param path: Input file path
        :type path: str
        :param url: Input file url
        :type url: str
        :param mime_type: Input file mime type
        :type mime_type: str
        :param calc_csum: Calculate crc32 checksum before consumed by the service. Defaults to False.
        :type calc_csum: bool
        """
        self._checksum = None
        self._path = path
        self._url = url
        self._type = mime_type
        self._length = -1
        if url:
            resp = None
            try:  # probe the mime type and length
                resp = urllib.urlopen(url).info()
                self._type = resp.type
                self._length = long(resp.getheaders('Content-Length')[0])
            except:
                pass
            finally:
                if resp is not None:
                    resp.close()
        elif path:
            self._length = os.path.getsize(path)
            if calc_csum:
                self._checksum = _crc32(path)
        else:
            raise ValueError("path or url argument must be specified")

    def type(self):
        """ MIME type of the input file
        :return: MIME type of the input file
        :rtype: str
        """
        return self._type

    def set_type(self, mime_type):
        """ set MIME type of the input

        :param mime_type: MIME type
        :return:
        """
        self._type = mime_type

    def length(self):
        """ Length of the input file
        :return: Length of the input file
        :rtype: long
        """
        return self._length

    def url(self):
        return self._url

    def path(self):
        """ Input file path
        :return: input file path
        :rtype: str
        """
        return self._path

    def checksum(self):
        """ CRC32 checksum of the input file
        :return: CRC32 checksum of the input file
        :rtype: int
        """
        return self._checksum

    def set_checksum(self, checksum):
        """ set CRC32 checksum of the input file

        :param checksum: CRC32 checksum
        :type checksum: int
        :return:
        """
        self._checksum = checksum


class MFOutput(object):
    """ Mediaflux service output class.
    """

    def __init__(self, path=None, file_obj=None):
        """ Constructor.

        :param path: Output file path
        :type path: str
        :param file_obj: Output file object
        :type file_obj: file
        """
        self._path = os.path.abspath(path) if path else None
        self._file_obj = file_obj
        self._mime_type = None

    def file_object(self):
        """ output file object
        :return: output file object
        :rtype: file
        """
        return self._file_obj;

    def path(self):
        """ output file path
        :return: output file path
        :rtype: str
        """
        return self._path

    def url(self):
        """ output url

        :return: output url
        :rtype: str
        """
        if self._path:
            return 'file:' + self._path
        else:
            return None

    def set_mime_type(self, mime_type):
        self._mime_type = mime_type

    def mime_type(self):
        return self._mime_type


class _MFRequest(object):
    class Packet(object):
        def __init__(self, string=None, path=None, url=None, length=None, mime_type=None, compress=False,
                     buffer_size=BUFFER_SIZE):
            if string:
                self._bytes = string.encode('utf-8')
                self._path = None
                self._url = None
                self._length = len(self._bytes)
            elif path:
                self._bytes = None
                self._path = path
                self._url = None
                self._length = length
            elif url:
                self._bytes = None
                self._url = url
                self._path = None
                self._length = length
            else:
                raise ValueError('Either str or url argument is required.')
            self._type = mime_type
            self._compress = compress
            self._buffer_size = buffer_size

        @property
        def url(self):
            return self._url

        @property
        def length(self):
            return self._length

        @property
        def type(self):
            return self._type

        @property
        def compress(self):
            return self._compress

        def send(self, sock, remaining):
            self._send_header(sock, remaining)
            self._send_content(sock)

        def _send_header(self, sock, remaining):
            header = '\x01'
            header += '\x01' if self._compress else '\x00'
            assert len(header) == 2
            header += struct.pack('!q', self._length)
            assert len(header) == 10
            header += struct.pack('!i', remaining)
            assert len(header) == 14
            if self._type is None:
                header += struct.pack('>h', 0)
                assert len(header) == 16
            else:
                mime_type = self._type.encode('utf-8')
                header += struct.pack('>h', len(mime_type))
                assert len(header) == 16
                header += mime_type
            sock.sendall(header)

        def _send_content(self, sock):
            if self._bytes is not None:
                sock.sendall(self._bytes)
            else:
                if self._path:
                    f = open(self._path, 'rb')
                elif self._url:
                    f = urllib.urlopen(self._url)
                else:
                    raise ValueError("Missing path or url.")
                try:
                    chunk = f.read(self._buffer_size)
                    while len(chunk) > 0:
                        sock.sendall(chunk)
                        chunk = f.read(self._buffer_size)
                finally:
                    f.close()

    def __init__(self, sgen, seq, service, args=None, inputs=None, outputs=None, route=None, emode=None, session=None,
                 token=None, app=None,
                 protocols=None, compress=False):
        self._packets = []
        # service request/message packet
        xml = self._create_request_xml(sgen, seq, service, args, inputs, outputs, route, emode, session,
                                       token, app, protocols)
        self._packets.append(_MFRequest.Packet(string=xml, mime_type='text/xml', compress=compress))
        if inputs is not None:
            for mi in inputs:
                self._packets.append(
                    _MFRequest.Packet(path=mi.path(), url=mi.url(), length=mi.length(), mime_type=mi.type(),
                                      compress=False))

    @classmethod
    def _create_request_xml(cls, sgen, seq, service, args=None, inputs=None, outputs=None, route=None, emode=None,
                            session=None, token=None, app=None, protocols=None):
        assert emode is None or emode == 'distributed-first' or emode == 'distributed-all'
        w = XmlStringWriter('request')
        if protocols is not None:
            for protocol in protocols:
                w.add('output-protocol', protocol)
        token_str, token_type = token if type(token) is tuple else (token, None)
        outputs = [] if outputs is None else outputs
        outputs = [outputs] if not isinstance(outputs, list) else outputs
        nb_outputs = len(outputs)
        data_out_min, data_out_max = (None, None) if nb_outputs == 0 else(nb_outputs, nb_outputs)
        w.push('service',
               {'emode': emode, 'target': route, 'name': service, 'session': session, 'token-type': token_type,
                'token': token_str, 'app': app, 'sgen': str(sgen), 'seq': str(seq), 'data-out-min': data_out_min,
                'data-out-max': data_out_max})
        if args is not None:
            w.add_element(args, True)
        if inputs is not None and len(inputs) > 0:
            for mi in inputs:
                w.push('attachment')
                if mi.url():
                    w.add('source', mi.url())
                if mi.checksum():
                    w.add('csum', str(mi.checksum()))
                w.pop()
        w.pop()
        return _get_xml_declaration() + w.doc_text()

    @property
    def length(self):
        length = 0L
        for packet in self._packets:
            if packet.length == -1:
                return -1L
            length += 16
            if packet.type:
                length += len(packet.type.encode('utf-8'))
            length += packet.length
        return length

    def send(self, sock):
        remaining = len(self._packets) - 1
        for packet in self._packets:
            packet.send(sock, remaining)
            remaining -= 1

    def __getitem__(self, index):
        return self._packets.__getitem__(index)

    def __len__(self):
        return self._packets.__len__()


class _MFResponse(object):
    def __init__(self, outputs):
        if outputs is None:
            self._outputs = []
        else:
            if not isinstance(outputs, list):
                assert isinstance(outputs, MFOutput)
                self._outputs = [outputs]
            else:
                self._outputs = outputs
        self._http_version = None
        self._http_status_code = None
        self._http_status_message = None
        self._http_header_fields = {}
        self._result = None
        self._error = None

    @property
    def result(self):
        return self._result

    @property
    def error(self):
        return self._error

    def recv(self, sock):
        bytes_received = self._recv_header(sock)
        pkt_idx = 0  # packet index
        while True:
            bytes_length = len(bytes_received)
            if bytes_length < 16:
                data = sock.recv(BUFFER_SIZE)
                if not data:
                    raise ExHttpResponse('Incomplete packet ' + pkt_idx + '.')
                else:
                    bytes_received += data
                    continue
            pkt_length = struct.unpack('>q', bytes_received[2:10])[0]
            pkt_remaining = struct.unpack('>i', bytes_received[10:14])[0]
            pkt_mime_type_length = struct.unpack('>h', bytes_received[14:16])[0]
            if pkt_mime_type_length <= 0:
                bytes_received = self._recv_packet(sock, pkt_idx, pkt_length, None, bytes_received, pkt_remaining)
                pkt_idx += 1
            else:
                if bytes_length < (16 + pkt_mime_type_length):
                    data = sock.recv(BUFFER_SIZE)
                    if not data:
                        raise ExHttpResponse('Incomplete packet ' + pkt_idx + '.')
                    else:
                        bytes_received += data
                        continue
                pkt_mime_type = bytes_received[16:16 + pkt_mime_type_length]
                bytes_received = bytes_received[16 + pkt_mime_type_length:]
                bytes_received = self._recv_packet(sock, pkt_idx, pkt_length, pkt_mime_type, bytes_received,
                                                   pkt_remaining)
                pkt_idx += 1
            if pkt_remaining == 0:
                break

    def _recv_packet(self, sock, idx, length, mime_type, bytes_received, remaining):
        n = len(bytes_received)
        if idx == 0:  # first packet: result/error xml
            while len(bytes_received) < length:
                data = sock.recv(BUFFER_SIZE)
                if not data:
                    raise ExHttpResponse('Incomplete packet ' + idx + '.')
                bytes_received += data
            self._parse_reply(bytes_received[0:length])
            bytes_received = bytes_received[length:]
            # now check outputs
            nb_outputs = len(self._outputs)
            if remaining != nb_outputs:
                raise ExHttpResponse('Mismatch number of service outputs. Expecting ' + str(nb_outputs) +
                                     ', found ' + str(remaining))
        else:
            output = self._outputs[idx - 1]
            if mime_type:
                output.set_mime_type(mime_type)
            if output.file_object():
                f = output.file_object()
            else:
                f = open(output.path(), 'wb')
            try:
                if n < length:
                    if n > 0:
                        f.write(bytes_received)
                        f.flush()
                        # print('written: ' + str(n))
                    while n < length:
                        data = sock.recv(BUFFER_SIZE)
                        if not data:
                            raise IOError('Failed to receive data for packet: ' + idx)
                        if n + len(data) < length:
                            f.write(data)
                            n += len(data)
                        else:
                            f.write(data[0:length - n])
                            bytes_received = data[length - n:]
                            n = length
                        f.flush()
                        # print('written: ' + str(n))
                else:
                    f.write(bytes_received[0:length])
                    bytes_received = bytes_received[length:]
            finally:
                f.close()
        return bytes_received

    def _parse_reply(self, text):
        rxe = XmlElement.parse(text)
        reply_type = rxe.value('reply/@type')
        if reply_type == 'result':
            self._result = rxe.element('reply/result')
        else:
            assert reply_type == 'error'
            self._error = rxe.element('reply')

    def _recv_header(self, sock):
        # receive header
        header = ''
        bytes_received = ''
        completed = False
        while not completed:
            data = sock.recv(BUFFER_SIZE)
            if not data:
                break
            end = data.find('\r\n\r\n')  # end of header
            if end >= 0:
                header += data[0:end]
                completed = True
                bytes_received += data[end + 4:]
                break
            else:
                header += data
        if not completed:
            raise ExHttpResponse('Failed to receive http header. Incomplete header: ' + header)
        # parse header fields
        self._parse_header(header)
        # handle status code
        if not self._http_status_code:
            raise ExHttpResponse("Invalid http response: missing status code.")
        if not self._http_status_message:
            raise ExHttpResponse("Invalid http response: missing status message.")
        if self._http_status_code == '200':
            # 200: success
            return bytes_received
        elif self._http_status_code == '407':
            # 407: proxy auth required
            raise ExProxyAuthenticationRequired('Proxy authentication required.')
        else:
            # Other failed status(errors)
            if 'Content-Type' in self._http_header_fields and 'Content-Length' in self._http_header_fields:
                # Error with content/message.
                content_type = self._http_header_fields['Content-Type']
                content_length = long(self._http_header_fields['Content-Length'])
                idx = content_type.find('charset=')
                encoding = None if idx == -1 else content_type[idx + 8:]
                content = ''
                while True:
                    data = sock.recv(BUFFER_SIZE)
                    content += data
                    if data == '' or len(content) >= content_length:
                        break
                    if encoding is not None:
                        content = content.decode(encoding)
                raise ExHttpResponse(
                    'Invalid HTTP/' + self._http_version + ' response: ' + self._http_status_code + ' ' +
                    self._http_status_message + '. Content: ' + content)
            else:
                # Error without content/message
                raise ExHttpResponse(
                    'Invalid HTTP/' + self._http_version + ' response: ' + self._http_status_code + ' ' +
                    self._http_status_message + '.')

    def _parse_header(self, header):
        lines = header.split('\r\n')
        idx1 = lines[0].find('HTTP/') + 5
        idx2 = lines[0].find(' ', idx1)
        self._http_version = lines[0][idx1:idx2]
        idx3 = idx2 + 1
        idx4 = lines[0].find(' ', idx3)
        self._http_status_code = lines[0][idx3:idx4]
        self._http_status_message = lines[0][idx4 + 1:]
        lines = lines[1:]
        self._http_header_fields = {}
        for line in lines:
            kv = line.split(':')
            self._http_header_fields[kv[0]] = kv[1].strip()


class ExNotConnected(Exception):
    pass


class ExHttpResponse(Exception):
    pass


class ExProxyAuthenticationRequired(Exception):
    pass


def _crc32(path):
    from zlib import crc32
    with open(path, 'r') as f:
        crc = crc32('')
        while True:
            data = f.read(BUFFER_SIZE)
            if not data:
                break
            crc = crc32(data, crc)
    return crc

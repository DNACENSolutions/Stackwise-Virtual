import json
import requests
import os
import sys
import yaml
import importlib
import time
import logging
import re
import pprint
import traceback
import getpass
from svlservices import StackWiseVirtual
from pyats.topology import loader
logger = logging.getLogger("ClientManager")
log = logger
GLOBAL_TASK_TIMEOUT=1800
TASK_COMPLETION_POLL_INTERVAL=2
CR_DEVICE_BUSY_STATUS = "This device is already under process by command runner in another session,try with other device"
tb_file = os.path.join(os.getcwd(), 'testbed', 'testbed_generated.yaml')
tb_template_file = os.path.join(os.getcwd(), 'testbed', 'generated_testbed_file.yaml')
print(tb_template_file)
class ResponseDict(dict):
    """ Data structure to extend dict attribute access """

    def __init__(self, response):
        """ initialize a dict to ResponseDict

        Args:
            response (dict): dict to convert
        """
        self._response = response
        for k, v in response.items():
            if isinstance(v, dict):
                self[k] = ResponseDict(v)
            else:
                self[k] = v
            if isinstance(v, list):
                val_list = []
                for item in v:
                    if isinstance(item, dict):
                        val_list.append(ResponseDict(item))
                    else:
                        val_list.append(item)
                self[k] = val_list

    def __getattr__(self, name):
        """ extend attribute access

        Args:
            name (str): name of attribute

        Returns:
            object: attribute of response
        """

        return self.get(name)
        
class ClientManager(object):
    """ Client manager to interact with API Clients of various services. """

    TIMEOUT = 60
    AUTHORIZATION_TOKEN = 'X-JWT-ACCESS-TOKEN'

    def __init__(self, server, username, password, base_url, protocol="https", port=None):
        """ Object initializer

        Initializer also authenticates using the credentials, and stores the generated
        authentication ticket/token.

        Args:
            server (str): cluster server name (routable DNS addess or ip)
            username (str): user name to authenticate with
            password (str): password to authenticate with
            base_url (str): default/constant portion of the url
            protocol (str): network protocol - http or https
            port (str): port number

        Raises:
            ApiClientException: when unsupported protocol is passed
        """

        self.log = log

        self.server = server
        self.username = username
        self.password = password

        self.port = str(port)
        if port:
            self.server = self.server + ":" + self.port

        if protocol not in ["http", "https"]:
            self.log.error("Not supported protocol {}.".format(protocol))
            raise BaseException("Not supported protocol {}.".format(protocol))

        self.base_url = "{}://{}{}".format(protocol, self.server, base_url)
        self.server_url = "{}://{}".format(protocol, self.server)

        self._default_headers = {}
        self._common_headers = {}

    def __repr__(self):
        """ Overrides the default object representation to display the object attributes. """

        return "[API Client: <server:{}> <username:{}> <password:{}>]".format(self.server,
                                                                              self.username,
                                                                              self.password)

    def add_api(self, name, obj):
        """ Add an api client to client manager.

        Args:
            name (str): name you want to set to the api client, has to follow python variable naming
                        rule.
            obj (object): api client which actually calling call_api method.
        """

        setattr(self, name, obj)

    def connect(self, force=None):
        """ Generates a new ticket/token.

        Args:
            force (bool): If true, forces a new connection, else authenticates the existing one
        """

        self.log.info("Connecting to the API client.")
        self.authenticate(force=force)

    def disconnect(self):
        """ Disconnect from API client"""

        self.log.info("Disconnecting from the API client.")

    def authenticate(self):
        """ Generates a new authentication ticket or token. """

        raise NotImplementedError

    @property
    def default_headers(self):
        return self._default_headers

    @default_headers.setter
    def default_headers(self, headers):
        """ Set default headers of client.

        Args:
            headers (dict): headers to set.
        """

        self._default_headers.update(headers)

    @property
    def common_headers(self):
        return self._common_headers

    @common_headers.setter
    def common_headers(self, headers):
        """ Set common headers of client.

        Args:
            headers (dict): headers to set.
        """

        self._common_headers.update(headers)

    def call_api(self,
                 method,
                 resource_path,
                 raise_exception=True,
                 response_dict=True,
                 port=None,
                 protocol=None,
                 **kwargs):
        """ Handles the requests and response.

        Args:
            method (str): type of request.
            resource_path (str): URL in the request object.
            raise_exception (boolean): If True, http exceptions will be raised.
            response_dict (boolean): If True, response dict is returned, else response object
            port (int): port value
            protocol (str): indicates whether protocol is http or https
            kwargs (dict):
                url (optional): URL for the new Request object.
                params (optional): Dictionary or bytes to be sent in query string for the Request.
                data (optional): Dictionary, bytes, or file-like object to send in the body of the
                                 Request.
                json (optional): json data to send in the body of the Request.
                headers (optional): Dictionary of HTTP Headers to send with the Request.
                cookies (optional): Dict or CookieJar object to send with the Request.
                files (optional): Dictionary of 'name': file-like-objects
                                  (or {'name': ('filename', fileobj)}) for multipart encoding upload
                auth (optional): Auth tuple to enable Basic/Digest/Custom HTTP Auth.
                timeout (float or tuple) (optional): How long to wait for the server to send data
                                                     before giving up, as a float, or a (connect
                                                     timeout, read timeout) tuple.
                allow_redirects (bool) (optional): Boolean. Set to True if POST/PUT/DELETE redirect
                                                   following is allowed.
                proxies (optional): Dictionary mapping protocol to the URL of the proxy.
                verify (optional): if True, the SSL cert will be verified. A CA_BUNDLE path can also
                                   be provided.
                stream (optional): if False, the response content will be immediately downloaded.
                cert (optional): if String, path to ssl client cert file (.pem). If Tuple,
                                 (‘cert’, ‘key’) pair
        Returns:
            object: response as a dict if response_dict is False
            dict: response as a dict if response_dict is True

        Raises:
            e: requests.exceptions.HTTPError, when HTTP error occurs
        """

        resource_path = requests.utils.quote(resource_path)

        if port:
            if self.port in self.base_url:
                base_url = self.base_url.replace(self.port, port)
                server_url = self.server_url.replace(self.port, port)
            else:
                base_url = self.base_url + ":{}".format(port)
                server_url = self.server_url + ":{}".format(port)
            if "full_path" in kwargs :
                kwargs.pop("full_path" )
                url = server_url + resource_path
            elif resource_path.find("/dna/intent/api/v") != -1 or resource_path.find("/dna/api/v") != -1 or resource_path.find("/dna/data/api/v") != -1 or\
                resource_path.find("/api/system/") != -1 or resource_path.find("/api/dnacaap/v") != -1 or resource_path.find("/api/sys-ops/v") != -1:
                url = server_url + resource_path
            else:
                url = base_url + resource_path
        else:
            if "full_path" in kwargs:
                kwargs.pop("full_path" )
                url = self.server_url + resource_path
            elif resource_path.find("/dna/intent/api/v") != -1 or resource_path.find("/dna/api/v") != -1 or resource_path.find("/dna/data/api/v") != -1 or\
                resource_path.find("/api/system/") != -1 or resource_path.find("/api/dnacaap/v") != -1 or resource_path.find("/api/sys-ops/v") != -1:
                url = self.server_url + resource_path
            else:
                url = self.base_url + resource_path
        self.log.info("Resource path full url: {}".format(url))
        if protocol:
            if protocol == "http" and "https:" in url:
                url = url.replace("https:", "http:")

            if protocol == "https" and "http:" in url:
                url = url.replace("http:", "https:")

        if "/api/v1/v2/" in url:
            url = url.replace("/api/v1/v2/", "/api/v2/")

        if "headers" in kwargs:
            headers = kwargs.pop("headers")
        else:
            headers = self.default_headers

        if not kwargs.get("timeout"):
            kwargs["timeout"] = ClientManager.TIMEOUT

        headers.update(self.common_headers)

        if "verify" in kwargs:
            verify = kwargs.pop("verify")
        else:
            verify = False
            requests.packages.urllib3.disable_warnings()

        self.log.debug("Request:\nmethod:\n{}\nurl: {}\nheaders: {}\nParameters: {}"
                       .format(method, url, headers, kwargs))
        response = requests.request(method, url, headers=headers, verify=verify, **kwargs)

        time_taken = response.elapsed.seconds + response.elapsed.microseconds / 1e6
        self.log.debug("API Response:\nurl: {}\nmethod: {}\ntime taken in seconds: {}\ntext: {}"
                       .format(url, method, format(time_taken, '.2f'), response.text))

        if hasattr(response, 'headers'):
            if response.headers and 'set-cookie' in response.headers:
                self.log.debug("Response has set-cookie: {}".format(response.headers['set-cookie']))
                if ClientManager.AUTHORIZATION_TOKEN in response.headers['set-cookie']:
                    self.log.debug("Response cookie has {}. Update cookie: {}".format(
                        ClientManager.AUTHORIZATION_TOKEN, response.headers['set-cookie']))
                    self.common_headers["Cookie"] = response.headers['set-cookie']

        if raise_exception:
            try:
                response.raise_for_status()
            except requests.exceptions.HTTPError as e:
                self.log.exception("Error Code: {} URL:{} Data:{} Headers:{} Message:{}"
                                   .format(e.response.status_code, url, kwargs, headers,
                                           e.response.text))
                raise e

        if response_dict:
            if response.text:
                return json.loads(response.text)
            else:
                return response
        else:
            return response

class ApicemClientManager(ClientManager):
    """ Client manager to interact with API Client. """

    MAGLEV_TIMEOUT = 60 # As requested by Maglev team via Olaf

    FORTY_FIVE_MIN = 600
    SIXTY_MIN = 900

    def __init__(self, server, username, password, version="v1",base_url = "/api", connect=True, maglev=True):
        """ Object initializer.

        Initializer also aunthenticates using the credentials, and stores the generated
        authentication ticket.

        Args:
            server (str): cluster server name (routable DNS address or ip)
            username (str): user name to authenticate with
            password (str): password to authenticate with
            version (str): version of the API to be used
            connect (bool): flag to authenticate and establish swagger client
            maglev (bool): flag to call the maglev authenticate
        """

        #base_url = base_url
        protocol = "https"
        self.version = version
        super().__init__(
            server,
            username,
            password,
            base_url,
            protocol=protocol)

        self.default_headers = {"Content-Type": "application/json"}
        self.__connected = False
        self._is_maglev = maglev
        self.cas_ticket = None
        self.all_calls_fname = 'ext_api_log'
        self._maglev_token_time = ""
        if connect:
            self.connect()
        self.setup_api()

    def setup_api(self):
        """ Creates the APIC-EM apis.

        For example:
            self.backup is an instance of BackupApi.
            self.capacity_manager is an instance of CapacityManagerApi
        Note:
            self.log is the instance of LogApi
        """

        self.log.debug("Initializing the APIC-EM APIs.")

    def connect(self, force=False):
        """ Generates a new ticket and establishes a fresh swagger client.

        Args:
            force (bool): If true, forces a new connection, else authenticates the existing one
        """

        if force:
            self.__connected = False

        self.log.info("Connecting to the Apic-em northbound API client.")
        if not self._is_maglev:
            self._authenticate()
        else:
            self._maglev_authenticate()
            self._maglev_token_time = int(time.time())
            self.log.debug("Initial Maglev login time: '{}'.".format(self._maglev_token_time))

    def disconnect(self):
        """ Deletes the generated ticket and effectively disconnecting the user. """

        try:
            self.log.info("Disconnecting the Apic-em northbound API client.")
            if not self._is_maglev:
                self.common_headers.pop("X-Auth-Token")
                self.common_headers.pop("X-CSRF-Token")
            else:
                self.common_headers.pop("Cookie")
        except KeyError:
            self.log.info("Already disconnected from Northbound API client.")
        self.__connected = False

    def call_api(self, method, resource_path, **kwargs):
        """ Wrapper of call_api to encode post data.

        Args:
            resource_path (str): resource_path
            method (str): http method, support "GET", "POST", "PUT", "DELETE"
            kwargs (dict):
                url (optional): URL for the new Request object.
                params (optional): Dictionary or bytes to be sent in query string for the Request.
                data (optional): Dictionary, bytes, or file-like object to send in the body of the
                                 Request.
                json (optional): json data to send in the body of the Request.
                headers (optional): Dictionary of HTTP Headers to send with the Request.
                cookies (optional): Dict or CookieJar object to send with the Request.
                files (optional): Dictionary of 'name': file-like-objects
                                  (or {'name': ('filename', fileobj)}) for multipart encoding upload
                auth (optional): Auth tuple to enable Basic/Digest/Custom HTTP Auth.
                timeout (float or tuple) (optional): How long to wait for the server to send data
                                                     before giving up, as a float, or a (connect
                                                     timeout, read timeout) tuple.
                allow_redirects (bool) (optional): Boolean. Set to True if POST/PUT/DELETE redirect
                                                   following is allowed.
                proxies (optional): Dictionary mapping protocol to the URL of the proxy.
                verify (optional): if True, the SSL cert will be verified. A CA_BUNDLE path can also
                                   be provided.
                stream (optional): if False, the response content will be immediately downloaded.
                cert (optional): if String, path to ssl client cert file (.pem). If Tuple,
                                 (‘cert’, ‘key’) pair

        Returns:
            dict: response of request.
        """
        if resource_path.find("/dna/intent/api/v") != -1 or resource_path.find("/api/v") != -1 or\
            resource_path.find("/api/system/") != -1 or resource_path.find("/api/dnacaap/v") != -1 or resource_path.find("/api/sys-ops/v") != -1:
            copyargs = {'method': method, 'URL': "{}{}".format(self.base_url, resource_path)}
        else:
            copyargs = {'method': method, 'URL': "{}{}".format(self.server, resource_path)}
        copyargs.update(kwargs)
        if self.__connected and self._is_maglev:
            self.log.debug("Checking the validity of the Maglev cookie.")
            self._handle_maglev_idle_timeout()

        headers = self.default_headers.copy()
        #TODO (mingyazh): remove trailing back slash of resource path in client

        if self._is_maglev:
            if not kwargs.get("timeout"):
               timeout = ApicemClientManager.MAGLEV_TIMEOUT
            else:
               timeout = kwargs.get("timeout")
               kwargs.pop("timeout")
        else:
            timeout = None

        if "headers" in kwargs:
            headers.update(kwargs.pop("headers"))
        resource_path = resource_path.rstrip('\/')

        if "data" in kwargs and "files" not in kwargs:
            if isinstance(kwargs["data"], dict):
                kwargs["data"] = json.dumps(kwargs["data"])
                if "encode" in kwargs:
                    kwargs["data"] = kwargs["data"].encode(kwargs.pop("encode"))
            if isinstance(kwargs["data"], list):
                kwargs["data"] = json.dumps(kwargs["data"]).encode("utf-8")
        if "files" in kwargs:
            if kwargs["files"]:
                if isinstance(kwargs["files"], dict):
                    fd = kwargs["files"]
                    if len(fd) == 1 and isinstance(list(fd.values())[0], tuple):
                        ft = fd[list(fd.keys())[0]]
                        fd[list(fd.keys())[0]] = ft[:1] + (open(ft[1], "rb"), ) + ft[2:]
                    else:
                        kwargs["files"] = {key:open(val, "rb") for key, val in fd.items()}

                if isinstance(kwargs["files"], str):
                    kwargs["files"] = open(kwargs["files"], "rb")

                if headers.get("Content-Type") == "application/json":
                    headers.pop("Content-Type")
            else:
                #TODO (mingyazh): deal with header parameters in client
                kwargs.pop("files")
                headers["Content-Type"] = "multipart/form-data"

        if method == "GET":
            if (headers.get('Content-Type') == 'multipart/form-data'
                    or headers.get('Accept') == 'application/octet-stream'
                    or headers.get('Content-Type') == 'application/octet-stream'):
                return super(ApicemClientManager, self).call_api(method=method,
                                                                 resource_path=resource_path,
                                                                 headers=headers,
                                                                 timeout=timeout,
                                                                 response_dict=False)
        if "dna" in kwargs:
            del kwargs['dna']

        response = super(ApicemClientManager, self).call_api(method=method,
                                                             resource_path=resource_path,
                                                             headers=headers,
                                                             timeout=timeout,
                                                             **kwargs)
        if isinstance(response, dict):
            return ResponseDict(response)

        if isinstance(response, list):
            response_list = []
            for item in response:
                if isinstance(item, dict):
                    response_list.append(ResponseDict(item))
                else:
                    response_list.append(item)
            return response_list

        return response

    def _authenticate(self):
        """ Generates a new authentication cas_ticket. """

        if not self.__connected:
            resource_path = "/" + self.version + "/ticket"
            data = json.dumps({"username": self.username, "password": self.password})
            response = self.call_api("POST",
                                     resource_path,
                                     data=data,
                                     raise_exception=True,
                                     response_dict=False)
            result_json = json.loads(response.text)
            if 'serviceTicket' in result_json['response'].keys():
                ticket = result_json["response"]["serviceTicket"]
            else:
                # If ticket is not generated for a user, don't want to proceed
                raise Exception("Cannot create NB client for an unauthorized user {}"
                                .format(self.username))
            headers = {"X-Auth-Token": ticket, "X-CSRF-Token": "soon-enabled"}
            self.common_headers = headers
            self.cas_ticket = ticket
            self.__connected = True
        else:
            self.log.info("Already connected to Northbound API client.")
    def _maglev_authenticate(self):
        """ Generates a new authentication cookie for Maglev. """

        if not self.__connected:
            resource_path = "/api/system/" + self.version + "/identitymgmt/login"
            response = self.call_api("GET",
                                     resource_path,
                                     auth=(self.username, self.password),
                                     raise_exception=True,
                                     response_dict=False,
                                     verify=False,full_path=True)
            if (not hasattr(self, 'common_headers')
                or not self.common_headers
                or 'Cookie' not in self.common_headers
                or 'X-JWT-ACCESS-TOKEN' not in self.common_headers['Cookie']):
                # If cookie is not generated for a user, don't want to proceed
                raise Exception("Cannot create NB client for an unauthorized user {}"
                                .format(self.username))
            self.__connected = True
        else:
            self.log.info("Already connected to Northbound API client.")

    def add_new_apis(self, client_path):
        """ Add new clients to ApicemClientManager.

        Args:
            client_path (str): path to new clients, inside it should contain python modules for
            clients

        Notes:
            If there is api file having the same filename and classname as in default api client
            folder, it will override the default one.
        """

        client_path = os.path.expanduser(client_path)
        if not os.path.isdir(client_path):
            self.log.error("{} is not a valid directory.".format(client_path))
            raise Exception("{} is not a valid directory.".format(client_path))
        sys.path.append(client_path)

        for file in os.listdir(client_path):
            if file.endswith("api.py"):
                client_name = file.replace(".py", "")
                client_module = importlib.import_module(client_name)
                for obj in dir(client_module):
                    if (not obj.startswith("__") and issubclass(getattr(client_module, obj), Apicem)
                        and not issubclass(Apicem, getattr(client_module, obj))):
                        client_instance = getattr(client_module, obj)(self)
                        setattr(self, client_name, client_instance)

    def _handle_maglev_idle_timeout(self):
        """ Handles the timeout for the maglev login """

        elapsed_time = int(time.time()) - self._maglev_token_time
        self.log.debug("Initial login: '{}', Elapsed time: '{}'.".format(self._maglev_token_time,
                                                                         elapsed_time))

        if ApicemClientManager.FORTY_FIVE_MIN <= elapsed_time < ApicemClientManager.SIXTY_MIN:
            self.log.debug("Cookie Age: '{}'. Cookie will be renewed.".format(elapsed_time))
            self._maglev_token_time = int(time.time())
            self.log.debug("New login time: '{}'".format(self._maglev_token_time))

        elif elapsed_time >= ApicemClientManager.SIXTY_MIN:
            self.log.debug("Cookie Age: '{}'. Re-authentication will be initiated".format(elapsed_time))
            self.__connected = False
            self._maglev_authenticate()
            self._maglev_token_time = int(time.time())
            self.log.debug("New login time: '{}'".format(self._maglev_token_time))

        else:
            self.log.debug("Cookie age: '{}'. It is still valid.".format(elapsed_time))

class SVLFormation(object):
    ''' SVL formation class, take both SVL devices ip addfresss as input and DNAC credentials and device credentials 
        Read NW Device info from dnac and form SVL
    '''
    def __init__(self, dnac_ip, dnac_user, dnac_pass, device1_ip, device2_ip, device_user, device_pass,device_enable_pass):
        self.devinfo = {}
        self.device1 = {}
        self.device2 = {}
        self.tb_file = tb_file
        self.testbed_file = tb_template_file
        self.dnac_ip = dnac_ip
        self.dnac_user = dnac_user
        self.dnac_pass = dnac_pass
        self.device1_ip = device1_ip
        self.device2_ip = device2_ip
        self.device_user = device_user
        self.device_pass = device_pass
        self.device_enable_pass = device_enable_pass
        self.log = logging.getLogger(__name__)
        self.log.info("SVL Formation Started for devices {} and {}".format(self.device1_ip,self.device2_ip))
        self.dnac = ApicemClientManager(self.dnac_ip, self.dnac_user, self.dnac_pass)
        self.device1['ip'] = self.device1_ip
        self.device2['ip'] = self.device2_ip
    def get_interface_info(self, deviceid, name, attribute='id'):
        """Find the device ID of the device in the inventory by name"""
        params={'name' : name}
        print(params)
        response =  self.dnac.call_api(method = "GET",
                                            resource_path = "/v1/interface/network-device/{0}/interface-name".format(deviceid), 
                                            params = params)
        response = response['response']
        self.log.info(response)
        return response[attribute]
    #==================================================================================================
    # (cfind_uuid_of_device )
    #--------------------------------------------------------------------------------------------------
    def get_network_device_info(self, ip_addresses, retry=2):
        ''' Get network device info from DNAC '''
        while retry > 0:
            for i in range(1, 50000, 100):
                resource_path = "/v1/network-device/{0}/{1}".format(i, 100)
                response = self.dnac.call_api(method="GET", resource_path=resource_path)
                response = response['response']
                if len(response):
                    for dev in response:
                        if dev['managementIpAddress'] and str(dev['managementIpAddress']) in ip_addresses and\
                            dev['managementIpAddress'] not in list(self.devinfo.keys()):
                            self.devinfo[dev['managementIpAddress']] = dev
                            print("device found:{} ".format(dev['managementIpAddress']))
                        else:
                            self.log.debug("device not from requested list:{} ignore ".format(dev['managementIpAddress']))
                            pass
                else:
                    self.log.info("Breaking, as no more entries left")
                    break
            if len(list(self.devinfo.keys())) == len(ip_addresses):
                self.log.info("Found all devices")
                break
            retry = retry - 1
            time.sleep(10)
        if retry == 0:
            self.log.error("No more retries left, and not all devices found")
            return False 
        self.log.info("Device info: {}".format(self.devinfo))
        return True
    #==================================================================================================
    def execute_command_on_device(self, deviceid, cli="", retry=2):
        ''' Execute command on device '''
        result=True
        data={"name":"command-runner","description":"command-runner-network-poller","deviceUuids":[deviceid],"commands":[cli]}
        self.log.info(data)
        url='/v1/network-device-poller/cli/read-request'
        try:
            response = self.dnac.call_api(method = "POST", resource_path = url,data=data)
            #self.log.info(response)
            r = self.task_handle(response,task_status = "Complete",timeout=300,msg = "Command execution on device is successful:",count=2)
            #self.log.info(result)
            if not r and retry > 0:
                return self.execute_command_on_device(deviceid, cli=cli, retry=retry-1)
            taskid=response["response"]["taskId"]
            #Get file id
            #self.log.info(result)
            if(result):
                response = self.dnac.call_api(method="GET", resource_path="/v1/task/{0}/tree".format(taskid))
                self.log.info(response)
                self.log.info(deviceid)
                if 'failureReason' in response["response"][0].keys() and\
                    response["response"][0]['failureReason'] == CR_DEVICE_BUSY_STATUS:
                    time.sleep(30)
                    return self.execute_command_on_device(deviceid, cli=cli, retry=retry)

                fileid=response["response"][0]['progress'].split(':')[1].split('"')[1]
                response1 = self.dnac.call_api(method="GET", resource_path="/v1/file/{0}".format(fileid))
                self.log.info(response1)
                for r in response1:
                    if r[ "deviceUuid"] in [deviceid]:
                        if r["commandResponses"]["SUCCESS"].values():
                            return  {'result':True, 'output':list(r["commandResponses"]["SUCCESS"].values())[0]}
                        elif r["commandResponses"]["FAILURE"].values():
                            if  CR_DEVICE_BUSY_STATUS in list(r["commandResponses"]["FAILURE"].values())[0]:
                                time.sleep(30)
                                return self.execute_command_on_device(deviceid, cli=cli, retry=retry)
                            return  {'result':False, 'output':list(r["commandResponses"]["FAILURE"].values())[0]}
                        else:
                            return  {'result':False, 'output':list(r["commandResponses"]["BLACKLISTED"].values())[0]}
            else:
                self.log.info(response)
                return {'result':False, 'output':"Command Failed"}
        except:
            self.log.error(traceback.format_exc())
            return {'result':False, 'output':"Command Failed"}
        return True

    #--------------------------------------------------------------------------
    #helper for handling task status
    #--------------------------------------------------------------------------
    def wait_for_task_complete(self, response, timeout=GLOBAL_TASK_TIMEOUT, count=2):
        self.log.info("Starting Task wait for task:{}".format(response))
        try:
            return self.__wait_for_task_complete(task_id=response['response']['taskId'], timeout=timeout)
        except :  # TODO: shouldn't this be a TimeoutError?
            traceback.print_exc()
            self.log.error(traceback.format_exc())
            if count <= 1:
                self.log.error("Timer Exceeded")
                return FAIL
            return self.wait_for_task_complete(response, timeout=timeout, count=count-1)

    def get_task_details(self, task_id):
        """ Returns a high-level summary of the specified Grapevine task.

        Args:
            task_id (str): task id of the job
        """
        resource_path = "/v1/task/{}/tree".format(task_id)
        method = "GET"
        return self.dnac.call_api(method=method,resource_path= resource_path)
    def task_handle(self, response, task_status="Complete", msg="Task Completion:",timeout=GLOBAL_TASK_TIMEOUT, count=2):
        '''helper for handling task status'''
        try:
            if(task_status=="Complete"):
                taskStatus= self.wait_for_task_complete(response,timeout=timeout)
                self.log.info(taskStatus)
                if(taskStatus['isError']):
                    self.log.error("{0} {1}".format(msg,taskStatus['failureReason']))
                    return False
                else:
                    self.log.info("{0} successful,{1}".format(msg,taskStatus['progress']))
            elif(task_status=="Success"):
                taskStatus= self.wait_for_task_success(response,timeout=timeout)
                self.log.info(taskStatus)
                if(taskStatus['isError']):
                    self.log.error("{0} {1}".format(msg,taskStatus['failureReason']))
                    return False
                else:
                    self.log.info("{0} successful,{1}".format(msg,taskStatus['progress']))
            elif(task_status=="Failure"):
                taskStatus= self.wait_for_task_failure(response,timeout=timeout)
                self.log.info(taskStatus)
                if(taskStatus['isError']):
                    self.log.error("{0} {1}".format(msg,taskStatus['failureReason']))
                else:
                    self.log.info("{0} Expected Failed,{1}".format(msg,taskStatus['progress']))
                    return False
        except AssertionError:  # TODO: shouldn't this be a TimeoutError?
            traceback.print_exc()
            self.log.error(traceback.format_exc())
            if count <= 1:
                self.log.error("Timer Exceeded")
                return False
            return self.task_handle(response, task_status=task_status,msg=msg, timeout=timeout, count=count-1)
        return True
    #-----------------------
    def get_task_id_from_task_id_result(self, task_id_result):
        """ Gets a taskId from a given TaskIdResult. """

        assert task_id_result is not None
        task_id_response = task_id_result["response"]
        assert task_id_response is not None
        task_id = task_id_response["taskId"]
        assert task_id is not None
        return task_id

    def wait_for_task_success(self, task_id_result=None, timeout=None):
        """ Waits for a task to be a success. """

        if timeout is None:
            timeout = self.TASK_DEFAULT_TIMEOUT

        assert task_id_result is not None
        task_id = self.get_task_id_from_task_id_result(task_id_result)
        return self.__wait_for_task_success(task_id=task_id, timeout=timeout)

    def wait_for_task_failure(self, task_id_result, timeout=None):
        """ Waits for the task to be failure for a given task_id

        Args:
            task_id_result (str): task_id is waiting for the failure status.
            timeout (int): time_out value to wait to failure status of the task.

        Returns:
            object: response of the task.
        """

        if timeout is None:
            timeout = self.TASK_DEFAULT_TIMEOUT

        task_id = self.get_task_id_from_task_id_result(task_id_result)
        return self.__wait_for_task_failure(task_id=task_id, timeout=timeout)

    def get_task_by_id(self,task_id):
        return self.dnac.call_api(method = "GET", resource_path = "/v1/task/{}".format(task_id))['response']

    def get_tasktree_by_id(self,task_id):
        return self.dnac.call_api(method = "GET", resource_path = "/v1/task/{}/tree".format(task_id))['response']

    def __wait_for_task_complete(self, task_id=None, timeout=None):

        if timeout is None:
            timeout = self.GLOBAL_TASK_TIMEOUT

        assert task_id is not None
        task_completed = False

        start_time = time.time()
        task_response = None

        while not task_completed:
            if time.time() > (start_time + timeout):
                assert False, ("Task {0} didn't complete within {1} seconds"
                               .format(task_response, timeout))
            task_response = self.get_task_by_id(task_id)
            self.log.info(task_response)
            if self.__is_task_success(task_response) or self.__is_task_failed(task_response):
                task_completed = True
                return task_response
            else:
                self.log.info("Task not completed yet, waiting:{}".format(task_response))
                time.sleep(TASK_COMPLETION_POLL_INTERVAL)
        return task_response

    def __wait_for_task_success(self, task_id=None, timeout=None):

        if timeout is None:
            timeout = self.GLOBAL_TASK_TIMEOUT

        assert task_id is not None
        task_completed = False

        start_time = time.time()
        task_response = None

        while not task_completed:
            if time.time() > (start_time + timeout):
                assert False, ("Task {0} didn't complete within {1} seconds"
                               .format(task_response, timeout))

            task_response = self.get_task_by_id(task_id)
            tasktree = self.get_tasktree_by_id(task_id)
            self.log.info(len(tasktree))
            if len(tasktree) > 1:
                self.log.info("Task Tree has more then 1 tasks")
                self.log.info(tasktree)

            if self.__is_task_success(task_response):
                self.log.info("Task Completed, Task Response:{}".format(task_response))
                task_completed = True
                return task_response
            elif self.__is_task_failed(task_response):
                task_completed = True
                assert False, ("Task failed, task response {0}".format(
                    task_response))
            else:
                self.log.info("Task not success yet, waiting:{}".format(task_response))
                time.sleep(TASK_COMPLETION_POLL_INTERVAL)

        return task_response

    def __wait_for_task_failure(self, task_id, timeout=None):
        """ Waits for the task to be failure for a given task_id

        Args:
            task_id (str): task_id is waiting for the failure status.
            timeout (int): time_out value to wait for failure status of the task.

        Returns:
            object: response of the task.
        """

        if timeout is None:
            timeout = self.GLOBAL_TASK_TIMEOUT

        task_completed = False
        task_response = None
        start_time = time.time()

        while not task_completed:
            if time.time() > (start_time + timeout):
                msg = "Task {0} didn't complete within {1} seconds".format(task_response,
                                                                           timeout)
                assert False, msg
            task_response = self.get_task_by_id(task_id)

            self.log.info(task_response)

            if self.__is_task_success(task_response):
                task_completed = True
            elif self.__is_task_failed(task_response):
                task_completed = True
            else:
                self.log.info("Task not failed yet, waiting:{}".format(task_response))
                time.sleep(TASK_COMPLETION_POLL_INTERVAL)
        return task_response

    def __is_task_failed(self, task_response):
        assert task_response is not None
        return task_response["isError"] is True

    def __is_task_success(self, task_response, error_codes=[]):
        """
        :type error_codes: list
        """
        result=True
        assert task_response is not None
        for error_code in error_codes:
            if error_code is not None and hasattr(
                    task_response, 'errorCode') and error_code == task_response["errorCode"]:
                return True
        is_not_error = task_response["isError"] is None or task_response["isError"] is False
        is_end_time_present = task_response.get("endTime") is not None
        result = is_not_error and is_end_time_present
        if result:
            self.log.info("Task completed with result:{}".format(result))
        return result
    def _collect_device_hostnames(self):
        """
        :type device_list: list
        """
        hostnames = []
        for device in self.devinfo:
            hostnames.append(self.devinfo[device]["hostname"])
        return hostnames

    def getCdpNbrData(self,deviceid,dev2hostname):
        """
        Capability Codes: R - Router, T - Trans Bridge, B - Source Route Bridge
                        S - Switch, H - Host, I - IGMP, r - Repeater, P - Phone,
                        D - Remote, C - CVTA, M - Two-port Mac Relay

        Device ID        Local Intrfce     Holdtme    Capability  Platform  Port ID
        TB5-N7K-FB3-FB3.fabric.com(FXS2044Q0S2)
                        Ten 1/1/2         144             R S C  N77-C7706 Eth 1/2
        TB4-DM1-9KB1.cisco.com
                        Gig 1/0/2         148             R S I  C9300-48U Gig 1/0/23
        Switch           Gig 0             126              S I   WS-C2950- Fas 0/13
        TB4-DM1-FB2.cisco.com
                        Gig 1/0/5         142             R S I  WS-C3850- Ten 1/0/8
        TB4-DM1-FB2.cisco.com
                        Gig 0/0/2         130             R S I  WS-C3850- Ten 1/0/6

        #N7K Output
        Device-ID          Local Intrfce  Hldtme Capability  Platform        Port ID
        Switch-2            mgmt0          144    S I       WS-C2950SX-24    Fas0/19
        TB5-ASR1K.fabric.com
                            Eth1/1         134    R I       ASR1006          Ten0/3/0
        N7k2-DC2(FXS2110Q4PM)
                            Gig 0/0/1       147     R S C   N77-C7706       Eth 2/3
        TB5-IM1.fabric.com
                            Eth1/2         176    R S I     WS-C3850-48P     Ten1/1/2
        # Some more variations
        AS-B1-AP12-3802I Gig 1/0/16        159              R T   AIR-AP380 Gig 0
        TB2-DMZ-Transit.cisco.com
                        Gig 1/0/21        177             R S I  C9300-24U Gig 1/0/21
        SEP5488DE5DF686  Gig 1/0/12        179             H P M  IP Phone  Port 1

        """
        intfMap = {
            'Fas': "FastEthernet",
            'Eth': "Ethernet",
            'eth': "Ethernet",
            'Gig': "GigabitEthernet",
            'Port': "GigabitEthernet",
            'Two': "TwoGigabitEthernet",
            'Fiv': "FiveGigabitEthernet",
            'Ten': "TenGigabitEthernet",
            'Twe': "TwentyFiveGigE",
            'For': "FortyGigabitEthernet",
            'Fif': "FiftyGigE",
            'Hun': "HundredGigE",
            'TwoH': "TwoHundredGigE",
            'Fou': "FourHundredGigE"
        }
        portlist = []
        cdpinfo = self.execute_command_on_device(deviceid, "show cdp nei")
        output = cdpinfo['output']
        if "IP Phone" in output:
            output = output.replace("IP Phone", "IPPhone") 
        nbr_pattern = f"({dev2hostname})"+"[\n\t\s]+(\S+ \S+|\S+)\s+\d+\s+(?:(?:[RTBSHIrPDCM]+[\s])+){1,}\s+\S+\s+(\S+ \S+|\S+)[\s\t]?"
        cdplist = re.findall(nbr_pattern, output)
        logger.debug(f"CDP List collected:\n{pprint.pformat(cdplist)}")
        for entry in cdplist:
            en = entry[0].split(".")[0]
            if ' ' in entry[1]:
                local_int_ps = entry[1].split(" ")
            else:
                local_int_ps = list(re.findall(r"([a-z]+)([0-9]+)", entry[1], re.I)[0])

            if ' ' in entry[2]:
                remote_int_ps = entry[2].split(" ")
            else:
                remote_int_ps = list(re.findall(r"([a-z]+)([0-9]+)", entry[2], re.I)[0])
            portlist.append(
                {
                    'name': en,
                    'localintf': intfMap[local_int_ps[0]] + local_int_ps[1],
                    'remoteIntf': intfMap[remote_int_ps[0]] + remote_int_ps[1]
                }
            )
        logger.info(f"Found following CDP Entries:\n{pprint.pformat(portlist)}")
        return portlist
    def get_both_switches_cdp_data(self):
        """
        :type device_list: list
        """
        self.cdpdata=[]
        device1 = list(self.devinfo.keys())[0]
        device2 = list(self.devinfo.keys())[1]
        self.cdpdata.append(
                {
                    "name": self.devinfo[device1]['hostname'],
                    "cdpdata": self.getCdpNbrData(self.devinfo[device1]['id'],
                                                  self.devinfo[device2]['hostname'])
                }
            )
        self.cdpdata.append(
                {
                    "name": self.devinfo[device2]['hostname'],
                    "cdpdata": self.getCdpNbrData(self.devinfo[device2]['id'],
                                                  self.devinfo[device1]['hostname'])
                }
            )
        return self.cdpdata

    def generate_cdp_data(self):
        ''' Generate CDP Data '''
        topology = "topology:\n"
        devlist = []
        topologydir = {
            'SWITCH-1': {'interfaces': {}},
            'SWITCH-2': {'interfaces': {}}
        }
        SpeedMap = {
            "FastEthernet": 1,
            "Ethernet": 1,
            "GigabitEthernet": 1,
            "TwoGigabitEthernet": 2,
            "FiveGigabitEthernet": 5,
            "TenGigabitEthernet": 10,
            "TwentyFiveGigE": 25,
            "FortyGigabitEthernet": 40,
            "FiftyGigE": 50,
            "HundredGigE": 100,
            "TwoHundredGigE": 200,
            "FourHundredGigE": 400
        }
        link_map = {}
        counter=0
        switchlist=['SWITCH-1','SWITCH-2']
        for devdata in self.cdpdata:
            devname = devdata['name']
            cdata = devdata['cdpdata']
            topology += f"\t{devname}:\n\t\tinterfaces:\n"
            #Check if all intrfaces are of same or different types.
            devIntflist = []
            for x in cdata:
                if x['localintf'].split('/')[0] not in devIntflist:
                    devIntflist.append(x['localintf'].split('/')[0])
            print(devIntflist)
            svllink = []
            dadLink = []
            if len(devIntflist) == 1:
                print("All interfaces are of same type")
                if len(cdata) ==1:
                    print("only 1 link present, use it for SVL Links")
                    svllink.append(cdata[0])
                else:
                    print("More than 1 link present, use it for DAD Links")
                    dadLink.append(cdata[0])
                    svllink = cdata[1:]
            else:
                print("Interfaces are of different types")
                print("Low speed interface will slected for DAD links and higher speed for SVL links")
                for link in cdata:
                    linkname = link['localintf'].split('/')[0][:-1]
                    if linkname in link_map:
                        link_map[linkname].append(link)
                    else:
                        link_map[linkname] = [link]
                print(link_map)
                for speed in SpeedMap:
                    if speed in link_map:
                        if  not dadLink :
                            dadLink = link_map[speed]
                        else:
                            svllink = link_map[speed]
            print(f"DAD Links: {dadLink}")
            print(f"SVL Links: {svllink}")
            #findout lower speed interface for DAD-LINK linkf and higher speed for STACKWISEVIRTUAL-LINK
            for interface in cdata:
                logger.debug(f"Processing info for Interface: {interface}")
                topology += f"\t\t\t{interface['localintf']}:\n"
                index1 = interface["localintf"].split('/')[-1]
                index1 = re.findall(r"\d", index1)[-1]
                index2 = interface["remoteIntf"] .split('/')[-1]
                index2 = re.findall(r"\d", index2)[-1]
                if interface in dadLink:
                    topologydir['SWITCH-1']['interfaces'][interface["localintf"]] = {
                        'link': f'DAD-LINK-{counter}',
                        'type': 'ethernet'
                    }
                    topologydir['SWITCH-2']['interfaces'][interface["remoteIntf"]] = {
                        'link': f'DAD-LINK-{counter}',
                        'type': 'ethernet'
                    }
                else:
                    topologydir['SWITCH-1']['interfaces'][interface["localintf"]] = {
                        'link': f'STACKWISEVIRTUAL-LINK-{counter}',
                        'type': 'ethernet'
                    }
                    topologydir['SWITCH-2']['interfaces'][interface["remoteIntf"]] = {
                        'link': f'STACKWISEVIRTUAL-LINK-{counter}',
                        'type': 'ethernet'
                    }
                counter += 1
                if interface['name'] in devlist:
                    topology += f"\t\t\t\tlink: eth-{interface['name']}-{index2}-{devname}-{index1}\n"
                else:
                    topology += f"\t\t\t\tlink: eth-{devname}-{index1}-{interface['name']}-{index2}\n"
                topology += "\t\t\t\ttype: ethernet\n"
            devlist.append(devname)
        #self.log.info(f"Below is the connection matrix that got generated with help of CDP Data:\n{topology}")
        #print(f"Below is the connection matrix that got generated with help of CDP Data:\n{topology}")
        pprint.pprint(topologydir)
        return topologydir

    def update_testbed_file(self):
        '''
        Read the testbed yaml file.
        update the testbed yaml file with device credentials
        update the tested yaml with SVL and DAD links.
        '''
        with open(self.testbed_file, 'r') as tb_file:
            tb_data = yaml.safe_load(tb_file)
        tb_data['testbed']['tacacs']['username'] = self.device_user
        tb_data['testbed']['passwords']['tacacs'] = self.device_pass
        tb_data['testbed']['passwords']['enable'] = self.device_enable_pass
        tb_data['testbed']['passwords']['line'] = self.device_enable_pass 
        tb_data['testbed']['custom']['switchstackinggroups'][0]["platformType"] = re.findall('Cisco Catalyst (\d+) Series Switches',
                                                                                self.devinfo[list(self.devinfo.keys())[0]]['series'])[0]
        counter=0
        for device in tb_data['devices']:
            tb_data['devices'][device]['connections']["a"] = {
                "protocol": "ssh",
                "ip": self.devinfo[list(self.devinfo.keys())[counter]]['managementIpAddress'],
                "port": 22,
                "ssh_options": " -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null",
               "arguments": {
                    "learn_hostname": "true"}
            }
            counter += 1
        tb_data['topology'] = self.generate_cdp_data()
        with open(self.tb_file, 'w') as tbfile:
            yaml.dump(tb_data, tbfile, default_flow_style=False)
        return tb_data
    def update_hostname(self):
        """
        :type device_list: list
        """
        result = True
        for device in self.devinfo:
            self.devinfo[device]['hostname'] = self.devinfo[device]['hostname'].split(".")[0]
            hostname = self.execute_command_on_device(self.devinfo[device]['id'], "show run | i hostname")
            if hostname['result'] and  hostname['output']!= "":
                #self.devinfo[device]['hostname'] = re.findall("\nhostname\s+(\S+)\n",hostname['output'])[0]
                print(hostname)
            else:
                print("Unable to get hostname from device")
                result = False
        return result
    def collect_device_info(self):
        """
        :type device_list: list
        """
        if not self.get_network_device_info([self.device1_ip, self.device2_ip]):
            self.log.error("Failed to get device info, Both devices are not yet available"+
                           " in DNAC, run the utility only when both SVL switches are in DNAC")
            return False
        return True
    
    def delete_device_from_inventory(self, devid, clean_config=False):
        """Unprovision method cleanup config and deletes device from inventory
         :param dev: device to be deleted
         :param clean_config: whether or not configs should be cleaned
         """
        self.log.info(f"Deleting device {devid} from inventory")
        params = {"networkDeviceId" : devid}
        response = self.dnac.call_api(method="GET", resource_path="/v2/data/customer-facing-service/DeviceInfo/", params=params)
        if not response["response"]:
            # device not provisioned
            url = "/v1/inventory/delete/bulk"
            data = [{"instanceUuid": devid, "cleanConfig": clean_config}]
            response = self.dnac.call_api(method="DELETE", data=data, resource_path=url)
            taskStatus = self.wait_for_task_complete(response)
            if taskStatus['isError']:
                self.log.error("Device deletion failed: {}".format(taskStatus))
                return False
            else:
                self.log.info("Device deletion is Success")
                return True
        id2 = response["response"][0]["id"]
        url = "/v2/data/customer-facing-service/DeviceInfo/{}".format(id2)
        self.log.info(url)
        params = {"correlationData": '{"cleanConfig":false}'}
        if not clean_config:
            response = self.dnac.call_api(method= "DELETE", resource_path=url, params=params)
        else:
            response = self.dnac.call_api(method="DELETE", resource_path=url)
        taskStatus = self.wait_for_task_complete(response)
        if taskStatus['isError']:
            self.log.error("Device deletion failed: {}".format(taskStatus))
            return False
        else:
            self.log.info("Device deletion is Success")
            return True
    #Force sync NW Device
    def force_sync(self, device_id):
        """
        data = [device_id]
        PUT /api/v1/network-device/sync?forceSync=true
        ParamsHeadersPutResponseJSON
        Source
        ["9834cfb8-f2b3-4c95-a3a6-42bb8dfa1054"]
        """
        params = {"forceSync": "true"}
        url = "/v1/network-device/sync"
        data = [device_id]
        response = self.dnac.call_api(method="PUT", data=data, resource_path=url, params=params)
        taskStatus = self.wait_for_task_complete(response)
        self.log.info(taskStatus)
        if taskStatus['isError']:
            self.log.error("Device sync failed: {}".format(taskStatus))
            return False
        else:
            self.log.info("Device sync is Success")
            return True

#main function
if __name__ == '__main__':
    #Initiate the client
    if len(sys.argv) > 1 and (sys.argv[1] == "help" or sys.argv[1] == "-h" or \
        sys.argv[1] == "--help" or sys.argv[1] == "-help" or sys.argv[1] == "--h" or \
            sys.argv[1] == "?"):
        print("\nUsage: python3 ./svlservices/client_manager.py <cluster_ip> "+
              "<username> <password> <device1_ip> <device2_ip> <device_user> "+
              "<device_pass> <device_enable_pass>\n")
        exit()
    elif len(sys.argv) == 9:
        clusterip = sys.argv[1] 
        clusteradmin = sys.argv[2] 
        clusteradminpass = sys.argv[3] 
        device1_ip = sys.argv[4]
        device2_ip = sys.argv[5]
        deviceuser = sys.argv[6]
        devicepass = sys.argv[7]
        deviceenablepass = sys.argv[8]        
    else:
        clusterip = input("Enter the DNAC IP address: ")
        clusteradmin = input("Enter the DNAC admin username: ")
        clusteradminpass = getpass.getpass("Enter the DNAC admin password: ")
        device1_ip = input("Enter the SVL switch 1 IP address: ")
        device2_ip = input("Enter the SVL switch 2 IP address: ")
        deviceuser = input("Enter the SVL switch username: ")
        devicepass = getpass.getpass("Enter the SVL switch password: ")
        deviceenablepass = getpass.getpass("Enter the SVL switch enable password: ")
    print("clusterip: ", clusterip)
    print("clusteradmin: ", clusteradmin)
    print("clusteradminpass: ", clusteradminpass)
    print("device1_ip: ", device1_ip)
    print("device2_ip: ", device2_ip)
    print("deviceuser: ", deviceuser)
    print("devicepass: ", devicepass)
    print("deviceenablepass: ", deviceenablepass)
    client = SVLFormation(clusterip, clusteradmin, clusteradminpass,
                          device1_ip, device2_ip, deviceuser, 
                          devicepass,deviceenablepass
                          )
    logger.info("Network device info")
    if not client.collect_device_info():
        client.log.error("Failed to get device info, Both devices are not yet available in DNAC")
        sys.exit(1)
    '''
    '''
    client.collect_device_info()
    if client.update_hostname():
        logger.info("Hostname updated successfully")
    else:
        logger.error("Failed to update hostname")
        sys.exit(1)
    print(client.get_both_switches_cdp_data())
    if len(list(client.devinfo.keys())) != 2:
        logger.error("Both devices are not yet available in DNAC")
        logger.error("Run the utility only when both SVL switches are in DNAC")
        sys.exit(1)
    else:
        logger.info("Both devices are available in DNAC")
    client.generate_cdp_data()
    pprint.pprint(client.update_testbed_file())
    #get user input id to continue or not
    uinput = input("Do you want to continue with the testbed file update? (y/n): ")
    testbed = loader.load(tb_file)
    svl_handle = StackWiseVirtual(testbed)
    logger.info(svl_handle)
    svl_handle.get_device_pairs(svlPair=None)
    result = True
    for stackpair in svl_handle.device_pair_list:
        if not svl_handle.check_links(stackpair):
            logger.error("The devices provided to be paired into SVL does not have any links connected to each others")
            result=False
    if not result:
        logger.error("The devices provided to be paired into SVL does not have correct links connected to each others")
        sys.exit(1)
    else:
        logger.info("The devices provided to be paired into SVL have correct links connected to each others")
    for stackpair in svl_handle.device_pair_list:
        if not svl_handle.connect_to_stackpair(stackpair):
            result=False
            logger.error("Could not connect to devices, Can not proceed. for stackwise virtual pair :{}".format(stackpair))
    if not result:
        logger.error("Could not connect to devices, Can not proceed.")
        sys.exit(1)
    else:
        logger.info("Connected to devices")
    for stackpair in svl_handle.device_pair_list:
        if not svl_handle.check_min_version_req(stackpair):
            result=False
            logger.error("Existing SVL Check/Minimum Version/Stack status failed for switchpair:{}, fix it before moving further".format(stackpair))
        else:
            logger.info("Existing SVL Check/Minimum Version/Stack status passed for switchpair:{}".format(stackpair))
    if not result:
        logger.error("Existing SVL Check/Minimum Version/Stack status failed, fix it before moving further")
        sys.exit(1)
    else:
        logger.info("Existing SVL Check/Minimum Version/Stack status passed")
    for stackpair in svl_handle.device_pair_list:
        if not svl_handle.configure_svl_step1(stackpair):
            result=False
            logger.error("Step1 Configure the step 1 config, switch number and domain configs on switches, failed")
        else:
            logger.info("Step1 Configure the step 1 config, switch number and domain configs on switches, passed")
        if not svl_handle.configure_svl_step2_svllinkconfig(stackpair):
            result=False
            logger.error("Step2 Config stackwise Virtual links on switches, failed.")
        else:
            logger.info("Step2 Config stackwise Virtual links on switches, passed.")
        if not svl_handle.connect_to_stackpair(stackpair):
            result=False
            logger.error("Could not connect to devices, Can not proceed. for stackwise virtual pair :{}".format(stackpair))
        else:
            logger.info("Connected to devices")
            
        if not svl_handle.configure_svl_step3_dad_linkconfig(stackpair):
            result=False
            logger.error("Step3 Configuring stackwise Virtual Dual Active Detection Links, failed.")
        else:
            logger.info("Step3 Configuring stackwise Virtual Dual Active Detection Links, passed.")
        svl_handle.update_device_config_with_new_link_numbers(stackpair)
        svl_handle.configure_updated_config_in_the_switches(stackpair)
        if not svl_handle.save_config_and_reload(stackpair,reloadAsync=True):
            result=False
            logger.error("Step6 Save config and reload the switches, failed.")
        else:
            logger.info("Step6 Save config and reload the switches, passed.")
    if not result:
        logger.error("SVL Formation failed")
        sys.exit(1)
    else:
        logger.info("SVL Formation passed")
    for stackpair in svl_handle.device_pair_list:
        if not svl_handle.remove_interface_config_eem_config_after_svl_formation(stackpair):
            result=False
            logger.error("Update interface config after SVL formation failed for stackwise virtual pair :{}".format(stackpair))
        else:
            logger.info("Update interface config after SVL formation passed for stackwise virtual pair :{}".format(stackpair))
    if not result:
        logger.error("SVL Formation failed")
    else:
        logger.info("SVL Formation passed")
    for stackpair in svl_handle.device_pair_list:
        if not svl_handle.check_stackwise_virtual_confgured(stackpair):
            result=False
            logger.error("Stackwise Virtual configs are still present on one or both of the switches of stackpair: {}".format(stackpair))
        else:
            logger.info("Stackwise Virtual configs are removed from both of the switches of stackpair: {}".format(stackpair))
    if not result:
        logger.error("SVL Formation failed")
    else:
        logger.info("SVL Formation passed")
    for stackpair in svl_handle.device_pair_list:
        if not svl_handle.validate_stackwise_SVL_and_DAD_links_status(stackpair):
            result=False
            logger.error("Stackwise Virtual and DAD links are not up on one or both of the switches of stackpair: {}".format(stackpair))
        else:
            logger.info("Stackwise Virtual and DAD links are up on both of the switches of stackpair: {}".format(stackpair))
    if not result:
        logger.error("SVL Formation failed")
    else:
        logger.info("SVL Formation passed")
    for stackpair in svl_handle.device_pair_list:
        primary_ip = str(stackpair['stackwiseVirtualDev'].connections['a'].ip)
        secondary_ip = device1_ip if primary_ip == device2_ip else device2_ip
        if result:
            client.delete_device_from_inventory(client.devinfo[secondary_ip]['id'], clean_config=False)
            print(client.force_sync(client.devinfo[primary_ip]['id']))
    if result:
        logger.info("SVL Formation passed")
    else:
        logger.error("SVL Formation failed")
    print("SVL Formation Completed")

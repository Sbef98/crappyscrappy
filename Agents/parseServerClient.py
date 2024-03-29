# let's import a library that allows for rest calls
import requests
import json
# let's import the ParseQuery class
from parseQuery import ParseQuery as Query
import websocket
import threading
import time

# let's now create a class called "ParseEnvironmentHandler" that will manage the connection to Parse Server
class ParseServerClient:
    # let's create a constructor that will take as input the url of the Parse Server and the application id
    def __init__(self, parse_server_url, parse_application_id, rest_api_key=None):
        self.parse_server_url = parse_server_url
        self.parse_application_id = parse_application_id
        self.rest_api_key = rest_api_key

    # let's now create the methods that allow for basic CRUD operartions on parse server
    # let's start with the create method
    def create(self, object_class, object):
        # let's create the url
        url = self.parse_server_url + '/classes/' + object_class
        # let's create the headers
        headers = {
            'X-Parse-Application-Id': self.parse_application_id,
            'Content-Type': 'application/json',
            'X-Parse-REST-API-Key': self.rest_api_key
        }
        # let's make the call
        response = requests.post(url, headers=headers, json=object)
        # let's return the response
        return response.json()
    
    # let's now create the read method
    def read(self, object_class, object_id):
        # let's create the url
        url = self.parse_server_url + '/classes/' + object_class + '/' + object_id
        # let's create the headers
        headers = {
            'X-Parse-Application-Id': self.parse_application_id,
            'Content-Type': 'application/json',
            'X-Parse-REST-API-Key': self.rest_api_key
        }
        # let's make the call
        response = requests.get(url, headers=headers)
        # let's return the response
        return response.json()
    
    # let's now create the update method
    def update(self, object_class, object_id, object):
        # let's create the url
        url = self.parse_server_url + '/classes/' + object_class + '/' + object_id
        # let's create the headers
        headers = {
            'X-Parse-Application-Id': self.parse_application_id,
            'Content-Type': 'application/json',
            'X-Parse-REST-API-Key': self.rest_api_key
        }
        if("className" in object):
            del object["className"]
        # let's make the call
        response = requests.put(url, headers=headers, json=object)
        # let's return the response
        return response.json()
    
    # let's query the database downloading all the elements of a given class
    def queryAll(self, object_class):
        # let's create the url
        url = self.parse_server_url + '/classes/' + object_class
        # let's create the headers
        headers = {
            'X-Parse-Application-Id': self.parse_application_id,
            'Content-Type': 'application/json',
            'X-Parse-REST-API-Key': self.rest_api_key
        }
        # let's make the call
        response = requests.get(url, headers=headers)
        # let's return the response loading the jsons into a list of objects
        return response.json()['results']
    
    # let's now create the delete method
    def delete(self, object_class, object_id):
        # let's create the url
        url = self.parse_server_url + '/classes/' + object_class + '/' + object_id
        # let's create the headers
        headers = {
            'X-Parse-Application-Id': self.parse_application_id,
            'Content-Type': 'application/json',
            'X-Parse-REST-API-Key': self.rest_api_key
        }
        # let's make the call
        response = requests.delete(url, headers=headers)
        # let's return the response
        return response.json()
    
    def query(self, parse_query):
        # Create the URL
        url = self.parse_server_url + '/classes/' + parse_query.className

        # Create the headers
        headers = {
            'X-Parse-Application-Id': self.parse_application_id,
            'Content-Type': 'application/json',
            'X-Parse-REST-API-Key': self.rest_api_key
        }

        # Create the parameters
        params = {
            'where': json.dumps(parse_query.filters)
        }
        if parse_query.limit_value is not None:
            params['limit'] = parse_query.limit_value
        if parse_query.skip_value is not None:
            params['skip'] = parse_query.skip_value
        if parse_query.aggregation_value is not None:
            params['aggregation'] = parse_query.aggregation_value
        if len(parse_query.include_value) > 0:
            params['include'] = ",".join(parse_query.include_value)

        # Make the GET request
        response = requests.get(url, headers=headers, params=params)
        # get the value of the response
        value = response.json()
        # dump the json into a list into a dictionary
        value = value['results']
        return value
    
    def getPointerToObject(self, object, type):
        if(not object["objectId"]):
            # throw an exception, you cannot create a point to an unexisting object bodoh!
            raise Exception("You cannot create a point to an unexisting object, bodoh!")
        pointer = {
            "__type": "Pointer",
            "className": type,
            "objectId": object["objectId"]
        }
        
        return pointer 

class LiveQueryClient:
    def __init__(self, app_id, clientKey, server_url):
        self.app_id = app_id
        self.clientKey = clientKey
        self.server_url = server_url
        self.websocket = None
        self.subscriptions = {}
        self.observers = []
        self.connect()

    def connect(self):
        self.websocket = websocket.create_connection(f"{self.server_url.replace('http', 'ws')}/parse")
        self._authenticate()

        # Start a thread to listen to the WebSocket messages
        threading.Thread(target=self._receive_messages).start()

    def _authenticate(self):
        auth_data = {
            "op": "connect",
            "applicationId": self.app_id,
            "clientKey": self.clientKey
        }
        self.websocket.send(json.dumps(auth_data))

    def _receive_messages(self):
        while True:
            try:
                message = self.websocket.recv()
                self._handle_message(message)
            except Exception as e:
                print(f"WebSocket error: {str(e)}")
                break

    def _handle_message(self, message):
        data = json.loads(message)
        for observer in self.observers:
            observer(data.get('op'), data.get('object'))

    def subscribe(self, class_name, callback, query = None):
        if(query is not None):
            subscription_data = {
                "op": "subscribe",
                "requestId": 1,  # Change this requestId for multiple subscriptions
                "query": {
                    "className": class_name,
                    "where": query
                }
            }
            # query = {"classname": "Node"}
        else:
            subscription_data = {
                "op": "subscribe",
                "requestId": 1,  # Change this requestId for multiple subscriptions
                "query": {
                    "className": class_name,
                    "where": {}
                }
            }
        self.websocket.send(json.dumps(subscription_data))
        self.observers.append(callback)

    def unsubscribe(self, subscription_id):
        unsubscribe_data = {
            "op": "unsubscribe",
            "requestId": 1,  # Change this requestId for multiple subscriptions
            "subscriptionId": subscription_id
        }
        self.observers = []
        return self.websocket.send(json.dumps(unsubscribe_data))

    def addCallback(self, callback):
        self.observers.append(callback)



def test_handle_message(operation, data):
        if operation == 'connected':
            print("Connected to LiveQuery")
        elif operation == 'error':
            print(f"Error: {data}")
        elif operation == 'subscribed':
            print(f"Subscribed to query: {data}")
        elif operation == 'unsubscribed':
            print(f"Unsubscribed from query: {data}")
        elif operation == 'create' or operation == 'update' or operation == 'delete':
            print(f"Object {operation}d: {data}")

if __name__ == "__main__":
    # let's read url, appId and masterKey from the environment variables saved in environment.json
    with open('environment.json', 'r') as f:
        environment = json.load(f)
    # let's create the ParseServerClient object
    parseServerClient = ParseServerClient(environment['serverURL'], environment['appId'], environment['restApiKey'])
    
    # let's create a live query client
    live_query_client = LiveQueryClient(environment['appId'], environment['clientKey'], environment['serverURL'])

    # Subscribe to the class Node
    live_query_client.subscribe("Node", test_handle_message)
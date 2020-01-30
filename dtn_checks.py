#!/usr/bin/env python3
"""
Monitor GO endpoint servers 

Based on tutorial and documentation at:
   http://globus.github.io/globus-sdk-python/index.html
-Galen Arnold, 2020, NCSA
"""
import time
import os
import re
import subprocess
import json
import webbrowser
import sys
from getpass import getpass
import globus_sdk

# some globals
CLIENT_ID = '2316-your-id-here-62da7'
MB = 1048576
TOKEN_FILE = 'refresh-tokens-bw.json'
REDIRECT_URI = 'https://auth.globus.org/v2/web/auth-code'
SCOPES = 'openid email profile urn:globus:auth:scope:transfer.api.globus.org:all'

def is_remote_session():
    """Test if this is a remote ssh session"""
    return os.environ.get('SSH_TTY', os.environ.get('SSH_CONNECTION'))


def load_tokens_from_file(filepath):
    """Load a set of saved tokens."""
    tokens = None
    try:
        with open(filepath, 'r') as tokenfile:
            tokens = json.load(tokenfile)
    except FileNotFoundError:
        pass
    except BaseException:
        sys.stderr.write("Failed to read tokens from {}\n".format(filepath))
    return tokens


def load_state_from_file(filepath):
    """Load paused state."""
    state = {}
    try:
        with open(filepath, 'r') as statefile:
            state = json.load(statefile)
    except FileNotFoundError:
        pass
    except BaseException:
        sys.stderr.write("Failed to read paused state from {}\n".format(filepath))
    return state


def save_tokens_to_file(filepath, tokens):
    """Save a set of tokens for later use."""
    try:
        with open(filepath, 'w') as tokenfile:
            json.dump(tokens, tokenfile)
    except BaseException:
        sys.stderr.write("Failed while saving tokens to {}\n".format(filepath))
        # TOKENS_NOT_SAVED = True


def save_state_to_file(filepath, state):
    """Save a set of tokens for later use."""
    try:
        with open(filepath, 'w') as statefile:
            json.dump(state, statefile)
    except BaseException:
        sys.stderr.write("Failed while saving state to {}\n".format(filepath))


def update_tokens_file_on_refresh(token_response):
    """
    Callback function passed into the RefreshTokenAuthorizer.
    Will be invoked any time a new access token is fetched.
    """
    save_tokens_to_file(TOKEN_FILE, token_response.by_resource_server)


def do_native_app_authentication(client_id, redirect_uri,
                                 requested_scopes=None):
    """
    Does a Native App authentication flow and returns a
    dict of tokens keyed by service name.
    """
    client = globus_sdk.NativeAppAuthClient(client_id=client_id)
    # pass refresh_tokens=True to request refresh tokens
    client.oauth2_start_flow(requested_scopes=requested_scopes,
                             redirect_uri=redirect_uri,
                             refresh_tokens=True)

    url = client.oauth2_get_authorize_url()

    print('Native App Authorization URL:\n{}'.format(url))

    if not is_remote_session():
        webbrowser.open(url, new=1)

    auth_code = getpass('Enter the auth code: ')

    token_response = client.oauth2_exchange_code_for_tokens(auth_code)

    # return a set of tokens, organized by resource server name
    return token_response.by_resource_server


#@profile
def my_endpoint_manager_server_check(tclient, endpoint):
    """
    Check for endpoint server responses on gsiftp well known port 2811:
        
    This routine forks a callout to the system curl (linux ) to do the
    checking.  There's probably a pure-python way of doing it but this works. 

    Parameters
    ----------
    tclient : globus transfer client object
    endpoint : GO endpoint long alpha-numeric id , string

    """
    

    myendpoint= tclient.endpoint_manager_get_endpoint(endpoint, num_results=None)
    # the DATA section contains the list of servers for an endpoint
    for server in myendpoint["DATA"]:
        mygsiftpstring="http://" + server["hostname"] + ":2811"
        # bwpy python 3.5.5, and older version of curl circa 2015-2016
        #mycheck= subprocess.run(["curl",mygsiftpstring],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=15)
        # python 3.7.5 on kali development platform , latest and greatest 2020
        mycheck= subprocess.run(["curl","--http0.9",mygsiftpstring],capture_output=True, timeout=15)
        if (re.search("GridFTP Server",str(mycheck.stdout),flags=0)):
            print(server["hostname"]," :ok")
        # Sometimes curl will crash python in subprocess.run above
        # and other times it returns an error to be caught here.
        # Note, this code will crash or exit on the 1st unresponsive server. 
        # There may be other servers down/unresponsive for an endpoint.
        # The purpose is to fail a Jenkins test.
        if (mycheck.returncode):
            print(server["hostname"]," :NOT ok")
            sys.exit( -1 )


def main():
    """
    main program
    """
    ENDPOINTS = (
        'ncsa#BlueWaters',
        'ncsa#BlueWaters-Duo',
        'umn#pgc-terranova',
        )

    tokens = load_tokens_from_file(TOKEN_FILE)

    if not tokens:
        # if we need to get tokens, start the Native App authentication process
        tokens = do_native_app_authentication(CLIENT_ID, REDIRECT_URI, SCOPES)
        save_tokens_to_file(TOKEN_FILE, tokens)

    transfer_tokens = tokens['transfer.api.globus.org']

    auth_client = globus_sdk.NativeAppAuthClient(client_id=CLIENT_ID)

    authorizer = globus_sdk.RefreshTokenAuthorizer(
        transfer_tokens['refresh_token'],
        auth_client,
        access_token=transfer_tokens['access_token'],
        expires_at=transfer_tokens['expires_at_seconds'],
        on_refresh=update_tokens_file_on_refresh)

    tclient = globus_sdk.TransferClient(authorizer=authorizer)

    # for the GO endpoints listed above ...
    for endpoint in ENDPOINTS:
        # Find the endpoint with search so that a replaced endpoint
        # with a replacement id will still be checked.
        for myep in tclient.endpoint_search(filter_fulltext=endpoint):
            # Isolate the search results to an exact match by forcing
            # /^endpoint$/  as the regex search we are matching.
            epsearchstring= "^" + endpoint + "$"
            if (re.search(epsearchstring,myep['display_name'],flags=0)):
                print("-->",myep['display_name'], myep['id'])
                my_endpoint_manager_server_check(tclient, myep['id'])

# end def main()

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Monitor Nearline endpoint


Based on tutorial and documentation at:
   http://globus.github.io/globus-sdk-python/index.html
-Galen Arnold, 2018, NCSA
"""
import time
import os
import globus_sdk
import json
import webbrowser
import pprint

# some globals
CLIENT_ID = '231634e4-37cc-4a06-96ce-12a262a62da7'
DEBUG = 0
TIMEOUT = 60
MB = 1048576
NOTIFY_SIZE = 100000
RECIPIENTS = "gwarnold@illinois.edu,gbauer@illinois.edu"
RECIPIENTS = "gwarnold@illinois.edu,help+bwstorage@ncsa.illinois.edu"
GLOBUS_CONSOLE = "https://www.globus.org/app/console/tasks/"
DISPLAY_ONLY_SIZE = NOTIFY_SIZE
PAUSE_SIZE = NOTIFY_SIZE
SRCDEST_FILES = 500
SLEEP_DELAY = 3600
# dictionary for testing to maintain state of tasks that would have been paused
MYTASKPAUSED = {}
TOKEN_FILE = 'refresh-tokens.json'
REDIRECT_URI = 'https://auth.globus.org/v2/web/auth-code'
SCOPES = ('openid email profile '
          'urn:globus:auth:scope:transfer.api.globus.org:all')
# endpoints determined by globus cli: globus endpoint search ncsa#jyc
#  or from globus.org -> "Manage Endpoints" -> endpoint detail, UUID
EP_BW = "d59900ef-6d04-11e5-ba46-22000b92c6ec"
EP_JYC = "d0ccdc02-6d04-11e5-ba46-22000b92c6ec"
EP_NEARLINE = "d599008e-6d04-11e5-ba46-22000b92c6ec"

GET_INPUT = getattr(__builtins__, 'raw_input', input)


def is_remote_session():
    """ Test if this is a remote ssh session """
    return os.environ.get('SSH_TTY', os.environ.get('SSH_CONNECTION'))


def load_tokens_from_file(filepath):
    """Load a set of saved tokens."""
    with open(filepath, 'r') as tokenfile:
        tokens = json.load(tokenfile)

    return tokens


def save_tokens_to_file(filepath, tokens):
    """Save a set of tokens for later use."""
    with open(filepath, 'w') as tokenfile:
        json.dump(tokens, tokenfile)


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

    print('Native App Authorization URL: \n{}'.format(url))

    if not is_remote_session():
        webbrowser.open(url, new=1)

    auth_code = GET_INPUT('Enter the auth code: ').strip()

    token_response = client.oauth2_exchange_code_for_tokens(auth_code)

    # return a set of tokens, organized by resource server name
    return token_response.by_resource_server


def add_notification_line(task, endpoint_is):
    """
    Append task info to a file to send vial email.
    """
    mail_file = open('large_xfer.txt', 'a')
    mail_file.write("{1:5s} {2:36s} {3:10d} {0}\n".format(
        task["owner_string"], endpoint_is,
        task["task_id"],
        task["files"]))
    mail_file.close()


def my_endpoint_manager_task_list(tclient, endpoint):
    """
    Monitor the endpoint for potential issues related to transfers:
        - too many files
        - DEST == SRC
    """
    source_total_files = dest_total_files = 0
    source_total_bps = dest_total_bps = 0
    source_total_tasks = dest_total_tasks = 0

    for task in tclient.endpoint_manager_task_list(filter_endpoint=endpoint, num_results=None):
        if task["status"] == "ACTIVE":
            if task["destination_endpoint_id"] == endpoint:
                endpoint_is = "DEST"
                dest_total_files += task["files"]
                dest_total_bps += task["effective_bytes_per_second"]
                dest_total_tasks += 1
            else:
                endpoint_is = "SRC"
                source_total_files += task["files"]
                source_total_bps += task["effective_bytes_per_second"]
                source_total_tasks += 1
            if (task["destination_endpoint_id"] == endpoint) and (task["source_endpoint_id"] == endpoint):
                if task["files"] > SRCDEST_FILES:
                    if MYTASKPAUSED.get(str(task["task_id"])) is None:
    #               if not task["is_paused"]:
    #                   tclient.endpoint_manager_pause_tasks([task["task_id"] ],"SRC and DEST endpoint are the same.  A new Jira issue has been created.")
                        print("{} for {} PAUSED.".format(task["task_id"], task["owner_string"]))
                        globus_url = GLOBUS_CONSOLE + str(task["task_id"])
                        detail_file = open('task_detail.txt', 'w')
                        detail_file.write("Click link to view in the GO console: {}\n".
                                          format(globus_url))
                        pprint.pprint(str(task), stream=detail_file, depth=1, width=50)
                        detail_file.close()
                        os.system("mail -s " + "PAUSED_SRC=DEST:" + task["owner_string"] +
                                  " " + RECIPIENTS + " < task_detail.txt")
                        MYTASKPAUSED[str(task["task_id"])] = 1
                    else:
                        print("{} for {} was already PAUSED.".format(task["task_id"],
                                                                     task["owner_string"]))
                        continue
                endpoint_is = "DEST_SRC"
                dest_total_files += task["files"]
                dest_total_bps += task["effective_bytes_per_second"]
                dest_total_tasks += 1
                source_total_files += task["files"]
                source_total_bps += task["effective_bytes_per_second"]
                source_total_tasks += 1
            if (task["files"] > PAUSE_SIZE) and (endpoint_is == "DEST"):
                if MYTASKPAUSED.get(str(task["task_id"])) is None:
#               if not task["is_paused"]:
#                   tclient.endpoint_manager_pause_tasks([task["task_id"] ],"File Count exceeds endpoint transfer limit.  A new Jira issue has been created.")
                    print("{} for {} PAUSED.".format(task["task_id"], task["owner_string"]))
                    globus_url = GLOBUS_CONSOLE + str(task["task_id"])
                    detail_file = open('task_detail.txt', 'w')
                    detail_file.write("Click link to view in the GO console: {}\n".
                                      format(globus_url))
                    pprint.pprint(str(task), stream=detail_file, depth=1, width=50)
                    detail_file.close()
                    os.system("mail -s " + "PAUSED_NFILES:" + task["owner_string"] +
                              " " + RECIPIENTS + " < task_detail.txt")
                    MYTASKPAUSED[str(task["task_id"])] = 1
                else:
                    print("{} for {} was already PAUSED.".format(task["task_id"],
                                                                 task["owner_string"]))
                    continue
            if (task["files"] > DISPLAY_ONLY_SIZE) or (endpoint_is == "DEST_SRC"):
                print("{1:10s} {2:36s} {3:10d} {0}".format(task["owner_string"], endpoint_is,
                                                           task["task_id"],
                                                           task["files"]))
                if (task["files"] > NOTIFY_SIZE) or (endpoint_is == "DEST_SRC"):
                    add_notification_line(task, endpoint_is)
    # end for
    print("...TOTAL.files..tasks..MBps...")
    print("SRC  {:9d}  {:4d}  {:6.1f}".format(
        source_total_files, source_total_tasks, source_total_bps/MB))
    print("DEST {:9d}  {:4d}  {:6.1f}".format(
        dest_total_files, dest_total_tasks, dest_total_bps/MB))


def main():
    """
    main program
    """
    tokens = None
    try:
        # if we already have tokens, load and use them
        tokens = load_tokens_from_file(TOKEN_FILE)
    except IOError:
        pass

    if not tokens:
        # if we need to get tokens, start the Native App authentication process
        tokens = do_native_app_authentication(CLIENT_ID, REDIRECT_URI, SCOPES)

        try:
            save_tokens_to_file(TOKEN_FILE, tokens)
        except IOError:
            pass

    transfer_tokens = tokens['transfer.api.globus.org']

    auth_client = globus_sdk.NativeAppAuthClient(client_id=CLIENT_ID)

    authorizer = globus_sdk.RefreshTokenAuthorizer(
        transfer_tokens['refresh_token'],
        auth_client,
        access_token=transfer_tokens['access_token'],
        expires_at=transfer_tokens['expires_at_seconds'],
        on_refresh=update_tokens_file_on_refresh)

    tclient = globus_sdk.TransferClient(authorizer=authorizer)

    while True:
        print("...Nearline..........task.[ACTIVE]............Nfiles.....owner...")
        my_endpoint_manager_task_list(tclient, EP_NEARLINE)
        if os.path.isfile("./large_xfer.txt"):
            print("found large_xfer.txt, handling...")
            os.system("cat -n large_xfer.txt")
#           os.system("mail -s ncsa#Nearline_many_file_xfers " + RECIPIENTS + " < ./large_xfer.txt")
            os.system("rm large_xfer.txt")
        print("...sleeping {}s...\n".format(SLEEP_DELAY))
        time.sleep(SLEEP_DELAY)
        # end while
# end def main()


main()

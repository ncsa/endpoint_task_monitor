# endpoint_task_monitor
A Globus Online python script to monitor ncsa#Nearline for issues of interest to our admin team:
  * too many files
  * SRC = DEST

# spoke_cli.sh
A Globus Online cli bash example showing a couple transfers to endpoints.  This is the most reliable way to know that the service is working (end to end test with a small file).
Sample output from a test run (SUCCEEDED transfers are just that, ACTIVE or other status may warrant further inspection via the Globus Online web interface).
```
galen@DESKTOP-RLP6AB1:~/globus-cli$ ./spoke_cli.sh
Endpoint is already activated. Activation expires at 2022-02-11 20:11:37+00:00
globus transfer e673866c-c80e-11e9-9ced-0edb67dd7a14:~/globus_function_test befd43ff-939c-438a-a320-83036a3809e9:~/globus_function_test

Endpoint is already activated. Activation expires at 2022-02-18 22:22:52+00:00
globus transfer e673866c-c80e-11e9-9ced-0edb67dd7a14:~/globus_function_test d59900ef-6d04-11e5-ba46-22000b92c6ec:~/globus_function_test

Endpoint is already activated. Activation expires at 2022-02-18 22:22:52+00:00
globus transfer e673866c-c80e-11e9-9ced-0edb67dd7a14:~/globus_function_test 4d813574-ac17-11ea-bee8-0e716405a293:~/globus_function_test

task: 133e3ade-8aae-11ec-900b-3132d806a822
Status:                       SUCCEEDED
Destination Endpoint:         Illinois Research Storage
task: 14915380-8aae-11ec-8fde-dfc5b31adbac
Status:                       SUCCEEDED
Destination Endpoint:         ncsa#BlueWaters
task: 15aae600-8aae-11ec-900b-3132d806a822
Status:                       ACTIVE
Destination Endpoint:         ncsa#hal
galen@DESKTOP-RLP6AB1:~/globus-cli$
```

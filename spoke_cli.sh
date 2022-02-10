#globus endpoint search "Illinois Research Storage"
#
#ID                                   | Owner                                                        | Display Name

#------------------------------------ | ------------------------------------------------------------ | -----------------
-----------------------
#befd43ff-939c-438a-a320-83036a3809e9 | 4344ef6f-6f6e-4ba9-95c3-78979d9d62fe@clients.auth.globus.org | Illinois Research
 Storage
#2fa5cf3b-a1a4-4b4b-9389-121b40c2a40e | 4344ef6f-6f6e-4ba9-95c3-78979d9d62fe@clients.auth.globus.org | Illinois Research
 Storage - Box
#2f74f429-1d83-4b46-8350-f33238bb34ac | 4344ef6f-6f6e-4ba9-95c3-78979d9d62fe@clients.auth.globus.org | Illinois Research
 Storage - Google Drive

#globus session consent 'urn:globus:auth:scope:transfer.api.globus.org:all[*https://auth.globus.org/scopes/befd43ff-939c
-438a-a320-83036a3809e9/data_access]'

export EP_IRS=befd43ff-939c-438a-a320-83036a3809e9
export EP_BW=d59900ef-6d04-11e5-ba46-22000b92c6ec
export EP_HAL=4d813574-ac17-11ea-bee8-0e716405a293
export LOCAL_CLIENT=e673866c-c80e-11e9-9ced-0edb67dd7a14
#export LOCAL_CLIENT=cbec6a5c-b326-11eb-afd1-e1e7a67e00c1
export MYSCRATCH=\~/globus_function_test

rm my_task_list.txt

alleps=($EP_IRS $EP_BW $EP_HAL)
for EP in ${alleps[@]}; do
   globus endpoint activate $EP
   echo "globus transfer $LOCAL_CLIENT:$MYSCRATCH $EP:$MYSCRATCH"
   globus transfer $LOCAL_CLIENT:$MYSCRATCH $EP:$MYSCRATCH >> my_task_list.txt
   echo
done

sleep 25

for task in `cat my_task_list.txt | grep Task | cut -d: -f2`
do
   echo "task: $task"
   globus task show $task | grep Status
   globus task show $task | grep 'Destination Endpoint:'
done

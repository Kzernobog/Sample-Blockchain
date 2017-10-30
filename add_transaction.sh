#!/bin/bash
sender="$1"
recipient="$2"
amount="$3"
curl -X POST -H "Content-Type: application/json" -d '{"sender":"'$sender'","recipient":"'$recipient'","amount":"'$amount'"}' "http://localhost:5000/transactions/new" 

#!/bin/bash

# Use `MAC` when static IP cannot be set
# MAC="$(grep 'MAC='' secrets |cut -d'=' -f2)"
# Use `IP` when static IP set through DHCP
IP="$(grep 'IP=' secrets |cut -d'=' -f2)"

OUTFILE="../data/tesla_gateway_meter_data.csv"

LOGINCMD=(curl -s -k -i
          -c ./cookie.txt
          -X POST
          -H "Content-Type: application/json"
          -d @./creds.json
          https://$IP/api/login/Basic )

# echo "Logging in..."
max_retry=5
counter=0
until "${LOGINCMD[@]}" |grep token >/dev/null
do
    sleep 1
    [[ counter -eq $max_retry ]] && echo "Failed!" && exit 1
    #echo "Trying again. Try #$counter"
    ((counter++))
done

CMD1="curl -sk -b ./cookie.txt https://$IP/api/meters/aggregates"
CMD2="curl -sk -b ./cookie.txt https://$IP/api/system_status/soe"
CMD3="curl -sk -b ./cookie.txt https://$IP/api/system_status/grid_status"
CMD4="curl -sk -b ./cookie.txt https://$IP/api/system_status"

(echo "[" && $CMD1 && echo "," && $CMD2 && echo "," && $CMD3 && echo "," && $CMD4 && echo "]") | jq -r " \
    [ \
    .[0].load.last_communication_time, \
    .[0].site.instant_power, \
    .[0].load.instant_power, \
    .[0].solar.instant_power, \
    .[0].battery.instant_power, \
    .[1].percentage, \
    .[3].nominal_full_pack_energy, \
    .[2].grid_status \
    ]
    | @csv" |./format.py >> $OUTFILE

# Add last record to database
echo "$(tail -n1 $OUTFILE)" | ./add_api_rec_to_database.py

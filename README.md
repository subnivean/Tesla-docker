Code to get and store data from our Tesla gateway.

Requires a `src/creds.json` file, which looks like:

```
{"username":"customer",
 "password":"<last 5 chars of SN>",
 "email":"me@gmail.com",
 "force_sm_off":false}
```

Also requires a `src/secrets` file, which has the form:

```
MAC=<Tesla gateway MAC>
# Set through the Netgear Nighthawk R7000 router 
# ('Advanced' tab | Setup | LAN Setup, see 'Address Reservation' at bottom)
IP=<Tesla gateway ethernet IP>

# pygotrader
Algorithmic cryptocurrency trader written in Python

### Requirements
* Python 3.7+
* Modified coinbasepro-python library: https://github.com/jshahbazi/coinbasepro-python

### Installation instructions
This program is currently not on pypi.org and requires a forked version of the coinbasepro-python library, so for now you can use the following commands to install:
```
 pip install --upgrade git+git://github.com/jshahbazi/coinbasepro-python
 pip install --upgrade git+git://github.com/jshahbazi/pygotrader
```
Note that this will override any existing installation of the coinbasepro-python library.

### Running the program
To view only the current BTC-USD orders on Coinbase, you can simply run:
```
 pygotrader
```

To change the viewed coin to something, use the --product argument, i.e.:
```
 pygotrader --product 'ETH-USD'
```

To connect to an exchange with your API key and do limited trading (manual buys and sells at market price), 
use the --config argument and pass in a config file as described above.  Warning: Unless you choose 
to connect to a sandbox, you will be trading with actual money and cryptocurrency.
```
 pygotrader --config my_config
```

For help:
```
 pygotrader -h
```

### Config file format
To connect to an exchange and do actual trading (or connect to a sandbox and do fake trading), 
you will need to use a config file to pass in your API key and secret, and the URL to connect with.  
The file needs to be in json format:
```
{"key":"12345",
 "b64secret":"1l2o3o4n5g",
 "passphrase":"pass123",
 "api_url":"https://api-public.sandbox.pro.coinbase.com"
 "websocket_url":"wss://ws-feed-public.sandbox.pro.coinbase.com"
}
```
You will need to log into Coinbase Pro (or Coinbase Pro Sandbox) and create an API key on your own.

Note that the websocket feed for the Coinbase Pro Sandbox has little traffic, so it will end 
in an error with the current websocket-client library, which does not seem to have timeouts implemented 
properly.  This will be remedied in a future release. For now, use the websocket feed for the 
regular Coinbase Pro exchange: wss://ws-feed.pro.coinbase.com

### Uninstall
```
 pip uninstall cbpro
 pip uninstall pygotrader
```

### Performance Notes
* The infrastructure for Coinbase's exchange runs on AWS, so the best place to run this (or any sort of trading utlity) is AWS

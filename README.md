# pygotrader
Algorithmic cryptocurrency trader written in Python

### Installation instructions
This program is currently not on pypi.org, so for now you can use the following commands to install:
```
 git clone https://github.com/jshahbazi/pygotrader.git
 pip3 install --user .
```

### Running the program
To view only the current BTC-USD orders on Coinbase, you can simply run:
```
 pygotrader
```

To change the viewed coin to something, use the --product argument, i.e.:
```
 pygotrader --product 'ETH-USD'
```

For help:
```
 pygotrader -h
```

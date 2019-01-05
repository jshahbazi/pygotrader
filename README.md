# pygotrader
Algorithmic cryptocurrency trader written in Python

### Requirements
* Python 3.7+
* Modified coinbasepro-python library: https://github.com/jshahbazi/coinbasepro-python.git

### Installation instructions
This program is currently not on pypi.org and requires a forked version of the coinbasepro-python library, so for now you can use the following commands to install:
```
 git clone https://github.com/jshahbazi/coinbasepro-python.git
 pip install -e ./coinbasepro-python/
 git clone https://github.com/jshahbazi/pygotrader.git
 pip install -e ./pygotrader/
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

### Uninstall
From the application directory:
```
 python3 setup.py develop --uninstall
```

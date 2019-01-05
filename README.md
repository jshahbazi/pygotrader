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

For help:
```
 pygotrader -h
```

### Uninstall
```
 pip uninstall cbpro
 pip uninstall pygotrader
```

### Performance Notes
* The infrastructure for Coinbase's exchange runs on AWS, so the best place to run this (or any sort of trading utlity) is AWS

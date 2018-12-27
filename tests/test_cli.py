import pytest

from pygotrader import cli

@pytest.fixture
def parser():
    return cli.create_parser()

def test_parser_with_exchange(parser):
    """
    Parser exits if no exchange specified
    """
    args = parser.parse_args(["--exchange", "coinbase"])
    assert args.exchange == "coinbase"
        
def test_parser_without_exchange(parser):
    """
    Exit if no exchange specified
    """
    with pytest.raises(SystemExit):
        parser.parse_args([])
        
def test_parser_with_unknown_exchange(parser):
    """
    Parser will exit if exchange name is unknown
    """
    with pytest.raises(SystemExit):
        parser.parse_args(['--exchange','bittrex'])
        
def test_parser_with_known_exchange(parser):
    """
    Parser will not exit if exchange name is known
    """
    for exchange in ['coinbase']:
        assert parser.parse_args(['--exchange', exchange])

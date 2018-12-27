from argparse import Action, ArgumentParser

exchange_choices = ['coinbase']

class ExchangeAction(Action):
    def __call__(self, parser, namespace, values, option_string=None):
        exchange = values
        if exchange.lower() not in exchange_choices:
            parser.error("Unknown exchange")
        namespace.exchange = exchange.lower()

def create_parser():
    parser = ArgumentParser(description="")
    exchange_arg_help = f"Exchange to connect to.  Currently supported exchanges: {exchange_choices}"
    parser.add_argument("--exchange", 
        help=exchange_arg_help,
        metavar=("EXCHANGE"),
        action=ExchangeAction,
        required=True)
    return parser
    
def main():
    args = create_parser().parse_args()

    if args.exchange == 'coinbase':
        pass
    else:
        pass
import sys
import logging
import poker.deck as dec

formatter = logging.Formatter('%(asctime)s [%(module)14s]'
                              '[%(levelname)8s] %(message)s')
log = logging.getLogger()
log.setLevel(logging.INFO)

console = logging.StreamHandler(sys.stdout)
console.setFormatter(formatter)
log.addHandler(console)

log_file = logging.FileHandler('logfile.log', mode='w')
log_file.setFormatter(formatter)
log.addHandler(log_file)


def main():
    deck = dec.Deck()
    table = dec.Table(9)
    table.deal(deck)
    deck.flop()
    deck.add_community_card()
    deck.add_community_card()
    table.evaluate_hands(deck.community)
    table.best_hand()


if __name__ == '__main__':
    main()

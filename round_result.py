import click

from fn_helper import config, MusicLeagueClient


@click.command()
@click.argument('round_url', nargs=1)
def round_result(round_url):
    """ Shows the round result
    """
    members = config['MEMBERS']
    nicknames = {m['ml_handle'].lower(): m['nickname']
                 for m in members if 'ml_handle' in m}
    ml_client = MusicLeagueClient()
    ml_round_result = ml_client.parse_round(round_url)

    for handle, score in ml_round_result.vote_count:
        print("{} {}".format(nicknames[handle.lower()], score))

    winner = ml_round_result.vote_count[0][0]
    print("WINNER: {}".format(nicknames[winner.lower()]))


if __name__ == '__main__':
    round_result()

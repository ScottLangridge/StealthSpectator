import re
import time

import chess
import chess.svg

import requests


def get_fen(username):
    r = requests.get(f'https://lichess.org/@/{username}/mini')
    html = r.text

    if 'data-state' in html and 'result' not in html:
        # If game in progress, pull out the fen
        full_fen = html.split('data-state="')[1]
        full_fen = full_fen.split('"')[0]
        split_fen = full_fen.split(',')

        # Break into board setup, player colour and last move
        board_fen, to_move = split_fen[0].split(' ')
        player_colour = split_fen[1]
        last_move = split_fen[2]

        # Pull out clock times for both players
        times = re.findall(r'data-time="\d*">\d+:\d+<\/span>', html)
        opponent_time = re.sub(r'data-time="\d*">', '', times[0])[:-7]
        player_time = re.sub(r'data-time="\d*">', '', times[1])[:-7]

        # Flip the board if the player being spectated is black
        if player_colour == 'black':
            board_fen = '/'.join(reversed([x[::-1] for x in board_fen.split('/')]))

        # If it is the spectated player's move, set player to move to true, else false
        player_to_move = to_move == player_colour[0]

        return board_fen, player_time, opponent_time, player_colour, player_to_move, last_move

    else:
        # If no game is being played, return a blank board
        return 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq', '0:00', '0:00', 'white', False, ''


def write_page(fen, player_time, opponent_time, player_colour, player_to_move, last_move):
    # Basic html components
    css = '<style>body{background-color:#333333;}mark{background:#92b166;color:white;}div{display:block;margin:20px auto;width:600px}svg{display:block;margin:auto 0}p{font-family:Arial,sans-serif;color:white;}</style>'
    tile = '<head>\n<title>Stealth Spectator</title>\n</head>'
    refresh_js = '<script type="text/javascript">\nsetTimeout(() => {  location.reload(); }, 500);\n</script>'
    body_start = '<body>'
    body_end = '</body>'
    div_start = '<div>'
    div_end = '</div>'

    # Player times, highlighter player who's move it currently is
    if player_to_move:
        player_time = f'<p><mark>{str(player_time)}</mark></p>'
        opponent_time = f'<p>{str(opponent_time)}</p>'
    else:
        player_time = f'<p>{str(player_time)}</p>'
        opponent_time = f'<p><mark>{str(opponent_time)}</mark></p>'

    # Build the image of the board
    board = chess.Board(fen)
    board_svg = str(chess.svg.board(board, size=600))
    # Overwrite default colour scheme
    board_svg = board_svg.replace('#d18b47', '#8ca2ad')
    board_svg = board_svg.replace('#ffce9e', '#dee3e6')
    # Overwrite colours to highlight last move
    if last_move != '':
        for i in [last_move[:2], last_move[2:]]:
            # If player is black coords are inverted
            if player_colour == 'black':
                i = invert_square(i)

            pattern = i + r'" stroke="none" fill="#......"'
            board_svg = re.sub(pattern, pattern.replace('#......', '#92b166'), board_svg)

    with open('stealth_spectator.html', 'w') as f:
        f.write(
            css
            + body_start
            + tile
            + refresh_js
            + div_start
            + opponent_time
            + board_svg
            + player_time
            + div_end
            + body_end
        )


def invert_square(square):
    file = chr(ord('h') - (ord(square[0])) + ord('a'))
    rank = str(9 - int(square[1]))
    return file + rank


def run(player_username):
    while True:
        fen, player_time, opponent_time, player_colour, player_to_move, last_move = get_fen(player_username)
        write_page(fen, player_time, opponent_time, player_colour, player_to_move, last_move)
        time.sleep(1)

run('AsinusAureus')

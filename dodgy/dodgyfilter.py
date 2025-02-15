import math
import re
import sys
import chess
import chess.uci
import configparser

cfg = configparser.ConfigParser()
cfg.read(sys.argv[1])

LC0=cfg['DEFAULT']['LC0']
LC0_OPTIONS = cfg['LC0_OPTIONS']

SF=cfg['DEFAULT']['SF']
SF_NODES=cfg['DEFAULT']['SF_NODES']
SF_OPTIONS=cfg['SF_OPTIONS']
SF_NODES=int(cfg['DEFAULT']['SF_NODES'])

DELTA=float(cfg['DEFAULT']['DELTA'])

def safe_quit(eng):
    try:
        eng.quit()
    except:
        pass
    
def init_sf():
    sf = chess.uci.popen_engine(SF)
    sf.setoption(SF_OPTIONS)

    sf_handler = chess.uci.InfoHandler()
    sf.info_handlers.append(sf_handler)
    return sf, sf_handler

def init_lc0():
    engine = chess.uci.popen_engine(LC0)

    engine.uci()
    engine.setoption(LC0_OPTIONS)
    info_handler = chess.uci.InfoHandler()
    engine.info_handlers.append(info_handler)
    return engine, info_handler


def scale_score(cp):
    return (2/(1+math.exp(-0.004 * cp)) - 1)

def score(score_):
    score = sf_handler.info["score"][1].cp
    if score == None:
        if sf_handler.info["score"][1].mate > 0:
            return 1.0
        else:
            return -1.0
    #return 2*math.atan2(score*abs(score)/100000.0,1)/math.pi
    return scale_score(score)


def sf_value(epd):
    board = chess.Board()
    board.set_epd(epd)

    sf.ucinewgame()
    sf.position(board)

    sf.go(nodes=SF_NODES)
    val = score(sf_handler.info["score"][1])

    if board.turn:
        return val
    else:
        return -val


def value_head(epd):
    
    board = chess.Board()
    board.set_epd(epd)

    engine.ucinewgame()
    engine.position(board)

    engine.go(nodes=0)

    m = re.search("\\(Q:\\s+(-?\\d\\.\\d+)\\s*\\)", info_handler.info["string"])
    val = float(m.group(1))
    if board.turn:
        return val
    else:
        return -val


sf, sf_handler = init_sf()
engine, info_handler = init_lc0()

count = 0
while True:
    count = count + 1
    if count%100 == 0:
        sys.stderr.write("{}\n".format(count))
        sys.stderr.flush()
    line = sys.stdin.readline()
    if (line == None):
        break
    line = line.rstrip()
    if line == "":
        break
    try:
        diff = abs(sf_value(line)-value_head(line))
    except:
        safe_quit(sf)
        safe_quit(engine)
        sf, sf_handler = init_sf()
        engine, info_handler = init_lc0()
        sys.stderr.write("error. restarted engines.\n")
        sys.stderr.flush()
        continue
    
    if diff >= DELTA:
        #print(diff)
        print(line)
        sys.stdout.flush()
    
engine.quit()
sf.quit()



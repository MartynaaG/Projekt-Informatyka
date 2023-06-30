import atexit
import codecs
import csv
import random
from os.path import join
from statistics import mean
from copy import deepcopy 
"""to jest kopia gleboka, bo jak pisalem te ify do poprawnosci true i false
    to w ogole mi nie wchodzilo w te warunki moje(wydaje mi sie ze to przez to, 
    ze psychopy ma jakis problem z tym przepisaniem do previous_go i  Go/ NoGo)
    nw dlaczego ale znalazlem ze to ma pomoc i chyba pomoglo bo dziala i dobrze 
    wylapuje mi warunki, a nie zostawia pustego pola w miejscu correctness 
    w wynikach"""
import yaml
from psychopy import visual, event, logging, gui, core, constants
from itertools import combinations_with_replacement, product

# GLOBALS
clock=core.Clock()
RESULTS = list()    # lista, w ktorej beda zapisywane wyniki
RESULTS.append(['PART_ID', 'Trial_no','Reaction_time', 'Correctness',"Experiment", 'Sex', 'Age', 'Stim_type'])
"""info o identyfikatorze, nr triala liczac od 0, czasie reakcji, 
    poprawności na bodziec, trening/experyment, plec, wiek, circle/rect;
    RESULTS.append wpisuje nazwy kolumn, bez danych""" 

@atexit.register
def save_test_results():
    # funkcja zapisujaca wyniki kazdego badanego w pliku csv
    with open(join('results', PART_ID + '_test.csv'), 'w', encoding='utf-8') as test_file:
        test_writer = csv.writer(test_file)
        test_writer.writerows(RESULTS)
    logging.flush()


def show_image(win, file_name, size, key='f7'):     
    # funkcja wyswietlajaca obrazki
    image = visual.ImageStim(win=win, image=file_name, interpolate=True, size=size)
    image.draw()
    win.flip()
    clicked = event.waitKeys(keyList=['space'])
    if clicked == ['space']:
        win.flip()
    return


def show_info(win, file_name, insert=''):
    # funkcja wyswietlajaca tekst(insert-->mozna cos zmienic)
    msg = read_text_from_file(file_name, insert=insert)
    msg = visual.TextStim(win, color='black', text=msg, height=25, wrapWidth=1000)
    msg.draw()
    win.flip()
    key = event.waitKeys(keyList=['f7', 'space', 'right'], clearEvents = True)
    if key == ['f7']:   # awaryjne wyjscie z procedury
        abort_with_error('Experiment finished by user on info screen! f7 pressed.')
    win.flip()


def read_text_from_file(file_name, insert=''):  
    # potrzebne do show_info, odczytuje i moze dodac info
    if not isinstance(file_name, str):
        logging.error('Problem with file reading, filename must be a string')
            # okresla bledy
        raise TypeError('file_name must be a string')
    msg = list()
    with codecs.open(file_name, encoding='utf-8', mode='r') as data_file:
        for line in data_file:
            if not line.startswith('#'):  
                if line.startswith('<--insert-->'):
                    if insert:
                        msg.append(insert)
                else:
                    msg.append(line)
    return ''.join(msg)


def check_exit(key='f7'):   
    # wyjscie z procedury, moze sie tez przydaj jako osobna
    stop = event.getKeys(keyList=[key])
    if stop:
        abort_with_error('Eksperyment przerwany przez użytkownika! Naciśnięto klawisz {}.'.format(key))

def abort_with_error(err):
    # okresli nam blad, ale nw czy sie przyda, zostawmy imo
    logging.critical(err)
    raise Exception(err)


def dialog_pulp(): 
    # wyswietla okno dialogowe, zbiera inf o identyfikatorze, plci, wieku
    info={'IDENTYFIKATOR': '', u'P\u0141E\u0106': ['M', "K"], 'WIEK': ''}
    dictDlg=gui.DlgFromDict(
        dictionary=info, title='Go/No Go Test')
    if not dictDlg.OK:
        abort_with_error('Brak wprowadzenia danych.')
        # jak nie bedzie danych to powinno wywalic teraz
    return info


def main():
    global PART_ID, sex, age    # zmienne globalne
    info = dialog_pulp()
    conf=yaml.safe_load(open('config.yaml', encoding='utf-8'))
    win = visual.Window(conf['SCREEN_RES'], fullscr=True, monitor='testMonitor', units='pix', screen=0, color=conf['BACKGROUND_COLOR']) 
    # scr=0, to jak ktos ma 1 monitor to spoko 
    # jak ma wiecej to bedzie korzystac z pierwszego(glownego)
    event.Mouse(visible=False, newPos=None, win=win) 
    # okno jest w pelnym ekranie oraz nie widac myszki
    PART_ID=info['IDENTYFIKATOR']
    sex = info[u'P\u0141E\u0106']
    age = info['WIEK']
    logging.LogFile("".join(['results/', PART_ID, '_', sex, '_', age + '.log']), level=logging.INFO)  
    # zbierze info
    logging.info('FRAME RATE: {}'.format(conf['FRAME_RATE'])) 
    """zbierze info o klatkach i rozdzielczosci, ale nw czy to nie przysporzy 
        nam jakiegos bledu, najwyzej ustawimy w configu odgornie i bedzie 
        procedura dopasowana do konkretnego komputera z mozliwoscia zmienienia 
        w configu"""
    logging.info('SCREEN RES: {}'.format(conf['SCREEN_RES']))
    # ten fragment zbiera inf z okna dialogowego do wynikow

#poczatek procedury
    show_info(win, join('.', 'messages', 'hello.txt')) 
    # pierwsza wiadomosc, czyli instrukcja
    trial_no = 0
    trial_no += 1 #liczenie numerow triali
    
    part_of_experiment(win, conf, 'training')    # wywolywanie treningu
    show_info(win, join('.', 'messages', 'before_experiment.txt')) 
    # wiadomosc przed czescia eksperymentalna
    part_of_experiment(win, conf, 'experiment') 
    # wywolywanie czesci eksperymentalnej

    # zapisuje tylko raz wyniki
    logging.flush()
    show_info(win, join('.', 'messages', 'end.txt')) # podziekowania
    win.close() # koniec procedury

def trial(win, stim, conf):
    fix_cross = visual.TextStim(win, text='+', height=70, color=conf['FIX_CROSS_COLOR'])
    for _ in range(conf['FIX_CROSS_TIME']):
        fix_cross.draw()
        win.flip()
        
    win.callOnFlip(clock.reset)     # zresetuje nam zegar w razie czego
    event.clearEvents()
    reaction_time = "NA"
    
    for frameN in range(conf['STIM_DURATION_IN_FRAMES']):
        stim.draw()
        win.flip()  # wyswietlanie bodzca
        response = event.getKeys()
        if response == conf['REACTION_KEY_RIGHT']:
            """znowu zegar, jak bedzie odp to powinno go zapisac, 
                zresetuje na kolejnej fiksacji, a jak nie bedzie odp., 
                to bedzie NA"""
            reaction_time = clock.getTime()
            break
    
    return reaction_time, response  
    #zbieranie czasu reakcji, jesli bedzie nacisnieta strzalka w prawo


def if_correct(response, go_no_go, conf): 
    """zbieranie inf o poprawosci reakcji, rozpisalem warunki i mam nadzieje 
        ze dziala, bo takie mi bledy robilo, ze szok"""
    if go_no_go == "go" and response == conf['REACTION_KEY_RIGHT']:
        return True
    elif go_no_go == "go" and response != conf['REACTION_KEY_RIGHT']:
        return False
    elif go_no_go == "nogo" and response == conf['REACTION_KEY_RIGHT']:
        return False
    elif go_no_go == "nogo" and response != conf['REACTION_KEY_RIGHT']:
        return True
        

def part_of_experiment(win, conf, experiment):
    stim_kolko_go = visual.Circle(win, radius=50, lineWidth=15, lineColor="blue", fillColor="lightgray", pos=(0,0))
    stim_kwadrat_nogo = visual.rect.Rect(win, width=100, height=100, lineWidth=15, lineColor="blue", fillColor="lightgray", pos=(0,0))
    # tworzymy figury jako bodzce w trialu
    
    allstimlist = []    # lista ze wszystkimi bodzcami do wyswietlenia
    
    
    if experiment == "training":
        allstimlist.extend(["go"] * conf['NO_GO_TRIALS_TRAINING'])
        allstimlist.extend(["nogo"] * conf['NO_NO_GO_TRIALS_TRAINING'])
        # beda losowe
        go_no_go = "NA"
        for trial_no in range(len(allstimlist)):
            previous_go = deepcopy(go_no_go)
            # komentarz przy imporcie jest dlaczego tego uzylem 
            # gdybyscie nie wiedzialy, skad to sie wzielo
            go_no_go = random.choice(allstimlist)   # losowaanie figury
            if previous_go == "NA":
                stim_type = stim_kolko_go  
                """pierwszy bodziec to bodziec go - kolko, zeby sobie badany
                    w treningu w najgorszej sytuacji przynajmniej raz 
                    strzalke nacisnal"""
                go_no_go = "go"
            elif go_no_go == "go":
                stim_type = stim_kolko_go
            elif go_no_go == "nogo":
                stim_type = stim_kwadrat_nogo
                # przypisalem stimy do "go" i "nogo"
                
            reaction_time, response = trial(win, stim_type,  conf)
            correctness = if_correct(response, go_no_go, conf)
            
            RESULTS.append([PART_ID, trial_no, reaction_time, correctness, experiment, sex, age, stim_type])
            # zbiera info po terningu
        
        
    elif experiment == "experiment":
        allstimlist.extend(["go"] * conf['NO_GO_TRIALS_BLOCK_EXPERIMENT'])
        allstimlist.extend(["nogo"] * conf['NO_NO_GO_TRIALS_BLOCK_EXPERIMENT'])
        
        for block_no in range(conf['NO_BLOCKS_IN_EXPERIMENT']):
            go_no_go = "NA"
            for trial_no in range(len(allstimlist)):
                check_exit()
                previous_go = deepcopy(go_no_go)
                go_no_go = random.choice(allstimlist)    # losowanie figury
                if previous_go == "NA":
                    stim_type = stim_kolko_go   # pierwszy bodziec Go kolko
                    go_no_go = "go"
                elif go_no_go == "go":
                    stim_type = stim_kolko_go
                elif go_no_go == "nogo":
                    stim_type = stim_kwadrat_nogo  
                    
                reaction_time, response = trial(win, stim_type, conf)
                correctness = if_correct(response, go_no_go, conf)
                
                RESULTS.append([PART_ID, trial_no, reaction_time, correctness, experiment, sex, age, stim_type])
                # znowu zbiera
                
            show_image(win, join('.', 'images', 'break.jpg'), size=conf['SCREEN_RES'])


if __name__ == '__main__':     # wywolanie procedury
    PART_ID=''
    main()

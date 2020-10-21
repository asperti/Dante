import numpy as np
import re
import pickle

#loading dante's dictionary
f = open("dantes_dictionary.pkl", "rb")
fulldict = pickle.load(f)
f.close()

#parameters
verbose = 1 # 0: no messages
            # 1: warnings on anomalous verses
            # 2: verses with multiple syllabifications
            # alla messages stop the computation.
            # Type return to go on, or comment input() in the code

save_syllabification = True   #warning: could overwrite syllabification files. Chek file names

###########
def preprocess(x):
    to_separate = '•:?!<>.;,-—«»“”()'
    for c in to_separate:
        x = x.replace(c,' '+c + ' ')
    x = re.sub(r"(?<! )’(?! )", "’ ", x) #split ’ not preceded by space
    x = x.split()
    return x

# for metric purposes we do not count accents on "blend" monosyllabs like articles and prenoms
# "su" (on,over) can also be used as an adverb: ché i Pesci guizzan su per l’orizzonta, Inferno • Canto XI, 113
# "fra" can also be an abbreviation of "frate": «Or dì a fra Dolcin dunque che s’armi,  Inferno • Canto XXVIII, 55

excluded = ['a','ab','ad','ai','al','a’','ce','ci','coi','col',\
 'com’','con','co’','cu’','c’','d','da','dal','da’','de','del','de’','di',\
 'd’','e','ed','fra','gliel','han','ha’','ho','il','in','l','la','le','li',\
 'lo','l’','ma','mi','m’','nei','nel','ne’','ni','nol','n’',\
 'o','od','que','que’','sub','sul','suo’','su’','s’','ti',\
 'tra','tra’','tuo’','t’','ver’','ve’','vi','vo’','v’']

#At a given position of the verse, the syllabification algorythm is in a state
#composed of the following fields
# - syllabs: the syllabification so far
# - prob: the likelihood of such syllabification
# - tot: the current number of syllables
# - pr: the propensity to participate to a synalephe on the right
# - metric_checks: a tuple of boolean metric constraints (expected stress positions)

# update the boolean metric constraints wrt the last accent acc
def check_update(state,acc):
    #state : current state
    #acc : position of the accent, expressed as a negative integer offset from the right
    syllabs,prob,tot,pr,metric_checks = state
    check4,check6,check10 = metric_checks
    if not check4:
        if tot + acc == 4:
            check4 = True
    if not check6:
        if tot + acc == 6:
            check6 = True
    if not check10:
        if tot + acc == 10:
            check10 = True
    return (syllabs,prob,tot,pr,(check4, check6, check10))

# synalephe_alternatives takes in input the left and right propensities of
# two adjacent words, and returns the synalephe alternatives
# (-1," ") (no synalephe)
# (0," |)  (synalephe)
# with the respective probabilities.
def synalephe_alternatives(pr,pl):
    if pr==2 or pl==2 or (pr==1 and pl==1): #synalephe
        return [(1,-1," ")]
    elif pr==0 or pl==0: #no synalephe
        return [(1,0," |")]
    else:
        assert (pr*pl>0 and pr*pl<1)
        return [(pr*pl,-1," "),(1-pr*pl,0," |")]

#extend_single takes in input a state, the metric token for a new word to be concatenated
#and returns a nondeterministic list of possible new states
def extend_single(state,token):
    syllabs, state_prob, tot, vpr,checks = state
    (check4,check6,check10) = checks
    (pl,n,acc,pr), w, token_prob = token
    if check10 and not(n==0) and tot+n-max(vpr,pl)>11:
        #print("cannot accept more tokens",id)
        #set check10 to False
        return [(syllabs+w,0,tot,vpr,(check4,check6,False))]
    if n == 0: #punctuation! do nothing
        return [(syllabs+w,state_prob,tot,vpr,checks)]
    tot = tot + n
    new_states = []
    admissible_accent = not w.lower() in excluded or w in ["O"]
    #if (n==1 and not admissible_accent and not w.lower() in excluded):
    #    excluded.append(w.lower())
    for alt in synalephe_alternatives(vpr,pl):
        syn_prob, adjust, join = alt
        #the likelihood of each new state is the product between the likelihood state_prob of
        #the current state, the probability token_prob of the token (we could have multiple
        # syllabifications), and the probability syn_prob of the synalephe alternative
        #the total number of syllables is adjusted according to the possible synalephe,
        #and the new work is concatenated, joining with either " " or " |".
        new_state_prob = state_prob*token_prob*syn_prob
        new_tot = tot+adjust
        new_syllabs = syllabs+join+w
        new_state = (new_syllabs,new_state_prob,new_tot,pr,checks)
        if admissible_accent:
            new_state = check_update(new_state,acc)
        new_states.append(new_state)
    return(new_states)

def extend_multiple(states,tokens): #multiple states, multiple tokens
    new_states = []
    for state in states:
        for token in tokens:
            for s in extend_single(state,token):
                new_states.append(s)
    return new_states

def check10(state):
    _,_,_,_,(b4,b6,b10) = state
    return b10

#split a list of states into admissible states and anomalous state, where the
#state is considered to be admissible if it contains an accent on either the
#4th or the 6th syllable
def split(states):
    admissible = []
    anomalous = []
    for s in states:
        _, _, _, _, (b4, b6, b10) = s
        if b4 or b6:
            admissible.append(s)
        else:
            anomalous.append(s)
    return(admissible,anomalous)

def capital(b,s):
    if b: s = s.capitalize()
    return s

#get the list of metric_tuples from the dictionary
def get_info(w):
    if w == "I":
        #only word in vucabolary appearing both in capital and lower form
        #due to the verse "Né O sì tosto mai né I si scrisse,  Inferno • Canto XXIV, 100
        #O is less problematic
        info = fulldict[w]
    else:
        info = fulldict[w.lower()]
    return info

def check_verse(verse,token_list,loc, verbose=verbose):
    #initial state
    states = [("",1,0,0,(False,False,False))] # (syllabs,prob,len,pr,cheks)
    for tokens in token_list:
        #print(states,tokens)
        states = extend_multiple(states,tokens)
    states = [s for s in states if check10(s)]
    if not(bool(states)):
        print("Syllabification failed for \n {}    {}".format(verse[0:-1],loc))
        input()
        return (bool(states),"...")
    admissible,anomalous = split(states)
    if admissible:
        use_me = admissible
    else:
        use_me = anomalous
    assert (use_me)
    use_me.sort(reverse=True, key=lambda x: x[1])
    if verbose > 1:
        if len(use_me)>1:
            print("multiple choices at {}".format(loc))
            for s in use_me:
                print(s)
            input()
    if not(admissible) and verbose > 0:
        print("Warning - anomalous verse \n {} {}".format(verse[0:-1],loc))
        input()
    best = use_me[0]
    return (True,best[0])

#process a verse already splitted into a sequence of tokens x
def process_tokenized_verse(verse,x,loc=None,verbose=verbose):
    xtokens = []
    for w in x:
        upper = w[0].isupper() #remember if the word was capitalized in the source
        tokens = get_info(w)
        ctokens = [((pl, n, a, pr),capital(upper, ws), prob) for ((pl, n, a, pr), ws, prob) in tokens]
        xtokens.append(ctokens)
    return(check_verse(verse, xtokens, loc,verbose=verbose))

def process_verse(v,loc=None,verbose=verbose):
    x = preprocess(v)
    return(process_tokenized_verse(v,x,loc,verbose=verbose))

#call process_verse if you watno to process a specific verse
#examples:
#print(process_verse("esta selva selvaggia e aspra e forte",verbose=2)[1])
#print(process_verse("E io a lui: «Poeta, io ti richeggio",verbose=2)[1])
#print(process_verse("da indi in giuso è tutto ferro eletto", verbose=2)[1])
#print(process_verse("Monaldi e Filippeschi, uom sanza cura:", verbose=2)[1])

def full_check(files):
    all = 0
    wrong = 0
    warnings = 0
    for fname in files:
      filename=fname+".txt"
      #outfile=fname+"syll.txt"
      print("Processing file {}".format(fname))
      f = open(filename, "r")
      #fout = open(outfile, "w")
      outlist = []
      cantica = fname
      canto = 0
      verso = 0
      for v in f:
        x = preprocess(v)
        xs = []
        xtokens = []
        if len(x)>1 and x[1] == "•":
            outlist.append(x)
            canto += 1
            verso = 0
        elif x == []:
            outlist.append(x)
        else:
            verso += 1
            all += 1
            loc = cantica,canto,verso
            b,verse = process_tokenized_verse(v,x,loc)
            if not(b):
                wrong += 1
            outlist.append((loc[2],verse))

      if save_syllabification:
        outfile=fname+"_syllnew.txt"
        fout = open(outfile, "w")

        for line in outlist:
          #print(line)
          if line == []:
              s = "\n"
          elif len(line)>1 and line[1] == "•":
              s = ' '.join(line)+"\n"
          else:
              loc,verse = line
              #print (loc,verse)
              verse = verse.replace("_","")
              s = "{:3d}{:60s}\n".format(loc,verse)
          #print(s)
          fout.write(s)

    print("checking over")
    print("all = {}".format(all))
    print("wrong = {}".format(wrong))

    #print(excluded)

full_check(["inferno","purgatorio","paradiso"])
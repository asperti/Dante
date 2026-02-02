---
paper: https://arxiv.org/abs/2010.13515
repository: https://github.com/asperti/Dante/
---

# Dante
**Syllabification of the Divine Comedy**

This project contains a full syllabification of the Divine Comedy of Dante Alighieri, exploiting techniques from probabilistic and constraint programming. 
We particularly focus on the synalephe, addressed in terms of the "propensity" of a word to take part in a synalephe with adjacent words. 
We jointly provide an online vocabulary containing, for each word, information about its syllabification, the location of the tonic accent, 
and the aforementioned synalephe propensity, on the left and right sides.
The algorithm is intrinsically nondeterministic, producing different possible syllabifications for each verse, with different likelihoods; metric constraints
relative to accents on the 10th, 4th and 6th syllables are used to further reduce the solution space. 
The most likely syllabification is hence returned as output. 

**Warning:** the algorithm is meant to guess the most likely sillabification supposing the endecasyllabus **is correct**. 
If you want to use it as a reinforcement for generation you should take probabilities into account.

Files:

- dante.py  
  this is the main algorithm

- dantes_dictionary.pkl  
  this is vocabulary, saved as a pkl files, providing information about the syllabification of words. The syllabification is non deterministic, 
  so we may have multiple entries for each word. Each entry is a pair (t,ws) where t is a "metric tuple" and ws the corresponding syllabification.
  The metric tuples is a if the form (pl,n,a,pr) where n is the number of syllabs of the word, a is the position of the accent, expressed as negative 
  integer offset from the right, and pl, pr are the synalephe propensities at the left and right sides of the words.
  
- inferno.txt, purgatorio.txt, paradiso.txt 
These are the orginal sources, borrowed from the Gutenberg digital edition

- inferno_syllnew.txt, purgatorio_syllnew.txt, paradiso_syllnew.txt 
Fully syllabified versions, obtained as output of the algorithm.

# New

Since the commit on 7/8/2021 the dictionary provides the location of the accent at charater level. So the "metric tuple" is now a structure of the kind 
(pl,n,(a,ac),pr) where pl,n and pr have the same meaning as before. "a" is a negative offset identifying the accented syllable, and "ac" is a negative offset identifying the accented character inside the syllable. Both offsets are computed form the right. So, e.g. in the word "selva" the position of the accent is (-1,-1).
The charachter offset "ac" can be None in a few pathological cases like "ch'", "l'" and similar.



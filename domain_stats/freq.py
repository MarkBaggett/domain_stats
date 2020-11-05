#!/usr/bin/env python3
from __future__ import division

import sys
import string
import re
import weakref
import json

from collections import Counter, defaultdict
from pprint import pprint

class node():
    """
    A class to represent a node.

    Note: Assigning a weight actually adds that value.  It doesn't set
    it to that value. For example node['c'] = 5    increases the value
    in node by 5

    Attributes
    ----------

    parent : node
        the parent to this node
    count : int
        the current count for the node
"""

    def __init__(self,parent):
        self.parent = parent
        self._pairs = Counter()
        self._cachecount = 0
        self._dirtycount = False

    def __getitem__(self,key):
        if self.parent.ignore_case and (key.islower() or key.isupper()):
            return  self._pairs[key.lower()] + self._pairs[key.upper()]
        else:
            return self._pairs[key]

    def __setitem__(self,key,value):

        # TODO: should consider using the __addr__ magic method instead
        # since the described behavior is this instead
        self._dirtycount = True
        self._pairs[key] += value

    @property
    def count(self):
        if self._dirtycount:
           self._cachecount = sum(self._pairs.values())
           self._dirtycount = False
        return self._cachecount

class FreqCounter(dict):
    """
    A class used for frequency counting.

    Attributes
    ----------

    ignore_case : bool
        TODO: Update
    ignorechars : str
        TODO: Update
    verbose : bool
        When enabled, print verbose messages to the console.
    count : int
        The number of entries in the table

    
    Methods
    -------

    toJSON()
        Returns a JSON representation of the Table as a string
    fromJSON(jsondata)
        Imports the JSON representation into the Table
    tally_str(line, weight=1)
        TODO: Update
    probability(line)
        Returns the probability of a given letter combination
    save(filename)
        Writes the table to a frequency file
    load(filename)
        Loads the table from a given frequency file
    printtable()
        Prints the JSON table to the console
    """
    def __init__(self, *args,**kwargs):
        self._table = defaultdict(lambda :node(self))
        self.ignore_case = False

        # TODO: consider refactoring to ignore_chars for consistency
        self.ignorechars = ""
        self.verbose = "verbose" in kwargs

    def __getitem__(self,key):
        return self._table[key]

    def __iter__(self):
        return iter(self._table)

    def __len__(self):
        return len(self._table)

    def toJSON(self):
        """
        Returns a string JSON reperesentation of the table.
        """
        serial = []
        for key,val in self._table.items():
            serial.append( (key, list(val._pairs.items())) )
        return json.dumps((self.ignore_case, self.ignorechars, serial))

    def fromJSON(self,jsondata):
        """
        Imports the table from a string JSON representation of the table

        Parameters
        ----------
        jsondata : str
            A string that represents the JSON Data

        Returns
        -------
        str
            the JSON representation of the table
        """

        # TODO: Raise an error if we get something that we didn't 
        # expect.
        args = json.loads(jsondata)
        if args:
            self.ignore_case = args[0]
            self.ignorechars = args[1]
            for outerkey,val in args[2]:
                self._table[outerkey] = node(self)
                for letter,count in val:
                   self._table[outerkey][letter] = count

    def tally_str(self,line,weight=1):
        """
        TODO: Update
        
        Parameters
        ----------
        line : string
            TODO: Update
        weight : int, optional
            the weight to be assigned to the pair (default = 1)
        """
        allpairs = re.findall(r"..", line)
        allpairs.extend(re.findall(r"..",line[1:]))
        for eachpair in allpairs:
            self[eachpair[0]][eachpair[1]] = weight

    def probability(self,line):
        """
        Calculates the probability of the word pair

        Parameters
        ----------
        line : str
            TODO: Update

        Returns
        -------
        float
            TODO: verify; the probability of the given word pair
        """
        allpairs = re.findall(r"..", line)
        allpairs.extend(re.findall(r"..",line[1:]))
        if self.verbose: 
            print("All pairs: {0}".format(allpairs))
        probs = []
        for eachpair in allpairs:
            pair = [eachpair[0], eachpair[1]]

            # check if any part of the pair should be ignored and alert
            # the user this was skipped
            if not all(x in self.ignorechars for x in pair):
                probs.append(self._probability(eachpair))
                if self.verbose: 
                    print ("Probability of {0}: {1}".format(eachpair,probs))
            elif self.verbose:
                print("Pair '{}' was ignored",format(self.ignorechars))
        if probs:
            average_probability = sum(probs) / len(probs) * 100
        else:
            average_probability = 0.0
        if self.verbose:
            print("Average Probability: {0}% \n\n".format(average_probability))
        
        totl1 = 0
        totl2 = 0
        for eachpair in allpairs:
            l1 = l2 = 0
            pair = [eachpair[0], eachpair[1]]

            if not all(x in self.ignorechars for x in pair):
                l1 += self[eachpair[0]].count
                if self.ignore_case and (eachpair[0].islower() or eachpair[0].isupper()):
                    l1 += self[eachpair[0].swapcase()].count
                l2 += self[eachpair[0]][eachpair[1]]
                if self.ignore_case and (eachpair[0].islower() or eachpair[0].isupper()):
                    l2 += self[eachpair[0].swapcase()][eachpair[1]]
                totl1 += l1
                totl2 += l2
                if self.verbose: 
                    print("Letter1:{0} Letter2:{1}  - This pair {2}:{3} {4}:{5}".format(
                        totl1,
                        totl2, 
                        eachpair[0],
                        l1,
                        eachpair[1],
                        l2
                    ))
        if (totl1 == 0) or (totl2 == 0):
            total_word_probability = 0.0
        else:
            total_word_probability = totl2/totl1 * 100
        if self.verbose: print("Total Word Probability: {0}/{1} = {2}".format(totl2, totl1, total_word_probability))
        return round(average_probability,4),round(total_word_probability,4)

    def _probability(self,twoletters):
        if self.ignore_case and (self[twoletters[0]].count == 0 and self[twoletters[0].swapcase()].count == 0):
            return 0.0
        if not self.ignore_case and self[twoletters[0]].count == 0:
            return 0.0
        if self.ignore_case and (twoletters[0].islower() or twoletters[0].isupper()):
            ignored_tot = sum([self[twoletters[0].lower()][eachlet] for eachlet in self.ignorechars]) + sum([self[twoletters[0].upper()][eachlet] for eachlet in self.ignorechars])
            let2 = self[twoletters[0].lower()][twoletters[1]] + self[twoletters[0].upper()][twoletters[1]]
            let1 = self[twoletters[0].lower()].count + self[twoletters[0].upper()].count
            if let1 - ignored_tot == 0:
                return 0.0
            return let2/(let1-ignored_tot)
        else:
            ignored_tot = sum([self[twoletters[0]][eachlet] for eachlet in self.ignorechars])
            if self[twoletters[0]].count - ignored_tot == 0:
                return 0.0
            return self[twoletters[0]][twoletters[1]] / (self[twoletters[0]].count - ignored_tot)

    def save(self,filename):
        try:
            file_handle =  open(filename, 'wb')
            file_handle.write(self.toJSON().encode("latin1"))
            file_handle.flush()
            file_handle.close()
        except Exception as e:
            print("Unable to write freq file :" + str(e))
            raise(e)

    def load(self,filename):
        try:
            file_handle =  open(filename,"rb")
            self.fromJSON(file_handle.read().decode("latin1"))
            file_handle.close()
        except Exception as e:
            print("Unable to load freq file :",str(e))
            raise(e)

    @property
    def count(self):
        return sum(map(lambda y:y.count, x._table.values()))

    def printtable(self):
        pprint(self.toJSON())



if __name__ == "__main__":
    import argparse
    import os
    parser=argparse.ArgumentParser()
    parser.add_argument(
        '-m',
        '--measure',
        required=False,
        help='Measure likelihood of a given string',
        dest='measure'
    )
    parser.add_argument(
        '-n',
        '--normal',
        required=False,
        help='Update the table based on the following normal string',
        dest='normal'
    )
    parser.add_argument(
        '-f',
        '--normalfile',
        required=False,
        help='Update the table based on the contents of the normal file',
        dest='normalfile'
    )
    parser.add_argument(
        '-p',
        '--print',
        action='store_true',
        required=False,
        help='Print a table of the most likely letters in order',
        dest='printtable'
    )
    parser.add_argument(
        '-c',
        '--create',
        action='store_true',
        required=False,
        help='Create a new empty frequency table',dest='create'
    )
    parser.add_argument(
        '-v',
        '--verbose',
        action='store_true',
        required=False,
        help='show calculation process',
        dest='verbose'
    )

    parser.add_argument(
        '-b',
        '--bulk',
        default=None,
        required=False,
        help='Measure every line in a file.',
        dest='bulk'
    )

    # TODO: break these up as well
    parser.add_argument('-t','--toggle_case_sensitivity',action='store_true',required=False,help='Ignore case in all future frequecy tabulations',dest='toggle_case')
    parser.add_argument('-s','--case_sensitive',action='store_true',required=False,help='Consider case in calculations. Default ignores case.',dest='case_sensitive')
    parser.add_argument('-w','--weight',type=int,default = 1, required=False,help='Affects weight of promote, update and update file (default is 1)',dest='weight')
    parser.add_argument('-e','--exclude',default = "\n\t~`!@#$%^&*()_+-", required=False,help='Provide a list of characters to ignore from the tabulations.',dest='exclude')
    parser.add_argument('freqtable',help='File storing character frequencies.')

    args=parser.parse_args()

    if args.verbose:
        fc = FreqCounter(verbose=True)
    else:
        fc = FreqCounter()
    if args.create and os.path.exists(args.freqtable):
        print("Frequency table already exists. " + args.freqtable)
        sys.exit(1)

    if not args.create:
        if not os.path.exists(args.freqtable):
           print("Frequency Character file not found. - %s " % (args.freqtable))
           raise(Exception("File not found."))
        fc.load(args.freqtable)

    if args.printtable: 
        fc.printtable()
    if args.normal: 
        fc.tally_str(args.normal, args.weight)
    if args.toggle_case:
        print("This feature has been depricated. By default all calculations ignore case.  Use -s to consider case.")
    fc.ignore_case = not args.case_sensitive
    fc.ignorechars = args.exclude
    if args.verbose: 
        print("Ignoring Case: {0}".format(fc.ignore_case))
    if args.verbose: 
        print("Ignoring Characters: {0}".format(fc.ignorechars))
    if args.normalfile:
        with open(args.normalfile,"rb") as filehandle:
            for eachline in filehandle:
                fc.tally_str(eachline.decode("latin1"))
    if args.measure: 
        print(fc.probability(args.measure))
    if args.bulk:
        with open(args.bulk,"rt") as filehandle:
            for eachline in filehandle:
                print(fc.probability(eachline),"-",eachline)
                
    fc.save(args.freqtable)
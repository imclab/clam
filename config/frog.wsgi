#!/usr/bin/env python
#-*- coding:utf-8 -*-

###############################################################
# CLAM: Computational Linguistics Application Mediator
# -- WSGI script for launching CLAM (from within a webserver) --
#       by Maarten van Gompel (proycon)
#       http://ilk.uvt.nl/~mvgompel
#       Induction for Linguistic Knowledge Research Group
#       Universiteit van Tilburg
#
#       Licensed under GPLv3
#
###############################################################

import os
import sys


sys.path.append('/home/proycon/work')
os.environ['PYTHONPATH'] = '/home/proycon/work' #sys.path[0] + '/../..'

import clam.config.frog
import clam.clamservice
clam.clamservice.run_wsgi(clam.config.frog)


#!/usr/bin/python
# -*- coding: UTF-8 -*-
from math import sqrt
from sys import argv, exit, stdin, stderr
from subprocess import Popen, PIPE
from os import environ
import cPickle
import time
import psyco

debug = False

if debug:
    inicio = time.time()

ruta = environ["HOME"] + "/.primos.pickle"

try:
    archivo = open(ruta, "r")
    criba = cPickle.load(archivo)
    archivo.close()

except EOFError:
    criba = None 
    archivo.close()

except IOError:
    criba = None

if debug:
    stderr.write(("%9.5f" % (time.time() - inicio) + " pickle abierto\n"))

def cribar(hasta, criba=None):
    if debug:
        stderr.write(("%9.5f" % (time.time() - inicio) + "   Iniciada\n"))

    criba = criba or [False, False, True, True, False, True, False, True]

    if hasta < len(criba):
        return criba[:hasta + 1]

    if debug:
        stderr.write(("%9.5f" % (time.time() - inicio) + "   Extendiendo\n"))

    desde = len(criba) + 1
    criba.extend([True] * (hasta - desde + 2))
    #print len(criba), criba[hasta]

    if debug:
        stderr.write(("%9.5f" % (time.time() - inicio) + "   Criba extendida\n"))

    for primo in [N for N in xrange(int(sqrt(hasta + 1)) + 1) if criba[N]]:
        for multiplo in xrange(max(desde / primo, 2), hasta / primo + 1):
            #[N for N in xrange(desde / primo, hasta / primo + 1) if criba[N]]
            #print primo, multiplo, primo * multiplo

                criba[primo * multiplo] = False

                #FIXME: cribar_awk va mucho mas rapido pero no aprovecha el calculo previo
                #criba = cribar_awk(hasta)

        if debug:
            stderr.write(("%9.5f" % (time.time() - inicio) + "   Criba renormalizada\n"))

        archivo = open(ruta, "w")
        cPickle.dump(criba, archivo, -1)
        archivo.close()

        if debug:
            stderr.write(("%9.5f" % (time.time() - inicio) + "   Criba guardada\n"))

    print time.time() - inicio

    return criba

def cribar_awk(hasta):
    subproceso = Popen("primos.awk " + `hasta`,\
    shell=True, stdout=PIPE, stderr=PIPE)
    exec("criba = " + subproceso.stdout.readlines()[0])
    return criba

def porcion(lista, minimo, maximo):
    return [elemento for elemento in lista if minimo <= elemento <= maximo]
    #FIXME: Aqui deberia hacerse una busqueda binaria

# # # MAIN # # #
if __name__ == "__main__":

    if debug:
        stderr.write(("%9.5f" % (time.time() - inicio) + " main\n"))

    if len(argv) > 2:
        print """Decidase por un numero, por favor."""
        exit(2)
    else:
        if len(argv) == 2:
            try:
                hasta = int(argv[1])
            except ValueError:
                print """Estamos hablando de numeros primos. NUMEROS!!"""
                exit(3)
        else:
            print """No se especifico ningun limite,\
            se buscaran los primos hasta 1000."""
            hasta = 1000

    if debug:
        stderr.write(("%9.5f" % (time.time() - inicio) + " > cribar(n)\n"))

    criba = cribar(hasta, criba)

    if debug:
        stderr.write(("%9.5f" % (time.time() - inicio) + " < cribar(n)\n"))

    total = 0

    for primo in [N for N in xrange(len(criba)) if criba[N]]:
#        print primo
        total += primo

    print total

    if debug:
        stderr.write(("%9.5f" % (time.time() - inicio) + " Primos mostrados\n"))

else:
    print "Modulo de criba:", dir()

if debug:
    stderr.write(("%9.5f" % (time.time() - inicio) + " FIN\n"))

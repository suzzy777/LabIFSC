#!/usr/bin/env python
# -*- coding: utf-8 -*-

from copy import copy
from math import floor, log, ceil
from .geral import acha_unidade, calcula_dimensao, analisa_numero, dimensao_em_texto, fator_de_conversao_para_si, unidades_em_texto, converte_unidades, analisa_unidades, simplifica_unidades

class Medida:
    unidades_originais = [] # Tuplas (objeto unidade, expoente) na ordem em que foram entradas  
    dimensao = (0, 0, 0, 0, 0, 0, 0)
    nominal = 0.0
    incerteza = 0.0
    si_nominal = 0.0
    si_incerteza = 0.0

    def __init__(self, valor, unidade_txt=None):
        # Analise o valor
        if isinstance(valor, Medida):
            self.nominal = valor.nominal
            self.incerteza = valor.incerteza
        elif isinstance(valor, str):
            self.nominal, self.incerteza = analisa_numero(valor)
        elif isinstance(valor, tuple) and len(valor) == 2:
            self.nominal, self.incerteza = float(valor[0]), abs(float(valor[1]))
        else:
            try:
                self.nominal = float(valor)
            except:
                raise Exception("não foi possível extrair o valor e a incerteza")

        # Veja as unidades
        self.unidades_originais = []
        if isinstance(unidade_txt, list):
            self.unidades_originais = copy(unidade_txt)
        elif unidade_txt != None:
            self.unidades_originais = analisa_unidades(unidade_txt)
        self.dimensao = calcula_dimensao(self.unidades_originais)

        # Converta para o SI
        mul_nom, mul_err, add_nom, add_err = fator_de_conversao_para_si(self.unidades_originais)
        self.si_nominal = self.nominal * mul_nom + add_nom
        self.si_incerteza = (self.nominal * mul_err + mul_nom * self.incerteza)  + add_err

    def _checa_dim(self, outro):
        if self.dimensao != outro.dimensao:
            raise ValueError("dimensões físicas incomaptíveis: {} vs {}".format(dimensao_em_texto(self.dimensao), dimensao_em_texto(outro.dimensao)))
    def _eh_medida(self, outro):
        if not isinstance(outro, Medida):
            raise TypeError("medidas só podem ser comparadas com outras medidas")
    def _torne_medida(self, outro, converter):
        m = outro
        if not isinstance(outro, Medida):
            m = Medida(outro)
        if converter:
            return m.converta(self.unidades_originais)
        else:
            return m

    def converta(self, unidades):
        nom, err = converte_unidades(self.nominal, self.incerteza, self.unidades_originais, unidades)
        return Medida((nom, err), unidades)

    def __str__(self):
        return "{}±{} {}".format(self.nominal, self.incerteza, unidades_em_texto(self.unidades_originais))

    def __repr__(self):
        return "<{}±{} {} = {}±{} {}>".format(self.nominal, self.incerteza, unidades_em_texto(self.unidades_originais), self.si_nominal, self.si_incerteza, dimensao_em_texto(self.dimensao))

    def __eq__(self, outro):
        self._eh_medida(outro)
        self._checa_dim(outro)
        return abs(self.si_nominal - outro.si_nominal) <= 2 * (self.si_incerteza + outro.si_incerteza)
    def __ne__(self, outro):
        self._eh_medida(outro)
        self._checa_dim(outro)
        return abs(self.si_nominal - outro.si_nominal) > 3 * (self.si_incerteza + outro.si_incerteza)
    def __add__(self, outro):
        outro = self._torne_medida(outro, False)
        self._checa_dim(outro)
        outro = self._torne_medida(outro, True)
        return Medida((self.nominal+outro.nominal, self.incerteza+outro.incerteza), self.unidades_originais)
    def __sub__(self, outro):
        outro = self._torne_medida(outro, False)
        self._checa_dim(outro)
        outro = self._torne_medida(outro, True)
        return Medida((self.nominal-outro.nominal, self.incerteza+outro.incerteza), self.unidades_originais)
    def __mul__(self, outro):
        outro = self._torne_medida(outro, False)
        nom = self.nominal * outro.nominal
        err = self.nominal * outro.incerteza + self.incerteza * outro.nominal
        m = Medida((nom, err), simplifica_unidades(self.unidades_originais, outro.unidades_originais))
        return m
    def __div__(self, outro):
        outro = self._torne_medida(outro, False)
        nom = self.nominal / outro.nominal
        err = ((self.nominal * outro.incerteza) + self.incerteza * outro.nominal)/outro.nominal**2
        m = Medida((nom, err), simplifica_unidades(self.unidades_originais, outro.unidades_originais, inverte=True))
        return m
    def __floordiv__(self, outro):
        m = self.__div__(outro)
        nom = floor(m.nominal)
        err = abs(m.nominal-nom) + m.incerteza
        return Medida((nom, err), m.unidades_originais)
    def __truediv__(self, outro):
        return self.__div__(outro)
    def __mod__(self, outro):
        pass
    def __divmod__(self, outro):
        outro = self._torne_medida(outro, False)
        a = self.__floordiv__(1)
        b = outro.__floordiv__(1)
        unidades = simplifica_unidades(self.unidades_originais, outro.unidades_originais, inverte=True)

        q_nom, r_nom = divmod(int(a.nominal), int(b.nominal))
        err = ((self.nominal * outro.incerteza) + self.incerteza * outro.nominal)/outro.nominal**2
        err *= 1/outro.nominal
        return Medida((q_nom, err), unidades), Medida((r_nom, err), unidades)
    def __pow__(self, outro):
        if isinstance(outro, Medida):
            raise NotImplementedError("a exponenciação entre medidas não está implementada")
        else:
            return Medida((self.nominal**outro, outro*self.nominal**(outro-1)*self.incerteza), self.unidades_originais)
    def __abs__(self):
        m = Medida((abs(self.nominal), self.incerteza), self.unidades_originais)
        return m
    def __int__(self):
        return int(self.nominal)
    def __float__(self):
        return float(self.nominal)
    def __complex__(self):
        return complex(self.nominal)
    def __radd__(self, outro):
        return Medida(outro).__add__(self)
    def __rsub__(self, outro):
        return Medida(outro).__sub__(self)
    def __rmul__(self, outro):
        return Medida(outro).__mul__(self)
    def __rfloordiv__(self, outro):
        return Medida(outro).__floordiv__(self)
    def __rmod__(self, outro):
        return Medida(outro).__mod__(self)
    def __rdivmod__(self, outro):
        return Medida(outro).__divmod__(self)
    def __rpow__(self, outro):
        outro = float(outro)
        return Medida((
            outro**self.nominal,
            outro**self.nominal * log(outro) * self.incerteza))
    def __rdiv__(self, outro):
        return Medida(outro).__div__(self)

    def __format__(self, fmt):
        fmt = fmt.split(",")
        modo = fmt[0]
        rouding = "ifsc"
        if len(fmt) >= 2:
            rouding = fmt[1]
        nom = ""
        sep = ""
        err = ""
        uni = ""
        base = "{}{}{} {}"

        if modo == "repr":
            return self.__repr__()

        if rouding == "ifsc" or rouding == "-":
            exp = 0
            nom = self.nominal
            err = self.incerteza
            # Arredonde o erro para a maior casa significativa
            while err < 1.0:
                exp -= 1
                err *= 10
            while err >= 10.0:
                exp += 1
                err /= 10
            err = round(err)*10**exp
            # Arredonde o valor nominal de acrodo
            if exp <= 0:
                nom = round(nom, -exp)
            else:
                nom = nom
            # Converta para string tomando cuidado com zeros desnecessários
            if nom == int(nom):
                nom = str(int(nom))
            else:
                nom = str(nom)
            if err == int(err):
                err = str(int(err))
            else:
                err = str(err)
        elif rouding == "full":
            nom = str(self.nominal)
            err = str(self.incerteza)
        else:
            raise ValueError("{} não é um parâmetro válido de arredondamento".format(rouding))
        sep = "±"
        uni = unidades_em_texto(self.unidades_originais)
        if modo == "latex":
            sep = "\\pm"
            uni = unidades_em_texto(self.unidades_originais, estilo="latex")
            base = "{}{}{}\\textrm{{ {}}}"
        elif modo == "latex-si":
            sep = "+-"
            uni = unidades_em_texto(self.unidades_originais, estilo="latex")
            base = "\\SI{{{}{}{}}}{{{}}}"
        elif modo == "ascii":
            sep = "+/-"
            uni = unidades_em_texto(self.unidades_originais, estilo="latex")
            print(modo, sep, uni, nom, err, rouding)

        return base.format(nom, sep, err, uni)
        
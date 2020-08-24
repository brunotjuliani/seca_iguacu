#BIBLIOTECAS
import pandas as pd
import numpy as np
import os
import datetime as dt
import matplotlib.pyplot as plt
import scipy.stats as stats
gbl = globals()


#DIRETORIO
dir_secas = "/home/bruno/Documentos/Seca_Iguacu"
os.chdir(dir_secas)


#IMPORTA SERIE
uniao_vitoria = pd.read_csv('vazoes_uva.csv', sep = ';', decimal=',')
uniao_vitoria.columns = ['Data', 'vazao_original', 'vazao']
uniao_vitoria['Data'] = pd.to_datetime(uniao_vitoria['Data'], format = '%Y-%m-%d')
uniao_vitoria['Data2'] = pd.to_datetime(uniao_vitoria['Data'], format = "%Y-%m-%d").dt.strftime("%m-%d")
uniao_vitoria["Ano"] = pd.DatetimeIndex(uniao_vitoria['Data']).year
uniao_vitoria["Mes"] = pd.DatetimeIndex(uniao_vitoria['Data']).month
uniao_vitoria["Dia"] = pd.DatetimeIndex(uniao_vitoria['Data']).day
print(uniao_vitoria)


#CALCULO MINIMOS
minimos_anuais = pd.DataFrame()
for ano in range(1930,2021):
    serie_ano = uniao_vitoria.loc[(uniao_vitoria["Ano"] == ano)].reset_index(drop=True)
    serie_ano['Vazao_7'] = serie_ano.iloc[:,2].rolling(window=7).mean()
    serie_ano['Vazao_10'] = serie_ano.iloc[:,2].rolling(window=10).mean()
    serie_ano['Vazao_30'] = serie_ano.iloc[:,2].rolling(window=30).mean()
    serie_ano['Vazao_90'] = serie_ano.iloc[:,2].rolling(window=90).mean()
    linha_ano = pd.DataFrame()
    linha_ano.loc[0,"Ano"] = ano
    linha_ano.loc[0,"Min_1"] = np.nanmin(serie_ano['vazao'])
    linha_ano.loc[0,"Min_7"] = np.nanmin(serie_ano['Vazao_7'])
    linha_ano.loc[0,"Min_10"] = np.nanmin(serie_ano['Vazao_10'])
    linha_ano.loc[0,"Min_30"] = np.nanmin(serie_ano['Vazao_30'])
    linha_ano.loc[0,"Min_90"] = np.nanmin(serie_ano['Vazao_90'])
    minimos_anuais = pd.concat([minimos_anuais, linha_ano]).reset_index(drop=True)
minimos_anuais.to_csv("Minimos_Uniao_Vitoria.csv")


#PRINTA MINIMOS
print(np.nanmin(minimos_anuais['Min_1']))
print(np.nanmin(minimos_anuais['Min_7']))
print(np.nanmin(minimos_anuais['Min_10']))
print(np.nanmin(minimos_anuais['Min_30']))
print(np.nanmin(minimos_anuais['Min_90']))


#PLOTA MINIMOS
plt.figure()
plt.plot(minimos_anuais["Ano"],minimos_anuais["Min_1"], label = "Min_1")
plt.plot(minimos_anuais["Ano"],minimos_anuais["Min_7"], label = "Min_7")
plt.plot(minimos_anuais["Ano"],minimos_anuais["Min_10"], label = "Min_10")
plt.plot(minimos_anuais["Ano"],minimos_anuais["Min_30"], label = "Min_30")
plt.plot(minimos_anuais["Ano"],minimos_anuais["Min_90"], label = "Min_90")
plt.legend(loc='best')
plt.xlabel('Ano')
plt.ylabel('Vazao Media (m3s-1)')
plt.savefig("Minimas_Anuais.png", dpi = 300)
plt.close()

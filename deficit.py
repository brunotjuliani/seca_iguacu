#BIBLIOTECAS
import pandas as pd
import numpy as np
import os
import datetime as dt
import matplotlib.pyplot as plt
import scipy.stats as stats

#INPUTS
dir_secas = "/home/bruno/Documentos/Seca_Iguacu"
os.chdir(dir_secas)
serie_original = pd.read_csv('Dados_Estacoes/Pontilhao_vazao_tratada.csv',
                              sep = ',', decimal='.', header = 0)
serie_original
nome_estacao = 'Pontilhao'
Percentil = 95
tc = 10 #tempo entre eventos distintos
dc = 5 #tempo minimo de evento

#FORMATA SERIE ORIGINAL
#serie_original.columns = ['data', 'q_m3s_corr']
serie_original.columns = ['data', 'q_m3s_orig', 'q_m3s_corr']
serie_original['data'] = pd.to_datetime(serie_original['data'], format = '%Y-%m-%d')
serie_original['mes-dia'] = pd.to_datetime(serie_original['data'],
                                           format = "%Y-%m-%d").dt.strftime("%m-%d")
serie_original["mes"] = pd.DatetimeIndex(serie_original['data']).month
serie_original["dia"] = pd.DatetimeIndex(serie_original['data']).day
#print(serie_original)


#SERIE THRESHOLDS
Q_Percentil = 'Q'+str(Percentil)
deficit_diario = 'deficit_diario_q'+str(Percentil)
deficit_total = 'deficit_total_q'+str(Percentil)
data_ini = dt.datetime(2019, 1, 1,  0,  0) #YYYY, M, D, H, Min
data_fim = dt.datetime(2019, 12, 31,  23,  59)
Thresholds = pd.DataFrame(pd.date_range(data_ini, data_fim), columns=['data'])
Thresholds['mes-dia'] = pd.to_datetime(Thresholds['data'],"%Y-%m-%d").dt.strftime("%m-%d")
Thresholds[Q_Percentil] = ''
for d in Thresholds.index:
    mes = Thresholds.iloc[d,0].month
    dia = Thresholds.iloc[d,0].day
    Serie_Threshold = pd.DataFrame()
    for indice in serie_original.loc[(serie_original["mes"] == mes) & (serie_original["dia"] == dia)].index:
        base_31dias = serie_original.iloc[indice-15:indice+16,:].dropna()
        Serie_Threshold = pd.concat([Serie_Threshold,base_31dias])
    Thresholds.loc[d,Q_Percentil] = np.percentile(Serie_Threshold['q_m3s_corr'], 100-Percentil)
print(Thresholds)

#EXPORTA THRESHOLD
Thresholds.to_csv(nome_estacao+'_thresholds_'+Q_Percentil+'.csv')

#CALCULO DEFICIT
serie_modificada = serie_original
serie_modificada.drop(serie_modificada[serie_modificada['mes-dia'] == '02-29'].index, inplace = True)
for i in serie_modificada.index:
    serie_modificada.loc[i,Q_Percentil] = Thresholds.loc[Thresholds['mes-dia'] == serie_modificada.loc[i,'mes-dia']].iloc[0,2]
serie_modificada[deficit_diario] = serie_modificada[Q_Percentil] - serie_modificada['q_m3s_corr']

eventos_deficit = pd.DataFrame(columns = ['data_inicio', 'data_final', 'duracao', deficit_total])
indiceLinhaEvento = 0
for indice in serie_modificada.index:
    if not indiceLinhaEvento in eventos_deficit.index:
        eventos_deficit.loc[indiceLinhaEvento] = ''
    if serie_modificada.loc[indice,deficit_diario] >= 0:
        #SE eventos_deficit[indiceLinhaEvento]['Data_Inicial'] é nulo então:
        if eventos_deficit.loc[indiceLinhaEvento,'data_inicio'] == '':
            #eventos_deficit[indiceLinhaEvento]['Data_Inicial'] = data-serie_modificada
            eventos_deficit.loc[indiceLinhaEvento,'data_inicio'] = serie_modificada.loc[indice,'data']
            #Para primeiro dia do evento deficit total recebe valor de di
            eventos_deficit.loc[indiceLinhaEvento, deficit_total] = serie_modificada.loc[indice,deficit_diario]
        #SENÃO
        else:
            #Para dias seguintes do evento deficit total soma valores seguintes de di
            eventos_deficit.loc[indiceLinhaEvento,deficit_total] = eventos_deficit.loc[indiceLinhaEvento,deficit_total] + serie_modificada.loc[indice,deficit_diario]

    #SENÃO
    else:
        #SE eventos_deficit[indiceLinhaEvento]['Data_Inicial'] NÃO é nulo E eventos_deficit[indiceLinhaEvento]['Data_Final'] É nulo então:
        if eventos_deficit.loc[indiceLinhaEvento,'data_inicio'] != '' and eventos_deficit.loc[indiceLinhaEvento, 'data_final'] == '':
            #eventos_deficit[indiceLinhaEvento]['Data_Final'] = data-serie_modificada
            eventos_deficit.loc[indiceLinhaEvento,'data_final'] = serie_modificada.loc[indice,'data']
            #insere duracao
            eventos_deficit.loc[indiceLinhaEvento,'duracao'] = (eventos_deficit.loc[indiceLinhaEvento, 'data_final'] - eventos_deficit.loc[indiceLinhaEvento, 'data_inicio']).days
            #indiceLinhaEvento = indiceLinhaEvento + 1
            indiceLinhaEvento = indiceLinhaEvento + 1
eventos_deficit.drop(eventos_deficit[eventos_deficit['data_inicio'] == ''].index, inplace = True)

indexEventoAgrupado = 0
eventos_agrupados = pd.DataFrame(columns = ['data_inicio', 'data_final',\
 'duracao', deficit_total])
for indice in eventos_deficit.index:
    if indice == 0:
        eventos_agrupados.loc[0] = eventos_deficit.loc[0]
    elif (eventos_deficit.loc[indice,'data_inicio'] - eventos_agrupados.loc[indexEventoAgrupado, 'data_final']).days < tc:
        eventos_agrupados.loc[indexEventoAgrupado, 'data_final'] = eventos_deficit.loc[indice, 'data_final']
        eventos_agrupados.loc[indexEventoAgrupado, 'duracao'] = eventos_agrupados.loc[indexEventoAgrupado, 'duracao'] + eventos_deficit.loc[indice, 'duracao']
        eventos_agrupados.loc[indexEventoAgrupado, deficit_total] = eventos_agrupados.loc[indexEventoAgrupado, deficit_total] + eventos_deficit.loc[indice, deficit_total]
    else:
        indexEventoAgrupado = indexEventoAgrupado + 1
        eventos_agrupados.loc[indexEventoAgrupado] = eventos_deficit.loc[indice]
eventos_agrupados.drop(eventos_agrupados[eventos_agrupados['duracao'] <= 5].index, inplace = True)
eventos_agrupados = eventos_agrupados.reset_index(drop=True)
print(eventos_agrupados)

#EXPORTA EVENTOS IDENTIFICADOS
eventos_agrupados.to_csv(nome_estacao+'_eventos_agrupados_'+Q_Percentil+'.csv')

#CALCULO CDF
CDF = pd.DataFrame()
CDF = eventos_agrupados
locexp, scaleexp = stats.distributions.expon.fit(CDF[deficit_total])
CDF['CDF_exponencial'] = stats.expon.cdf(CDF[deficit_total], loc = locexp, scale = scaleexp)
CDF = CDF.sort_values(['CDF_exponencial']).reset_index(drop=True)
print(CDF)

#PLOTA CDF
plt.plot(CDF[deficit_total], CDF['CDF_exponencial'])
plt.xlabel('Deficit')
plt.ylabel('CDF Exponencial')

#EXPORTA RESULTADOS

CDF.to_csv(nome_estacao+'_CDF_exponencial_'+Q_Percentil+'.csv')
plt.savefig(nome_estacao+'_CDF_Exponencial_'+Q_Percentil+'.png', dpi = 300)

import ee
import matplotlib.pylab as plt
import matplotlib.pyplot as pl
import numpy as np
import matplotlib.cm as cm
import time
import json
import datetime
import copy
import shutil
import pandas as pd
from scipy.stats.stats import pearsonr
from datetime import datetime, timedelta
from datetime import date
from sklearn.metrics import confusion_matrix

ee.Initialize()
start_time = time.time()

layer = qgis.utils.iface.activeLayer()
print("Nombre de layer", layer.name())
#features seleccionadas
selected_features = layer.selectedFeatures()
count= len(list(selected_features))
print("Feature number", count)
#Filtrar las fotos por fecha
sentinelCollection = ee.ImageCollection('COPERNICUS/S2');
sentinelDateCollection = ee.ImageCollection(sentinelCollection.filterDate('2017-06-21', '2017-09-23'))

i=0
val = [None] * count
valGNDVI = [None] * count
etiquetas = []
clases= []
datak = [None] * count
fechasRep = [None] * count
dife= [None] * count
datosBosque=[]
datosCesped=[]
hayBosque= False
hayCesped= False
featuresNull = []
featuresNotNull=[]

#analizar cada feature
while i< count:
    
    p = selected_features[i]
    #crear un vector con el nombre de cada feature. p[1] el el atributo de descripcion
    etiquetas.append(p[1])
#    if p[1]==NULL:
#        print 1
#        clases.append(str(p[3]))
        
    print("ETIQUETAS", etiquetas)
    g = p.geometry()
    gJSON=g.exportToGeoJSON()
    o=json.loads(gJSON)
    b = ee.Geometry.Polygon(o['coordinates'])
    #filtrar la coleccion de imagenes por la geometria de la feature que se esta analizando
    sentinelAOI = ee.ImageCollection(sentinelDateCollection.filterBounds(b))
    print("Imagenes filtradas por feature", sentinelAOI.size().getInfo())
    imagesConNubes = [item.get('id') for item in sentinelAOI.getInfo().get('features')]
    print("STOP 2", len(imagesConNubes))
    
    
    #crear dos arrays para separar las features sin nobre de las nombradas(mar, arena, bosque...)
    if p[1]==NULL:
        print("DENTRO NULL")
        featuresNull.append(p)
    else:
        featuresNotNull.append(p)
    values=[]
    valuesGNDVI=[]
    datas=[]
    diferencias=[]
    fechasR = []
    images=[]
    #crear coleccion de imagenes sin nubes
    for icn in imagesConNubes:
        icnindex= imagesConNubes.index(icn)
        cloudPercentage=ee.Image(imagesConNubes[icnindex]).get('CLOUDY_PIXEL_PERCENTAGE').getInfo()
        if cloudPercentage< 10.0:
            images.append(icn)
        else:
            print("IMAGEN CON MUCHAS NUBES")
    print("IMAGENES SIN NUBES", len(images))
    #analizar cada imagen de la coleccion
    for image in images:
        print 1
        #conseguir la fecha de recepcion de la imagen
        date1 = ee.Image(image).get('system:time_start')
        indexPhoto= images.index(image)
        dat= date.fromtimestamp(date1.getInfo() / 1e3)
        print("FECHA", dat)
        datas.append(dat)

            
        #properties = ee.Image(image).propertyNames();
        
        # calcular NDVI
        nir = ee.Image(image).reduceRegion(ee.Reducer.mean(), o).getInfo().get('B8')
        red = ee.Image(image).reduceRegion(ee.Reducer.mean(), o).getInfo().get('B4')
        
        #en caso de que nir o red sean nulos, darle el mismo valor que el contrario para formzar que
        #NDVI sea 0 e imputar los valores posteriormente
        
        if nir == None:
            print("NIR IS NONE")
            nir = red
        if red == None:
            print("RED IS NONE")
            red = nir
                    
        if nir == 0 and red == 0:
            ndvi= 0
        else:
            ndvi = ((nir - red)/(nir + red))
        
        values.append(ndvi)
        
        #GNDVI
        green = ee.Image(image).reduceRegion(ee.Reducer.mean(), o).getInfo().get('B3')
        if green == None:
            print("GREEN IS NONE")
            green = nir
                    
        if nir == 0 and green == 0:
            ndvi= 0
        else:
            gndvi = ((nir - green)/(nir + green))
        
        valuesGNDVI.append(gndvi)
        
        etiquetasR= []
        
        #Cuando hay dos fotos de la misma fecha
        
        if indexPhoto>0 :

            a= copy.copy(datas[indexPhoto])
            b= copy.copy(datas[indexPhoto-1])

            if a == b: #si hay dos fechas iguales
                print("FECHA REPETIDA", a)
                fechasR.append(a)
                etiquetasR.append(p[1])
                if p[1]=='bosque':
                    hayBosque= True
                    print("Bosque index i e index i-1", values[indexPhoto],values[indexPhoto-1])
                    datosBosque.append(max([values[indexPhoto],values[indexPhoto-1]]))
                    print("Maximo bosque", max([values[indexPhoto],values[indexPhoto-1]]))
                elif p[1]== 'cesped':
                    hayCesped= True
                    print("cesped index i e index i-1", values[indexPhoto],values[indexPhoto-1])
                    datosCesped.append(max([values[indexPhoto],values[indexPhoto-1]]))
                    print("Maximo cesped", max([values[indexPhoto],values[indexPhoto-1]]))
                
                dif= abs(values[indexPhoto]-values[indexPhoto-1])
                diferencias.append(dif)
                

                
            
    #Todas las imagenes procesadas de una feature
    dife[i]=diferencias

    fechasRep[i]=fechasR
    if i == 0:
        tamanoColumnas= datas
    else:
        if len(tamanoColumnas)< len(datas):
            tamanoColumnas= datas
            print("Tamano columnas", tamanoColumnas)
    
    datak[i]=datas
    val[i]=values
    print ("FECHA Y DATOS", datak[i], val[i])
   
    valGNDVI[i]= valuesGNDVI
    
    
    
    # Grafica de la diferencia de valores para imagenes tomadas en la misma fecha
    
   
    plt.figure(1)
    plt.plot(fechasRep[i][:],dife[i][:],color='silver', linewidth=2, alpha=1.5)
    pr=[str(j) for j in fechasRep[i][:]]
    #x= range(len(fechasRep[i][:]))
    
    plt.xticks(pr)
    plt.xlabel('Fechas repetidas')
    plt.ylabel('Diferencia')
    
    
    i+=1
#Deberia de etsar seleccionado el feature de bosque y cesped para cuantificar la diferencia
if hayBosque and hayCesped:
    
    print("DATOS DATOSBOSQUE ", datosBosque )
    print("DATOS DATOSCESPED", datosCesped)

    difCB= [abs(x - y) for x, y in zip(datosBosque, datosCesped)]
    print("DIFERENCIAS BOSQUE Y CESPED",difCB)
    plt.plot(fechasRep[0][:],difCB,color='red',linewidth=2, alpha=1.5)
plt.show()



#Crear fichero
print("DATA Y COLUMNAS", len(val[:]), tamanoColumnas)
fp= open('/tmp/datos.txt', 'w')
fp1= open('/tmp/datosTimeBased.txt', 'w')
fp2= open('/tmp/datosSuma.txt', 'w')
fp3= open('/tmp/datosPrueba.txt', 'w')

#crear un dataframe con los valores NDVI calculados, los index seran las etiquetas
#y las columnas seran las fechas.

df = pd.DataFrame(data=val[:],index=etiquetas,columns=tamanoColumnas)
print("REPLACE")
#buscar los valores 0 y sustiturilos por n.a para hacer interpolacion linear
dfn= df.replace(0, np.nan)
dfni=dfn.interpolate()
dfni= dfni.sort_index(axis='index')
fp.write(dfni.to_string())

#crear tabla de distancias
#Se crea un fichero para cada paso para ver si hace correctamente

tablaDistancias =[]
nombreColumnas=list(zip(*featuresNotNull))[1]

for elements in range(0,len(featuresNull)):
    print("QUE ELEMENTO NULL? ",  featuresNull[elements][1])
    clases.append(featuresNull[elements][3])
    for noNullElements in range(len(featuresNull),len(dfni.index)):
        print("QUE VALOR? ",noNullElements)
        
        #indice= nullElements+len(featuresNotNull)
        #prueba = dfni.loc[featuresNotNull[noNullElements][1]]-dfni.iloc[[elements]]
        prueba = dfni.iloc[[noNullElements]]-dfni.iloc[[elements]]
        #print("FILAS A RESTAR",  dfni.loc[featuresNotNull[noNullElements][1]],dfni.iloc[[elements]] )
        #print("Resta de columnas ", prueba.to_string())
        
        fp3.write(prueba.to_string())
      
        

diffTSa= prueba.abs()
fp1.write(diffTSa.to_string())
r= diffTSa.sum(axis=1)
fp2.write(r.to_string())
print("SUMA FILA", r)
tablaDistancias.append(r)
fp.close()
fp3.close()
fp1.close()
fp2.close()
print("TABLA DISTANCIAS", tablaDistancias)
fp4= open('/tmp/distancias.txt', 'w')
datosDistancias=[]

for el in range(0, len(tablaDistancias)):
    print("ES EL ELEMENTO??? ", tablaDistancias[el][0])
    datosDistancias.append(tablaDistancias[el][0])
    

print("TODOS LOS VALORES BIEN ", datosDistancias, nombreColumnas)
#chunks = [datosDistancias[x:x+len(featuresNotNull)] for x in xrange(0, len(datosDistancias), len(featuresNull))]
splitted= np.array_split(datosDistancias, len(featuresNull))
#numDim= len(featuresNotNull)
#datafinal=[]
#for c in range(0, numDim):
#    print("C ", c)
#    datafinal.append(zip(*splitted)[c])
dist = pd.DataFrame(data=splitted, columns=nombreColumnas)
fp4.write(dist.to_string())
fp4.close()
fp5= open('/tmp/pruebaminimo.txt', 'w')
dist['Clase'] = dist.loc[:, ['mar', 'arena', 'edificios', 'cesped', 'bosque']].idxmin(axis=1)
fp5.write(dist.to_string())
fp5.close()
predictedClases= dist.iloc[:,-1]
predictedClases=predictedClases.tolist()
#pruebaselecClase= ["mar", "bosque", "mar", "arena", "cesped", "edificios", "bosque", "cesped", "cesped", "cesped", "edificios", "cesped", "edificios","cesped", "cesped", "cesped"]
plt.figure(2)

#COnfusion Matrix
print("Confusion Matrix")
print(confusion_matrix(clases, predictedClases))


#Grafica valores NDVI 

for j in range (0, count):

    if selected_features[j][1]=='mar':
        print("ES MAR")
        plt.plot(datak[j],val[j],color="blue",linewidth=2)
    elif selected_features[j][1]=='bosque':
        print("ES Bosque")
        plt.plot(datak[j],val[j],color="darkgreen",linewidth=2)
    elif selected_features[j][1]=='cesped':
        print("ES cesped")
        plt.plot(datak[j],val[j],color="olivedrab",linewidth=2)
    elif selected_features[j][1]=='edificios':
        print("ES edificios")
        plt.plot(datak[j],val[j],color="sienna",linewidth=2)
    elif selected_features[j][1]=='arena':
        print("ES arena")
        plt.plot(datak[j],val[j],color="yellow",linewidth=2)

    else:
        plt.plot(datak[j],val[j],color="silver",linewidth=2, alpha=0.5)
    

    

plt.xlabel('Valores verano 2017')
plt.ylabel('NDVI value')
plt.show()

    #CORRELACION

#plt.figure(3)
#plt.subplot(1,1,1)
#plt.plot(val,valGNDVI,'bo')
#plt.xlabel('NDVI')
#plt.ylabel('GNDVI')
#print np.corrcoef(val, valGNDVI)
#plt.show() 



print("--- %s seconds ---" % (time.time() - start_time))


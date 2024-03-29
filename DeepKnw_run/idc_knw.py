"""
# Code based on DeepImportance code release
# @ https://github.com/DeepImportance/deepimportance_code_release
modified by @Sondess
"""
import pickle

import time
import math
from .utils import *
import numpy as np
import pandas as pd
from sklearn import cluster
from .utils_ini  import get_layer_outs_new, create_dir, get_non_con_neurons
from .utils_ini import get_conv
from sklearn.metrics import silhouette_score
from .utils import get_yolo_outs
experiment_folder = 'experiments'
model_folder      = 'Networks'
"""
# Code based on DeepImportance code release
# @ https://github.com/DeepImportance/deepimportance_code_release
# modified by @Sondess
"""


def getneuron_layer(subset, neuron):
    for k in subset:
        if k[1] ==neuron:
            layer = k[0]


    return layer



class ImportanceDrivenCoverage:
    def __init__(self,model, model_name, num_relevant_neurons, selected_class, subject_layer,
                 train_inputs, train_labels):
        self.covered_combinations = ()

        self.model = model
        self.model_name = model_name
        self.num_relevant_neurons = num_relevant_neurons
        self.selected_class = selected_class
        self.subject_layer = subject_layer
        self.train_inputs = train_inputs
        self.train_labels = train_labels
        create_dir(experiment_folder)


    def get_measure_state(self):
        return self.covered_combinations

    def set_measure_state(self, covered_combinations):
        self.covered_combinations = covered_combinations




def quantize(out_vectors, conv, relevant_neurons, n_clusters=3):

    quantized_ = []

    for i in range(out_vectors.shape[-1]):
        out_i = []
        for l in out_vectors:
            if conv: #conv layer
                out_i.append(np.mean(l[...,i]))
            else:
                out_i.append(l[i])

        #If it is a convolutional layer no need for 0 output check
        if not conv: out_i = filter(lambda elem: elem != 0, out_i)
        values = []

        if not len(out_i) < 10:

            kmeans = cluster.KMeans(n_clusters=n_clusters)
            kmeans.fit(np.array(out_i).reshape(-1, 1))
            values = kmeans.cluster_centers_.squeeze()
        values = list(values)
        values = limit_precision(values)



        quantized_.append(values)


    quantized_ = [quantized_[rn] for rn in relevant_neurons]

    return quantized_
def quantizeSilhouette(out_vectors, conv, relevant_neurons):
    quantized_ = []


    for i in relevant_neurons:
        out_i = []
        for l in out_vectors:

            if conv: #conv layer
                out_i.append(np.mean(l[i[1]]))
            else:
                out_i.append(l[i[1]])

        #If it is a convolutional layer no need for 0 output check
        if not conv:
            out_i = [item for item in out_i if item != 0] # out_i = filter(lambda elem: elem != 0, out_i)

        values = []
        if not len(out_i) < 10:
            clusterSize = range(2, 5)#[2, 3, 4]
            clustersDict = {}
            for clusterNum in clusterSize:
                kmeans          = cluster.KMeans(n_clusters=clusterNum)
                clusterLabels   = kmeans.fit_predict(np.array(out_i).reshape(-1, 1))
                silhouetteAvg   = silhouette_score(np.array(out_i).reshape(-1, 1), clusterLabels)
                clustersDict [silhouetteAvg] = kmeans

            maxSilhouetteScore = max(clustersDict.keys())
            bestKMean          = clustersDict[maxSilhouetteScore]

            values = bestKMean.cluster_centers_.squeeze()
        values = list(values)
        values = limit_precision(values)


        if len(values) == 0:
            values.append(0)

        quantized_.append(values)

    return quantized_
def quantizeSilhouetteYolo(out_vectors, conv, relevant_neurons):

    quantized_ = []

    for i in relevant_neurons:
        out_i = []
        for l in out_vectors:

            if conv:  # conv layer
                out_i.append(np.mean(l[i[1]]))
            else:
                out_i.append(l[i[1]])

        # If it is a convolutional layer no need for 0 output check
        if not conv:
            out_i = [item for item in out_i if item != 0]  # out_i = filter(lambda elem: elem != 0, out_i)

        values = []
        if not len(out_i) < 10:

            clusterSize = range(2, 5)#[2, 3, 4]
            clustersDict = {}
            for clusterNum in clusterSize:
                kmeans          = cluster.KMeans(n_clusters=clusterNum)
                clusterLabels   = kmeans.fit_predict(np.array(out_i).reshape(-1, 1))
                silhouetteAvg   = silhouette_score(np.array(out_i).reshape(-1, 1), clusterLabels)
                clustersDict [silhouetteAvg] = kmeans

            maxSilhouetteScore = max(clustersDict.keys())
            bestKMean          = clustersDict[maxSilhouetteScore]

            values = bestKMean.cluster_centers_.squeeze()
        values = list(values)
        values = limit_precision(values)


        if len(values) == 0:
            values.append(0)

        quantized_.append(values)

    return quantized_





def quantizeSilhouetteOld(out_vectors, conv, relevant_neurons):

    quantized_ = []

    for i in range(out_vectors.shape[-1]):
        if i not in relevant_neurons: continue

        out_i = []
        for l in out_vectors:
            if conv:
                out_i.append(np.mean(l[...,i]))
            else:
                out_i.append(l[i])


        if not conv:
            out_i = [item for item in out_i if item != 0]

        values = []

        if not len(out_i) < 10: #10 is threshold of number positives in all test input activations

            clusterSize = range(2, 6)
            clustersDict = {}
            for clusterNum in clusterSize:
                kmeans          = cluster.KMeans(n_clusters=clusterNum)
                clusterLabels   = kmeans.fit_predict(np.array(out_i).reshape(-1, 1))
                silhouetteAvg   = silhouette_score(np.array(out_i).reshape(-1, 1), clusterLabels)
                clustersDict [silhouetteAvg] = kmeans

            maxSilhouetteScore = max(clustersDict.keys())
            bestKMean          = clustersDict[maxSilhouetteScore]

            values = bestKMean.cluster_centers_.squeeze()
        values = list(values)
        values = limit_precision(values)

        #if not conv: values.append(0) #If it is convolutional layer we dont add  directly since thake average of whole filter.
        if len(values) == 0: values.append(0)

        quantized_.append(values)


    return quantized_


def limit_precision(values, prec=2):
    limited_values = []
    for v in values:
        limited_values.append(round(v,prec))

    return limited_values


def determine_quantized_cover(lout, quantized):
    covered_comb = []
    for idx, l in enumerate(lout):
            # print('idx', idx)
            # print('l',l)
            # print(quantized[idx])
            # print("the combination covered by idx in neurons act",quantized[idx])
            closest_q = min(quantized[idx], key=lambda x:abs(x-l))
            # print(closest_q)
            covered_comb.append(closest_q)


    return covered_comb

def get_prediction(test_inputs,test_idx, model, test_labels):
    input = test_inputs[test_idx]
    input = np.expand_dims(input, axis=0)
    predictions = model.predict(input)
    pred = np.argmax(predictions)
    label = test_labels[test_idx]
    label = np.argmax(label)
    if label == pred:
        predict = True
    else:
        predict = False

    return label, predict


def measure_idc(model, model_name, test_inputs,relevant_neurons, subsetTop,sel_class,
                                   test_layer_outs, train_layer_outs,trainable_layers, skip_layers,data_set,test_labels,DATA_DIR,
                                   covered_combinations=()):
    save_dir=os.path.join(DATA_DIR, 'TCC_' +data_set +"_" +model_name+'_.sav')

    TCC_combinations=[]


    relevant= {}
    layers=[]
    neurons_list=[]
    for n in relevant_neurons:
        neurons_list.append(n[1])
        if n[0] not in layers:
            layers.append(n[0])


    for x in relevant_neurons:
        if x[0] in relevant:
            relevant[x[0]].append(x[1])
        else:
            relevant[x[0]] = [x[1]]


    total_max_comb=0
    t = 0
    for layer,neurons in relevant.items():
        subject_layer = layer

        if subject_layer not in skip_layers:

            is_conv = get_conv(subject_layer, model, train_layer_outs)

            qtizedlayer=quantizeSilhouette(train_layer_outs[subject_layer], is_conv,
                                  neurons)




            for test_idx in range(len(test_inputs)):

                if is_conv :
                    lout = []
                    for r in neurons:
                        lout.append(np.mean(test_layer_outs[subject_layer][test_idx][r[1]]))

                else:
                        lout = []

                        neuronsindices=get_non_con_neurons(neurons)

                        for i in neuronsindices:
                            lout.append(test_layer_outs[subject_layer][test_idx][i])


                comb_to_add = determine_quantized_cover(lout, qtizedlayer)

                cov=0
                if comb_to_add not in covered_combinations:
                        covered_combinations += (comb_to_add,)
                        cov=1



            max_comb = 1
            for q in qtizedlayer:
                    max_comb *= len(q)



            total_max_comb += max_comb



        else:continue

    covered_num = len(covered_combinations)
    coverage = float(covered_num) / total_max_comb
    fields = ['combinations', 'nbre_covered', 'prediction', 'classes']
    df = pd.DataFrame(TCC_combinations,columns=fields)
    #
    with open(save_dir, 'wb') as out_file:
        pickle.dump(df, out_file)

    return coverage*100, covered_combinations, total_max_comb


def measure_idcYolo(model,model_ul, model_name, test_inputs,train_inputs,relevant_neurons, subsetTop,data_set,BATCH, samp,DATA_DIR,classes,
                                   y_test,covered_combinations=()):


    test_dir=os.path.join(DATA_DIR, 'TCC_testset'  +"_" +data_set +"_" +model_name+'_.sav')
    details_dir = os.path.join(DATA_DIR, 'TCC_details' +"_"  + data_set + "_" + model_name + '_.sav')
    train_qtz=os.path.join(DATA_DIR, 'Train_TCC' +"_" + data_set + "_" + model_name + '_.sav')
    train_outs_file=os.path.join(DATA_DIR, 'Train_layers_features' +"_" + data_set + "_" + model_name + '_.sav')


    TCC_details=[]
    train_qtized = []
    relevant= {}
    layers=[]
    neurons_list=[]
    for n in relevant_neurons:
        neurons_list.append(n[1])
        if n[0] not in layers:
            layers.append(n[0])


    for x in relevant_neurons:
        if x[0] in relevant:
            relevant[x[0]].append(x[1])
        else:
            relevant[x[0]] = [x[1]]
    # print("Loaded val data features (train_outs)  ....................")
    # startTime=time.time()
    # train_outs = get_allouts(model, train_inputs)
    # endt=time.time()
    # elapsed= endt - startTime
    # print("to calculate train features = %s" % elapsed)
    train_outs = pd.read_pickle(os.path.join(DATA_DIR, 'Train_layers_features_yolo_yolo_.sav'))
    qtized = pd.read_pickle(train_qtz)
    test_outs = get_allouts(model, test_inputs)
    total_max_comb=0
    for layer,neurons in relevant.items():
        is_conv=True
        # qtizedlayer = quantizeSilhouetteYolo(train_outs, True,
        #                                  neurons)
        qtizedlayer=qtized[0]
        # print("Loaded train clusters", qtizedlayer)
        # train_qtized.append(qtizedlayer)

        # for test_idx in (range(BATCH)):
        for test_idx, dt in enumerate(test_inputs):
            T = dt
            x = T['img']
            if is_conv :
                        lout = []
                        for r in neurons:
                            lout.append(np.mean(test_outs[test_idx][r[1]]))
            else:
                        lout = []
                        neuronsindices=get_non_con_neurons(neurons)
                        for i in neuronsindices:
                            lout.append(test_outs[test_idx][i])
            comb_to_add = determine_quantized_cover(lout, qtizedlayer)
            cov=0
            if comb_to_add not in covered_combinations:
                            covered_combinations += (comb_to_add,)
                            cov=1
            else:cov=+1
            results = model_ul.predict(x,save=False)
            for res in results:
                names_obj=[]
                # print('label', result[-1])
                names = res.names
                # print("prediction!!!!!!!!!!!", names[0])
                # nbr_obj=len(res.boxes.cls)
                for c in res.boxes.cls:
                    names_obj.append(names[int(c)])

                # print(names[int(y)])

                # probs = result.probs
                # print("probs", probs)
                # print('confidence',result[-2])
                # box = result.boxes
                # print('Boxes!!!!!!!!!!')
                # print("Object type:", box.cls)
                # print("Coordinates:", box.xyxy)
                # print("Probability:", box.conf)




                if names[0]==classes[0]:
                    if names[0] in names_obj:
                        prediction = True
                        # print("correct prediction")
                    else:
                        # print("wrong prediction")
                        prediction = False

                    # if prediction >0:
                    #     prediction = True
                    # else:
                    #     prediction = False
                else:
                    prediction = False

            case = [comb_to_add,  cov, prediction, classes[0]]
            TCC_details.append(case)

        max_comb = 1
        for q in qtizedlayer:
        # for q in train_qtized:
                        max_comb *= len(q)


        total_max_comb += max_comb
        # print("covered_combinations",covered_combinations)

    covered_num = len(covered_combinations)
    coverage = float(covered_num) / total_max_comb

    # with open(train_qtz, 'wb') as out_file:
    #     pickle.dump(train_qtized, out_file)
    #
    # with open(train_outs_file, 'wb') as out_file:
    #     pickle.dump(train_outs, out_file)


    fields = ['combinations', 'nbre_covered', 'prediction', 'classes']
    df_details = pd.DataFrame(TCC_details,columns=fields)
    with open(details_dir, 'wb') as out_file:
                pickle.dump(df_details, out_file)

    with open(test_dir, 'wb') as out_file:
                pickle.dump(covered_combinations, out_file)

    return coverage*100, covered_combinations, total_max_comb, df_details


def measure_Runtime(model, model_name, tensor_img,train_outs,relevant_neurons, Testset_TCC, Train_qtizer, data_set,DATA_DIR,
                                   covered_combinations=()):


    total_max_comb=0
    is_conv = True
    Comb_test=0
    covered_test = 0
    nbr_neurons=0
    for layer,neurons in relevant_neurons.items():
        # startTime=time.time()

        qtizedlayer = quantizeSilhouetteYolo(train_outs, True,
                                         neurons)
        nbr_neurons=+len(neurons)
        # print("the TK neurons trainset combinations!!!!\n",qtizedlayer)

        outs, pred = get_yolo_outs(model, tensor_img)
        # print('the images activations\n', outs)


        if is_conv :
            lout = []
            for r in neurons:
                            lout.append(np.mean(outs[r[1]]))

        else:
            lout = []

            neuronsindices=get_non_con_neurons(neurons)

            for i in neuronsindices:
                            lout.append(outs[i])


        comb_to_add = determine_quantized_cover(lout, qtizedlayer)
        # print('combination covered by corrupted image\n',comb_to_add)


        if comb_to_add not in covered_combinations:
                        covered_combinations += (comb_to_add,)





        max_comb = 1
        for q in qtizedlayer:
                        max_comb *= len(q)
        total_max_comb += max_comb
        Uncertainty=[]
        Eucleadian_Uncertainty=[]
        # print("Design Time TCC combinations",Testset_TCC.keys())
        # print(type(Testset_TCC.keys()))
        """eucleadian distance """
        for comb in covered_combinations:
            euc_unc = {}
            for TCC in Testset_TCC.keys():
                Eucleadian_dist=math.dist(comb,TCC)
                euc_unc.update({Eucleadian_dist:TCC})
            min_dist = min(euc_unc.keys())
            # print("eucleadian distance",euc_unc)
            simTcc=euc_unc[min_dist]
            T, F = Testset_TCC[simTcc]
            Uncer = (F / (T + F) * 100)
            Eucleadian_Uncertainty.append(Uncer)


        for comb in covered_combinations:
                comb=tuple(comb)
                for c in comb:
                    # print("c", c)
                    for TCC in Testset_TCC.keys():
                        # print("TCC",TCC)
                        if c in TCC:
                            # print("combination",c)
                            T,F=Testset_TCC[TCC]
                            Uncer=(F/(T+F)*100)
                            Uncertainty.append(Uncer)

                    # Uncertainty.append(Uncer)<== this was the cause of error I'm only adding for each c


    covered_num = len(covered_combinations)
    Runtime_Uncertainty=max(Uncertainty)
    Euc_runtime_uncetainty= max(Eucleadian_Uncertainty)


    design_coverage=covered_num/total_max_comb
    print("Runtime Uncertainty", Euc_runtime_uncetainty)
    # print("Runtime Uncertainty", Runtime_Uncertainty)
    # print(" Uncertainty details  %s for %s neurons " % (Uncertainty, nbr_neurons))
    # print("Design Coverage:  \n",
    #       design_coverage, '\n i.e., an estimate of the similarity between the Frame and the Test set')




    return Euc_runtime_uncetainty


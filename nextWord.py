#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jan 16 22:44:26 2020

@author: afaanansari
"""

import tensorflow as tf
import numpy as np
import pandas as pd
from tensorflow.contrib import  rnn
import random
import collections
import time

"""tf=ta.compat.v1
tf.disable_eager_execution()
"""
start_time = time.time()

def elapsed(sec) : 
    if sec<60:
        return str(sec) + "sec"
    elif sec < (60*60):
        return str(sec/60) + "min"
    else : 
        return str(sec/(60*60)) + "hr"

logs_path = "/Users/afaanansari/Desktop/spyder/nextWord"
writer = tf.summary.FileWriter(logs_path)

training_file = "/Users/afaanansari/Desktop/spyder/nextWord/file.txt"

def read_data(frame) :
    with open(frame) as f:
        content = f.readlines()
    content = [x.strip() for x in content]
    content = [content[i].split() for i in range(len(content))]
    content = np.array(content)
    content = np.reshape(content,[-1,])
    return content

training_data = read_data(training_file)
print(training_data)
print("loaded training data ...")
def build_dataset(words):
    count = collections.Counter(words).most_common()
    dictionary = dict()
    for word, _ in count:
        dictionary[word] = len(dictionary)
    reverse_dictionary = dict(zip(dictionary.values(), dictionary.keys()))
    return dictionary, reverse_dictionary

dictionary, reverse_dictionary = build_dataset(training_data)
vocab_size = len(dictionary)

learning_rate = 0.001
training_iters = 50000
display_step = 1000
n_input = 3

n_hidden = 512

x = tf.placeholder("float",[None,n_input,1])
y = tf.placeholder("float",[None,vocab_size])

weights = {
    'out' : tf.Variable(tf.random_normal([n_hidden,vocab_size]))
    }

biases = {
    'out' : tf.Variable(tf.random_normal([vocab_size]))
    }

def RNN(x , weights , biases) :
    x = tf.reshape(x , [-1,n_input])
    
    x = tf.split(x,n_input,1)
    
    
    rnn_cells = rnn.MultiRNNCell([rnn.BasicLSTMCell(n_hidden),rnn.BasicLSTMCell(n_hidden)])
    
    outputs, states = rnn.static_rnn(rnn_cells, x, dtype=tf.float32)
    
    return tf.matmul(outputs[-1],weights['out']) + biases['out']



pred = RNN(x,weights,biases)

cost = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(logits=pred , labels=y))

optimizer = tf.train.RMSPropOptimizer(learning_rate=learning_rate).minimize(cost)

correct_pred = tf.equal(tf.argmax(pred,1), tf.argmax(y,1))
accuracy = tf.reduce_mean(tf.cast(correct_pred, tf.float32))

init = tf.global_variables_initializer()

with tf.Session() as session :
    session.run(init)
    step=0
    offset = random.randint(0,n_input+1)
    end_offset = n_input + 1
    acc_total = 0
    loss_total = 0
    
    writer.add_graph(session.graph)
    
    while step < training_iters :
        if offset > (len(training_data) - end_offset):
            offset = random.randint(0,n_input+1)
            
        symbols_in_keys = [ [dictionary[ str(training_data[i])]] for i in range(offset,offset + n_input) ]
        symbols_in_keys = np.reshape(np.array(symbols_in_keys) , [-1, n_input , 1])
        
        symbols_out_onehot = np.zeros([vocab_size],dtype=float)
        symbols_out_onehot[dictionary[str(training_data[offset + n_input])]] = 1.0
        
        symbols_out_onehot = np.reshape(symbols_out_onehot , [1,-1])
        
        
        _, acc , loss, onehot_pred = session.run([optimizer , accuracy , cost , pred] , \
                                                 feed_dict = { x:symbols_in_keys , y : symbols_out_onehot})
        
        loss_total += loss
        acc_total += acc
        
        if (step + 1) % display_step == 0 :
            print("Iter= " + str(step+1) + "Average Loss= " + \
                  "{:.6f}".format(loss_total / display_step) + ", Average Accuracy= " + \
                      "{:.2f}%".format(100 * acc_total / display_step ))
            
            acc_total = 0
            loss_total = 0
            symbols_in = [training_data[i] for i in range(offset,offset + n_input)]
            symbols_out = training_data[offset + n_input]
            symbols_out_pred = reverse_dictionary[int(tf.argmax(onehot_pred , 1).eval())]
                        #symbols_out_pred = reverse_dictionary[int(tf.argmax(onehot_pred, 1).eval())]

            print("%s - [%s] vs [%s]" % (symbols_in , symbols_out , symbols_out_pred))
            
        step += 1
        offset += (n_input + 1)
        
    print("optimizer finished")
    print("Elapsed time : ",elapsed(time.time() - start_time))
    print("Run on command line")
    print("\t tensorboard --logdir=%s" % (logs_path))
    print("Point your web browser to: http://localhost:6006/")
    
    while True:
        prompt = "%s words : " % n_input
        sentence = input(prompt) 
        sentence = sentence.strip()
        words = sentence.split(' ')
        if len(words) != n_input :
            continue
        try:
            symbols_in_keys = [dictionary[str(words[i])] for i in range(len(words))]
            for i in range(32):
                keys = np.reshape(np.array(symbols_in_keys) , [-1 , n_input , 1])
                onehot_pred = session.run(pred , feed_dict = { x: keys})
                onehot_pred_index = int(tf.argmax(onehot_pred ,1 ).eval())
                sentence = "%s %s" % (sentence , reverse_dictionary[onehot_pred_index])
                symbols_in_keys = symbols_in_keys[1:]
                symbols_in_keys.append(onehot_pred_index)
            print(sentence)
        except :
            print("Word not found")
        
        
        
        

        
        
import numpy as np
import tensorflow as tf

import argparse
import pickle
import matplotlib.pyplot as plt
 
import gym
import custom_gym

from model import Model
from utils import *

parser = argparse.ArgumentParser()
parser.add_argument("--env", type=str, help="environment id")
parser.add_argument("--name", type=str, help="name")
parser.add_argument("--num_train", type=int)
parser.add_argument("--num_eval", type=int)
parser.add_argument("--success", type=str, default="Finish Task")
args = parser.parse_args()

env_id = args.env
name = args.name
batch_size = 1024

env = gym.make(env_id)
data = load_data("Asset/expert/%s.pickle" % name)

config = tf.ConfigProto()
config.gpu_options.allow_growth = True

data_size = []
all_dists = []

with tf.Session(config=config) as sess:
    print(len(data))
    model = Model(len(data[0][0]), len(data[0][1]))
    sess.run(tf.global_variables_initializer())
    
    writer = tf.summary.FileWriter("Asset/logdir/%s" % name)
    saver = tf.train.Saver([v for v in tf.global_variables() if "model" in v.name], max_to_keep=10)

    for i in range(args.num_train):
        # train a batch
        states, actions = get_batch(data, batch_size, i)
        loss, summary = model.train(states, actions)
        
        writer.add_summary(summary, i)
        save_path = saver.save(sess, "Asset/model/%s/model" % name, global_step=i)

        # evaluation
        dists = []
        if i % 10 == 0:
            for _ in range(args.num_eval):
                obs = env.reset()
                done = False
                while not done:               
                    action = model.predict([obs])
                    obs, r, done, info = env.step(action[0][0])
                    if done: dists.append((info["done_status"] == args.success))

            print("data: %d , success rate: %f %%" % (batch_size * (i + 1), np.sum(dists)) / args.num_eval * 100)
            data_size.append(batch_size * (i + 1))
            all_dists.append(np.sum(dists) / args.num_eval * 100)

plt.xlabel("# of data")
plt.ylabel("mean distance")

plt.plot(data_size, all_dists)
plt.savefig("Asset/picture/%s.png" % name)

with open("Asset/cooked_data/%s.pickle" % name, "wb") as file_out:
    data_out = {"data_size": data_size, "dists": all_dists}
    pickle.dump(data_out, file_out)

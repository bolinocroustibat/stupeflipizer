import tensorflow as tf
from data_provider import DataProvider
from rnn_model import RNNModel
import datetime
import sys
import matplotlib
import numpy as np
import time
import matplotlib.pyplot as plt

matplotlib.use('Agg')

# Args
if len(sys.argv) != 2:
    print('Please select a dataset.')
    print('Usage: python text_predictor.py <dataset>')
    print('Available datasets: stupeflip.')
    exit(1)
else:
    dataset = sys.argv[1]

# I/O
data_dir = './data/' + dataset
tensorboard_dir = data_dir + '/tensorboard/' + str(time.strftime('%Y-%m-%d_%H-%M-%S'))
input_file = data_dir + '/input.txt'
now = datetime.datetime.now()
output_file = data_dir + '/output_{}-{}-{}_{}-{}.txt'.format(now.year, now.month, now.day, now.hour, now.minute)
output = open(output_file, 'w')
output.close()

# Hyperparams
BATCH_SIZE = 32
SEQUENCE_LENGTH = 25
LEARNING_RATE = 0.01
DECAY_RATE = 0.97
HIDDEN_LAYER_SIZE = 256
CELLS_SIZE = 2

TEXT_SAMPLE_LENGTH = 500
SAMPLING_FREQUENCY = 1000
LOGGING_FREQUENCY = 1000


def rnn():
    data_provider = DataProvider(data_dir, BATCH_SIZE, SEQUENCE_LENGTH)
    model = RNNModel(data_provider.vocabulary_size, batch_size=BATCH_SIZE, sequence_length=SEQUENCE_LENGTH, hidden_layer_size=HIDDEN_LAYER_SIZE, cells_size=CELLS_SIZE)

    with tf.Session() as sess:

        summaries = tf.summary.merge_all()
        writer = tf.summary.FileWriter(tensorboard_dir)
        writer.add_graph(sess.graph)
        sess.run(tf.global_variables_initializer())

        epoch = 0
        temp_losses = []
        smooth_losses = []

        while True:
            sess.run(tf.assign(model.learning_rate, LEARNING_RATE * (DECAY_RATE ** epoch)))
            data_provider.reset_batch_pointer()
            state = sess.run(model.initial_state)
            for batch in range(data_provider.batches_size):
                inputs, targets = data_provider.next_batch()
                feed = {model.input_data: inputs, model.targets: targets}
                for index, (c, h) in enumerate(model.initial_state):
                    feed[c] = state[index].c
                    feed[h] = state[index].h
                iteration = epoch * data_provider.batches_size + batch
                summary, loss, state, _ = sess.run([summaries, model.cost, model.final_state, model.train_op], feed)
                writer.add_summary(summary, iteration)
                temp_losses.append(loss)

                if iteration % SAMPLING_FREQUENCY == 0:
                    sample_text(sess, data_provider, iteration)

                if iteration % LOGGING_FREQUENCY == 0:
                    smooth_loss = np.mean(temp_losses)
                    smooth_losses.append(smooth_loss)
                    temp_losses = []
                    plot(smooth_losses, 'iterations (thousands)', 'loss')
                    print(f'metric: iteration, value: {iteration}')
                    print(f'metric: epoch, value: {epoch}')
                    print(f'metric: loss, value: {smooth_loss}')
            epoch += 1


def sample_text(sess, data_provider, iteration):
    model = RNNModel(data_provider.vocabulary_size, batch_size=1, sequence_length=1, hidden_layer_size=HIDDEN_LAYER_SIZE, cells_size=CELLS_SIZE, training=False)
    text = model.sample(sess, data_provider.chars, data_provider.vocabulary, TEXT_SAMPLE_LENGTH).encode('utf-8')
    with open(output_file, 'a') as output:
        output.write(f'Iteration: {iteration}\n{text}\n\n')


def plot(data, x_label, y_label):
    plt.plot(range(len(data)), data)
    plt.title(dataset)
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plt.savefig(data_dir + '/' + y_label + '.png', bbox_inches='tight')
    plt.close()


if __name__ == '__main__':
    print(f'Selected dataset: {dataset}')
    print(f'Batch size: {BATCH_SIZE}')
    print(f'Sequence length: {SEQUENCE_LENGTH}')
    print(f'Learning rate: {LEARNING_RATE}')
    print(f'Decay rate: f{DECAY_RATE}')
    print(f'Hidden layer size: {HIDDEN_LAYER_SIZE}')
    print(f'Cells size: {CELLS_SIZE}')
    rnn()

import tensorflow as tf
import numpy as np


class NeuralNetworkUnit:
    def __init__(self, hidden_dim, input_dim, transfer_fun, name, dtype=tf.float64):
        # father and son store the upper layer and the lower layer of this unit.
        # if the layer is the first layer, then it is the root; if the layer is the last one, it is the leaf.
        self.name = name
        self.father = None
        self.sons = dict()
        self.dtype = dtype
        self.hidden_dim = hidden_dim
        self.input_dim = input_dim
        self.transfer_fun = transfer_fun
        self.parameters = dict()
        self.output = None
        self.on_train = None
        self.input = None

    def __add__(self, other):
        return Identity(self.output + other.output)

    def __sub__(self, other):
        return Identity(self.output - other.output)


class NeuronLayer(NeuralNetworkUnit):
    def __init__(self, hidden_dim, input_dim=None, transfer_fun=None, name=None, dtype=tf.float64, trainable=True):
        super().__init__(hidden_dim, input_dim, transfer_fun=transfer_fun, dtype=dtype, name=name)
        self.trainable = trainable

    def initialize(self, counter, graph=None, **kwargs):
        input_dim = kwargs.get('input_dim')
        self.input_dim = int(input_dim[1])
        counter['Dense'] += 1
        if graph is None:
            graph = tf.get_default_graph()
        with graph.as_default():
            with tf.variable_scope('Dense_'+str(counter['Dense'])):
                variables = tf.Variable(name='weight', initial_value=tf.truncated_normal(dtype=self.dtype,
                                                                                         shape=(self.input_dim,
                                                                                                self.hidden_dim),
                                                                                         mean=0,
                                                                                         stddev=0.1),
                                        trainable=self.trainable)

                self.parameters['w'] = variables
                variables = tf.Variable(name='bias', initial_value=tf.truncated_normal(dtype=self.dtype,
                                                                                       shape=(1, self.hidden_dim),
                                                                                       mean=0,
                                                                                       stddev=0.1),
                                        trainable=self.trainable)

                self.parameters['b'] = variables
            self.output = tf.matmul(self.input, self.parameters['w']) + self.parameters['b']

            try:
                self.output = self.transfer_fun(self.output)
            except TypeError:
                self.output = self.output


class Identity(NeuralNetworkUnit):
    def __init__(self, name=None, dtype=tf.float64):
        super().__init__(hidden_dim=None, input_dim=None, transfer_fun=None, dtype=dtype, name=name)

    def initialize(self, counter, graph=None, **kwargs):
        counter['Identity'] += 1
        if graph is None:
            graph = tf.get_default_graph()
        with graph.as_default():
            with tf.variable_scope('Identity_'+str(counter['Identity'])):
                self.output = tf.identity(self.input)


class SoftMaxLayer(NeuralNetworkUnit):
    def __init__(self, name=None):
        super().__init__(hidden_dim=None, input_dim=None, transfer_fun=None, dtype=None, name=name)

    def initialize(self, counter, graph=None, **kwargs):
        counter['SoftMax'] += 1
        if graph is None:
            graph = tf.get_default_graph()
        with graph.as_default():
            with tf.variable_scope('SoftMax_' + str(counter['SoftMax'])):
                sum_exp = tf.reduce_sum(tf.exp(self.input), axis=1)
                sum_exp = tf.expand_dims(sum_exp, axis=1)
                self.output = tf.divide(tf.exp(self.input), sum_exp)


class Relu(NeuralNetworkUnit):
    def __init__(self, name=None):
        super().__init__(hidden_dim=None, input_dim=None, transfer_fun=None, dtype=None, name=name)

    def initialize(self, counter, graph=None, **kwargs):
        counter['Relu'] += 1
        if graph is None:
            graph = tf.get_default_graph()
        with graph.as_default():
            with tf.variable_scope('Relu_' + str(counter['Relu'])):
                self.output = tf.nn.relu(self.input)


class Sigmoid(NeuralNetworkUnit):
    def __init__(self, name=None):
        super().__init__(hidden_dim=None, input_dim=None, transfer_fun=None, dtype=None, name=name)

    def initialize(self, counter, graph=None, **kwargs):
        counter['Sigmoid'] += 1
        if graph is None:
            graph = tf.get_default_graph()
        with graph.as_default():
            with tf.variable_scope('Sigmoid_' + str(counter['Sigmoid'])):
                self.output = tf.nn.sigmoid(self.input)


class ConvolutionUnit(NeuralNetworkUnit):
    # The shape parameter should be (height, width, num filters)
    def __init__(self, shape, transfer_fun=None, name=None, dtype=tf.float64, **kwargs):
        super().__init__(None, None, transfer_fun=transfer_fun, dtype=dtype, name=name)
        self.shape = shape
        self.kwargs = kwargs

    def initialize(self, counter, graph=None, **kwargs):
        counter['Convolution'] += 1
        input_dim = kwargs.get('input_dim')
        shape = list(self.shape)
        shape.insert(2, int(input_dim[3]))
        shape = tuple(shape)

        if graph is None:
            graph = tf.get_default_graph()
        with graph.as_default():
            with tf.variable_scope('Convolution_' + str(counter['Convolution'])):
                self.parameters['w'] = tf.Variable(name='weight',
                                                   initial_value=tf.truncated_normal(dtype=self.dtype,
                                                                                     shape=shape, mean=0, stddev=0.1))
                self.parameters['b'] = tf.Variable(name='bias',
                                                   initial_value=tf.truncated_normal(dtype=self.dtype,
                                                                                     shape=(shape[-1],), mean=0,
                                                                                     stddev=0.1))
            self.output = tf.nn.conv2d(self.input, self.parameters['w'],
                                       strides=self.kwargs.get('strides', [1, 1, 1, 1]),
                                       padding=self.kwargs.get('padding', 'SAME'))
            self.output = self.output + self.parameters['b']
            if self.transfer_fun is not None:
                self.output = self.transfer_fun(self.output)


class ReduceMean(NeuralNetworkUnit):
    def __init__(self, hidden_dim=None, input_dim=None, transfer_fun=None, name=None, dtype=tf.float64):
        super().__init__(hidden_dim, input_dim, transfer_fun=transfer_fun, dtype=dtype, name=name)

    def initialize(self, **kwargs):
        self.output = self.input - tf.reduce_mean(self.input, axis=1, keepdims=True)


class ResidualBlock(NeuralNetworkUnit):
    pass


class Flatten(NeuralNetworkUnit):
    def __init__(self, name=None):
        super().__init__(hidden_dim=None, input_dim=None, transfer_fun=None, dtype=None, name=name)

    def initialize(self, counter, graph=None, **kwargs):
        counter['Flatten'] += 1
        if graph is None:
            graph = tf.get_default_graph()
        with graph.as_default():
            self.output = tf.reshape(self.input, shape=[-1, int(np.prod(self.input.__dict__['_shape_val'][1:]))])


# The input of this layer could only be NeuronLayer.
class BatchNormalization(NeuralNetworkUnit):
    def __init__(self, dtype=tf.float64, transfer_fun=None, epsilon=0.01, moving_decay=0.99, name=None, **kwargs):
        super().__init__(None, None, transfer_fun=transfer_fun, name=name, dtype=dtype)
        self.epsilon = epsilon
        self.kwargs = kwargs
        self.moving_decay = moving_decay

    def initialize(self, counter, graph=None, **kwargs):
        counter['BatchNormalization'] += 1
        on_train = kwargs.get('on_train')

        if graph is None:
            graph = tf.get_default_graph()
        with graph.as_default():
            with tf.variable_scope('BatchNormalization_'+str(counter['BatchNormalization'])):
                self.output = tf.layers.batch_normalization(self.input, training=on_train)
            if self.transfer_fun is not None:
                self.output = self.transfer_fun(self.output)
            glb_vars = [var for var in tf.global_variables()]
            self.parameters['moving_variance'] = glb_vars[-1]
            self.parameters['moving_mean'] = glb_vars[-2]
            self.parameters['beta'] = glb_vars[-3]
            self.parameters['gamma'] = glb_vars[-4]


class AvgPooling(NeuralNetworkUnit):
    # The shape is corresponding to each dimension of the input data. 
    def __init__(self, shape, transfer_fun=None, name=None, dtype=tf.float64, **kwargs):
        super().__init__(None, None, transfer_fun=transfer_fun, dtype=dtype, name=name)
        self.shape = shape
        self.kwargs = kwargs

    def initialize(self, counter, graph, **kwargs):
        counter['AvgPooling'] += 1
        if graph is None:
            graph = tf.get_default_graph()
        with graph.as_default():
            with tf.variable_scope('AvgPooling_' + str(counter['AvgPooling'])):
                self.output = tf.nn.avg_pool(value=self.input, ksize=self.shape,
                                             strides=self.kwargs.get('strides', [1, 1, 1, 1]),
                                             padding=self.kwargs.get('padding', 'SAME'))
    
   
class MaxPooling(NeuralNetworkUnit):
    # The shape is corresponding to each dimension of the input data. 
    def __init__(self, shape, transfer_fun=None, name=None, dtype=tf.float64, **kwargs):
        super().__init__(None, None, transfer_fun=transfer_fun, dtype=dtype, name=name)
        self.shape = shape
        self.kwargs = kwargs

    def initialize(self, counter, graph, **kwargs):
        counter['MaxPooling'] += 1
        if graph is None:
            graph = tf.get_default_graph()
        with graph.as_default():
            with tf.variable_scope('MaxPooling_' + str(counter['MaxPooling'])):
                self.output = tf.nn.avg_pool(value=self.input, ksize=self.shape,
                                             strides=self.kwargs.get('strides', [1, 1, 1, 1]),
                                             padding=self.kwargs.get('padding', 'SAME'))


class Dropout(NeuralNetworkUnit):
    def __init__(self, keep_prob, transfer_fun=None, name=None, dtype=tf.float64, **kwargs):
        super().__init__(None, None, transfer_fun=transfer_fun, dtype=dtype, name=name)
        self.kwargs = kwargs
        self.keep_prob = keep_prob

    def initialize(self, counter, graph, **kwargs):
        counter['Dropout'] += 1
        if graph is None:
            graph = tf.get_default_graph()
        with graph.as_default():
            with tf.variable_scope('MaxPooling_' + str(counter['MaxPooling'])):
                self.output = tf.nn.dropout(self.input, keep_prob=self.keep_prob)

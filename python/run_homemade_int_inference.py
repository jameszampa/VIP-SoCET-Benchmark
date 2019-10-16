"""
Homemade implementation for inferencing using 'model.tflite' compares 'My Accuracy' with Tensorflow's implementation
"""

import tensorflow as tf
from tensorflow import keras
import numpy as np
import offline
import integer_inference


mnist = keras.datasets.mnist
(train_images, train_labels), (test_images, test_labels) = mnist.load_data()

train_images = train_images / 255.0
test_images = test_images / 255.0

flat_train = []
flat_test = []

for i, img in enumerate(train_images):
    flat_train.append(img.flatten())
flat_train = np.asarray(flat_train)

for i, img in enumerate(test_images):
    flat_test.append(img.flatten())
flat_test = np.asarray(flat_test)

flat_train = flat_train[..., np.newaxis]
flat_test = flat_test[..., np.newaxis]

# load TFLite file
interpreter = tf.lite.Interpreter(model_path=f'model.tflite')
# Allocate memory.
interpreter.allocate_tensors()

input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()
inter_layer = interpreter.get_tensor_details()

tensorflow_no_softmax_acc = 0
tensorflow_softmax_acc = 0
homemade_acc = 0

num_test_imgs = 10000

# Conv1D offline parameters
# Hardcoded values for specific weights/biases ect. The application Netron was very helpful in understanding
# inputs and outputs to different layers. Netron gives a good overview of what a model looks like
weight_index = 4
bias_index = 6
output_index = 1
input_index = 7
quantized_weight_conv = interpreter.get_tensor(inter_layer[weight_index]['index'])
quantized_bias_conv = interpreter.get_tensor(inter_layer[bias_index]['index'])
weight_scale_conv, weight_offset_conv = inter_layer[weight_index]['quantization']
input_scale_conv, input_offset_conv = inter_layer[input_index]['quantization']
output_scale_conv, output_offset_conv = inter_layer[output_index]['quantization']
M_conv = (input_scale_conv * weight_scale_conv) / output_scale_conv
right_shift_conv, M_0_conv = offline.quantize_mult_smaller_one(M_conv)

# hidden dense layer offline parameters
weight_index = 10
bias_index = 8
output_index = 9
input_index = 0
quantized_weight_dense = interpreter.get_tensor(inter_layer[weight_index]['index'])
quantized_bias_dense = interpreter.get_tensor(inter_layer[bias_index]['index'])
weight_scale_dense, weight_offset_dense = inter_layer[weight_index]['quantization']
input_scale_dense, input_offset_dense = inter_layer[input_index]['quantization']
output_scale_dense, output_offset_dense = inter_layer[output_index]['quantization']
M_dense = (input_scale_dense * weight_scale_dense) / output_scale_dense
right_shift_dense, M_0_dense = offline.quantize_mult_smaller_one(M_dense)

# prediction layer offline parameters
weight_index = 14
bias_index = 12
output_index = 11
input_index = 9
quantized_weight_pred = interpreter.get_tensor(inter_layer[weight_index]['index'])
quantized_bias_pred = interpreter.get_tensor(inter_layer[bias_index]['index'])
weight_scale_pred, weight_offset_pred = inter_layer[weight_index]['quantization']
input_scale_pred, input_offset_pred = inter_layer[input_index]['quantization']
output_scale_pred, output_offset_pred = inter_layer[output_index]['quantization']
M_pred = (input_scale_pred * weight_scale_pred) / output_scale_pred
right_shift_pred, M_0_pred = offline.quantize_mult_smaller_one(M_pred)


for i in range(num_test_imgs):
    # set up img to be infered on...
    quantized_input = offline.quantize(input_details[0], flat_test[i:i+1])
    interpreter.set_tensor(input_details[0]['index'], quantized_input)

    # let tensorflow do the math
    interpreter.invoke()

    # save layer before softmax because softmax too hard for now
    quantized_output_no_softmax = interpreter.get_tensor(inter_layer[output_index]['index'])

    # Output with softmax
    quantized_output_softmax = interpreter.get_tensor(output_details[0]['index'])

    # Homemade inference time!
    output_conv_arr = (integer_inference.Conv(quantized_input, input_offset_conv, quantized_weight_conv,
                                              weight_offset_conv, quantized_bias_conv, output_offset_conv, M_0_conv,
                                              right_shift_conv, (784, 16)))

    # to do move to Conv function
    output_conv_arr = output_conv_arr.flatten()
    output_conv_arr = output_conv_arr[np.newaxis, ...]

    output_full_conn_arr = (integer_inference.FullyConnected(output_conv_arr, input_offset_dense,
                                                             quantized_weight_dense, weight_offset_dense,
                                                             quantized_bias_dense, output_offset_dense, M_0_dense,
                                                             right_shift_dense, (1, 128)))

    output_full_conn_arr_2 = (integer_inference.FullyConnected(output_full_conn_arr, input_offset_pred,
                                                               quantized_weight_pred, weight_offset_pred,
                                                               quantized_bias_pred, output_offset_pred, M_0_pred,
                                                               right_shift_pred, (1, 10)))

    if test_labels[i] == np.argmax(quantized_output_softmax):
        tensorflow_softmax_acc += 1
    if test_labels[i] == np.argmax(quantized_output_no_softmax):
        tensorflow_no_softmax_acc += 1
    if test_labels[i] == np.argmax(output_full_conn_arr_2):
        homemade_acc += 1

    print('Interation ', i + 1, ':', num_test_imgs)
    print('Tensorflow - softmax    accuracy : ', tensorflow_softmax_acc / (i + 1))
    print('Tensorflow - no softmax accuracy : ', tensorflow_no_softmax_acc / (i + 1))
    print('Homemade   - no softmax accuracy : ', homemade_acc / (i + 1), '\n')



print('Final Tensorflow - softmax    accuracy :', tensorflow_softmax_acc / num_test_imgs)
print('Final Tensorflow - no softmax accuracy :', tensorflow_no_softmax_acc / num_test_imgs)
print('Final Homemade   - no softmax accuracy :', homemade_acc / num_test_imgs)


#ifndef MODEL_H
#define MODEL_H
#include <stdint.h>

const uint8_t quantized_weight_conv[1][1][3][8] = { 
181,  59, 235,   6,  29, 203, 219, 215, 
255, 235, 211, 191, 187, 213, 163, 211, 
 30, 222, 102, 254, 239,  80,   0, 217
};

const int32_t quantized_bias_conv[8] = { -143, -2, 1836, 696, 1142, -128, 5411, 997 };

const uint8_t weight_offset_conv = 157;

const uint8_t input_offset_conv = 0;

const uint8_t output_offset_conv = 0;

const int right_shift_conv = 11;

const int32_t M_0_conv = 1259830531;

#endif
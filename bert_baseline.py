# Calculates time it takes for device_map to run sequentially through the batch and model
# To compare with `PiPPy`, it will run on two batches individually

from transformers import T5ForConditionalGeneration, T5Config
from accelerate import infer_auto_device_map, dispatch_model
from accelerate.utils import calculate_maximum_sizes, convert_bytes
from hf_utils import generate_inputs_for_model
import math

config = T5Config()

model = T5ForConditionalGeneration(config)

model_size, shared = calculate_maximum_sizes(model)
# Returns 242026496, (65798144, ['shared'])

# Split in half for two devices
memory = (model_size + shared[0]) / 2
memory = convert_bytes(memory)
# Returns 115.41 MB
value, ending = memory.split(' ')

# Add a chunk to deal with err:
# cannot access free variable 'chunk_args_list' where it is not associated with a value in enclosing scope
memory = math.ceil(float(value)) * 1.1
memory = f'{memory} {ending}'
device_map = infer_auto_device_map(model, max_memory={0: memory, 1: memory}, no_split_module_classes=["T5Block"])

model = dispatch_model(model, device_map)

model.eval()

example_inputs = [
        generate_inputs_for_model(
        T5ForConditionalGeneration, model, "T5ForConditionalGeneration", 1, "cuda:0"
    ),
    generate_inputs_for_model(
        T5ForConditionalGeneration, model, "T5ForConditionalGeneration", 1, "cuda:0"
    ),
    
]


import time
import torch
times = []
for _ in range(5):
    start_time = time.time()
    for input in example_inputs:
        with torch.no_grad():
            output = model(**input)
    end_time = time.time()
    times.append(end_time - start_time)
print(f'Time of first pass: {times[0]}')
print(f"Time taken for sequential run: {sum(times[1:]) / len(times[1:])}")
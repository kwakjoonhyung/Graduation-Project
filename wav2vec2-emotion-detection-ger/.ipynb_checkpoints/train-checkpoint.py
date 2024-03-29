import os
import json
import random
from datasets import load_dataset, Audio
from transformers import (
	AutoConfig,
	Wav2Vec2Processor,
	Wav2Vec2CTCTokenizer,
	EvalPrediction,
	TrainingArguments,
	Trainer
)
import glob
from dataclasses import dataclass
import torch
from torch import nn
from torch.nn import BCEWithLogitsLoss, CrossEntropyLoss, MSELoss

from transformers.models.wav2vec2.modeling_wav2vec2 import (
	Wav2Vec2PreTrainedModel,
	Wav2Vec2Model
)

import numpy as np
from typing import Dict, List, Optional, Union, Tuple, Any

import transformers
from transformers import Wav2Vec2Processor
from packaging import version

from Wav2Vec2ForSpeechClassification import Wav2Vec2ForSpeechClassification

TRAIN_FILE = "train.json"
TEST_FILE = "test.json"
LABELS = {'0': 'anger', '1': 'boredom', '2': 'disgust', '3': 'fear', '4': 'happiness', '5': 'sadness', '6': 'neutral'}
LABEL_LETTER_MAP = {'W': 0, 'L': 1, 'E': 2, 'A': 3, 'F': 4, 'T': 5, 'N': 6}

INPUT_COLUMN = "path"
OUTPUT_COLUMN = "label"

# We need the "self" to get a model with self attention
model_name_or_path = "facebook/wav2vec2-large-960h-lv60-self"

# create processor
processor = Wav2Vec2Processor.from_pretrained(model_name_or_path)
	
class CTCTrainer(Trainer):
	def training_step(self, model: nn.Module, inputs: Dict[str, Union[torch.Tensor, Any]]) -> torch.Tensor:
		model.train()
		inputs = self._prepare_inputs(inputs)

		loss = self.compute_loss(model, inputs)

		if self.args.gradient_accumulation_steps > 1:
			loss = loss / self.args.gradient_accumulation_steps

		loss.backward()

		return loss.detach()		
		
@dataclass
class DataCollatorCTCWithPadding:
	processor: Wav2Vec2Processor
	padding: Union[bool, str] = True
	max_length: Optional[int] = None
	max_length_labels: Optional[int] = None
	pad_to_multiple_of: Optional[int] = None
	pad_to_multiple_of_labels: Optional[int] = None

	def __call__(self, features: List[Dict[str, Union[List[int], torch.Tensor]]]) -> Dict[str, torch.Tensor]:
		input_features = [{"input_values": feature["input_values"]} for feature in features]
		label_features = [feature["label"] for feature in features]

		d_type = torch.long if isinstance(label_features[0], int) else torch.float

		batch = self.processor.pad(
			input_features,
			padding=self.padding,
			max_length=self.max_length,
			pad_to_multiple_of=self.pad_to_multiple_of,
			return_tensors="pt",
		)

		batch["labels"] = torch.tensor(label_features, dtype=d_type)

		return batch

def compute_metrics(p: EvalPrediction):
	preds = p.predictions[0] if isinstance(p.predictions, tuple) else p.predictions
	preds = np.argmax(preds, axis=1)
	return {"accuracy": (preds == p.label_ids).astype(np.float32).mean().item()}

def prepare_data():
	data = []
	labels = {}
	files = glob.glob('wav/*.wav')
	for f in files:
		formatted_sample = {}
		formatted_sample['wav'] = f
		formatted_sample['label'] = LABEL_LETTER_MAP[os.path.basename(f)[5]]
		formatted_sample['audio'] = f
		data.append(formatted_sample)
		
	random.shuffle(data)
	print("Found", len(data), "samples. Example: ", data[:5])
	
	train = data[:int(len(data)*0.8)]
	test = data[len(train):]
	
	print("Length train:", len(train), "length test:", len(test))
	
	with open(TRAIN_FILE, 'w') as json_file:
		json.dump(train, json_file)
	with open(TEST_FILE, 'w') as json_file:
		json.dump(test, json_file)

def preprocess_function(examples):
	speech_list = [audio["array"] for audio in examples["audio"]]
	result = processor(speech_list, sampling_rate=16000)
	return result
	
if __name__ == "__main__":
	if not (os.path.exists(TRAIN_FILE) and os.path.exists(TEST_FILE)):
		prepare_data()
		
	# load datasets
	print("Loading datasets...")
	dataset = load_dataset('json', data_files={'train': TRAIN_FILE, 'test': TEST_FILE}).cast_column("audio", Audio())
		
	print(dataset)
	print("There are ", len(LABELS), "labels: ", LABELS)
	
	# create config
	config = AutoConfig.from_pretrained(
		model_name_or_path,
		num_labels=len(LABELS),
		label2id={LABELS[label]: i for i, label in enumerate(LABELS)},
		id2label={i: LABELS[label] for i, label in enumerate(LABELS)},
		finetuning_task="wav2vec2_clf",
	)
	#setattr(config, 'pooling_mode', "mean")
	# nice visualization https://www.kaggle.com/questions-and-answers/59502
	config.pooling_mode = "mean"
	print("label2id", config.label2id)
	print("id2label", config.id2label)
	
	processed_dataset = dataset.map(
		preprocess_function,
		batch_size=100,
		batched=True,
		num_proc=4
	)
	
	model = Wav2Vec2ForSpeechClassification.from_pretrained(
		model_name_or_path,
		config=config,
	)
	
	# disable the gradient computation for the feature extractor so that its parameter will not be updated during training
	model.freeze_feature_extractor()
	
	training_args = TrainingArguments(
		output_dir="./wav2vec/",
		per_device_train_batch_size=2,
		per_device_eval_batch_size=4,
		gradient_accumulation_steps=2,
		evaluation_strategy="steps",
		num_train_epochs=20.0,
		fp16=False,
		save_steps=20,
		eval_steps=10,
		logging_steps=10,
		learning_rate=1e-4,
		save_total_limit=2,
	)
	
	data_collator = DataCollatorCTCWithPadding(processor=processor, padding=True)

	trainer = CTCTrainer(
		model=model,
		data_collator=data_collator,
		args=training_args,
		compute_metrics=compute_metrics,
		train_dataset=processed_dataset['train'],
		eval_dataset=processed_dataset['test'],
		tokenizer=processor.feature_extractor
	)
	
	tokenizer = Wav2Vec2CTCTokenizer.from_pretrained(model_name_or_path)
	tokenizer.save_pretrained("myrun3") 

	trainer.train()
	trainer.save_model("myrun3")

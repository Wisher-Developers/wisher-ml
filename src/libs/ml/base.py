import os

import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModel
from transformers.agents.agent_types import Tensor

# We won't have competing threads in this example app
os.environ["TOKENIZERS_PARALLELISM"] = "true"


# Initialize tokenizer and model for GTE-base
tokenizer = AutoTokenizer.from_pretrained('thenlper/gte-base')
model = AutoModel.from_pretrained('thenlper/gte-base')


def average_pool(last_hidden_states: Tensor, attention_mask: Tensor) -> Tensor:
    last_hidden = last_hidden_states.masked_fill(
        ~attention_mask[..., None].bool(), 0.0)
    return last_hidden.sum(dim=1) / attention_mask.sum(dim=1)[..., None]


def generate_embedding(text, metadata=None):
    if metadata is None:
        metadata = {}
    combined_text = " ".join(
        [text] + [v for k, v in metadata.items() if isinstance(v, str)])

    inputs = tokenizer(combined_text, return_tensors='pt',
                       max_length=512, truncation=True)
    with torch.no_grad():
        outputs = model(**inputs)

    attention_mask = inputs['attention_mask']
    embeddings = average_pool(outputs.last_hidden_state, attention_mask)

    embeddings = F.normalize(embeddings, p=2, dim=1)

    return embeddings.numpy().tolist()[0]
